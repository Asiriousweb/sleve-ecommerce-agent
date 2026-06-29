#!/usr/bin/env python3
"""
Supervisor para Railway — UN solo servicio corre todo el agente E-commerce,
compartiendo disco/volumen. Mismo patrón que Sleve-Trade-Marketing.

  • Bot de Telegram (long-polling; se relanza si muere)
  • Scheduler: brief diario (08:00) + (placeholder) validación nocturna
  • MCP server read-only (si MCP_ENABLED) — para que el orquestador Comercial
    y el E-commerce se consulten entre sí
  • Health HTTP en $PORT (Railway)

Hora: usa la hora local del contenedor. En Railway poné TZ=America/Santiago.
"""
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import schedule

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.environ.get("PORT", "8080"))


def log(msg: str) -> None:
    print(f"[run_railway {datetime.now(timezone.utc):%F %T}Z] {msg}", flush=True)


# --- Health + data API (Railway) --------------------------------------------
DATA_DIR = Path(os.environ.get("DATA_DIR", str(ROOT / "agent" / "data")))


class _Health(BaseHTTPRequestHandler):
    def do_GET(self):
        # OAuth Shopify multi-tienda
        if self.path.startswith("/shopify/callback"):
            import shopify_oauth
            import urllib.parse as _up
            qs = _up.parse_qs(_up.urlparse(self.path).query)
            code = qs.get("code", [""])[0]
            shop = qs.get("shop", [""])[0]
            try:
                shopify_oauth.exchange(shop, code)
                html = (f"<h2>✅ {shop} conectada</h2><p>Token guardado. "
                        "<a href='/shopify'>← Volver a las tiendas</a></p>")
            except Exception as e:  # noqa: BLE001
                html = (f"<h2>❌ Error en {shop}</h2><pre>{e}</pre>"
                        "<p>Revisa SHOPIFY_CLIENT_ID/SECRET y el redirect. "
                        "<a href='/shopify'>← Volver</a></p>")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return
        if self.path.startswith("/shopify/install"):
            import shopify_oauth
            import urllib.parse as _up
            store = _up.parse_qs(_up.urlparse(self.path).query).get("store", [""])[0]
            self.send_response(302)
            self.send_header("Location", shopify_oauth.install_url(store) if store else "/shopify")
            self.end_headers()
            return
        if self.path == "/shopify" or self.path.startswith("/shopify?"):
            import shopify_oauth
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(shopify_oauth.index_html().encode("utf-8"))
            return
        # /refresh → fuerza un refresco de datos ahora (on-demand)
        if self.path.startswith("/refresh"):
            try:
                refresh_data()
                body = b"refresh ejecutado"
            except Exception as e:  # noqa: BLE001
                body = f"error: {e}".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return
        # /nightly/status → resultado de la última corrida del loop nocturno
        if self.path.startswith("/nightly/status"):
            f = DATA_DIR / "nightly_last.json"
            self.send_response(200 if f.exists() else 404)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(f.read_bytes() if f.exists()
                             else b'{"error":"aun no hay corrida registrada"}')
            return
        # /nightly → dispara el loop nocturno manualmente (para validar). Corre en
        # segundo plano (clonar+Claude tarda) y respeta el candado de "sin cambios".
        if self.path.startswith("/nightly"):
            threading.Thread(target=nightly_job, daemon=True).start()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("loop nocturno lanzado — mira los logs de Railway "
                             "(o el repo si hubo commit)".encode("utf-8"))
            return
        # /api/overview → sirve el JSON que escribe el refresh (para el dashboard).
        if self.path.startswith("/api/overview"):
            f = DATA_DIR / "overview.json"
            if f.exists():
                body = f.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")  # dashboard lo lee
                self.send_header("Cache-Control", "public, max-age=300")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"error":"overview.json aun no generado"}')
            return
        # / → health
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SLEVE ecommerce agent ok")

    def log_message(self, *a):
        pass


def _run_health():
    try:
        HTTPServer(("0.0.0.0", PORT), _Health).serve_forever()
    except Exception as e:  # noqa: BLE001
        log(f"health server error: {e}")


# --- Procesos long-lived (se relanzan si mueren) ----------------------------
_procs: dict = {}


def _ensure_procs() -> None:
    procs = ["agent/bot.py"]
    if os.environ.get("MCP_ENABLED"):
        procs.append("agent/mcp_server.py")
    for p in procs:
        cur = _procs.get(p)
        if cur is None or cur.poll() is not None:
            if cur is not None:
                log(f"{p} terminó (code={cur.returncode}) → relanzando")
            _procs[p] = subprocess.Popen([sys.executable, "-u", p], cwd=str(ROOT))
            log(f"lanzado {p} (pid={_procs[p].pid})")


# --- Tareas programadas -----------------------------------------------------
def daily_brief() -> None:
    """Manda el brief diario por Telegram (orquestador → especialistas)."""
    try:
        from orchestrator import build_daily_brief
        from bot import send_message
        send_message(build_daily_brief())
        log("brief diario enviado")
    except Exception as e:  # noqa: BLE001
        log(f"error en daily_brief: {e}")


def refresh_data() -> None:
    """Trae la data de las fuentes y actualiza overview.json (cada 2h)."""
    try:
        import refresh
        refresh.refresh()
    except Exception as e:  # noqa: BLE001
        log(f"error en refresh_data: {e}")


def nightly_job() -> None:
    """Loop nocturno: snapshot + (con créditos) auditoría/optimización de los .md."""
    try:
        import nightly_audit
        nightly_audit.nightly_audit()
    except Exception as e:  # noqa: BLE001
        log(f"error nightly: {e}")


def main() -> None:
    log("supervisor E-commerce iniciado")
    threading.Thread(target=_run_health, daemon=True).start()

    _ensure_procs()

    # Refresco de datos al arrancar + cada 2 horas
    refresh_data()
    schedule.every(2).hours.do(refresh_data)
    schedule.every().day.at("08:00").do(daily_brief)
    schedule.every().day.at("02:30").do(nightly_job)   # loop nocturno (macro-ciclo)
    log("agendado: refresh datos cada 2h · brief 08:00 · loop nocturno 02:30 (TZ del contenedor)")

    while True:
        _ensure_procs()
        try:
            schedule.run_pending()
        except Exception as e:  # noqa: BLE001
            log(f"scheduler error: {e}")
        time.sleep(30)


if __name__ == "__main__":
    # agent/ en el path para importar bot/orchestrator como módulos
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
