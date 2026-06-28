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


# --- Health server (Railway) ------------------------------------------------
class _Health(BaseHTTPRequestHandler):
    def do_GET(self):
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


def main() -> None:
    log("supervisor E-commerce iniciado")
    threading.Thread(target=_run_health, daemon=True).start()

    _ensure_procs()

    schedule.every().day.at("08:00").do(daily_brief)
    log("agendado: brief diario 08:00 (TZ del contenedor)")

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
