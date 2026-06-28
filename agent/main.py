#!/usr/bin/env python3
"""
SLEVE Agent — servicio always-on (Railway).

Fase 1: escucha Telegram (long-polling), responde comandos y manda briefs.
        Sin dependencias externas (solo stdlib). Health HTTP en $PORT para Railway.
Fase 2 (siguiente): conectar el cerebro (Claude Agent SDK) para que los comandos
        disparen al orquestador y a los especialistas con análisis en vivo.
        Ver el hook `handle_command()` → TODO.

Variables de entorno (configurar en Railway, NUNCA en el repo):
    TELEGRAM_BOT_TOKEN   (de @BotFather)
    TELEGRAM_CHAT_ID     (chat autorizado; el bot solo responde a este)
    PORT                 (lo inyecta Railway; default 8080)
"""

import json
import os
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

API = "https://api.telegram.org/bot{token}/{method}"

# ----------------------------------------------------------------------------
# Config / credenciales
# ----------------------------------------------------------------------------
def _load_local_env():
    """Para correr local: lee ../secrets/.env si existe. En Railway usa env vars."""
    env_path = Path(__file__).resolve().parent.parent / "secrets" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_local_env()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
PORT = int(os.environ.get("PORT", "8080"))


# ----------------------------------------------------------------------------
# Telegram helpers (stdlib)
# ----------------------------------------------------------------------------
def tg(method, params):
    url = API.format(token=TOKEN, method=method)
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send(text, chat_id=None):
    try:
        tg("sendMessage", {"chat_id": chat_id or CHAT_ID, "text": text,
                           "disable_web_page_preview": "true"})
    except Exception as e:  # noqa: BLE001
        print(f"[send] error: {e}", flush=True)


# ----------------------------------------------------------------------------
# Comandos
# ----------------------------------------------------------------------------
HELP = (
    "🤖 SLEVE Agent — comandos\n"
    "/brief — resumen de Chile\n"
    "/estado — estado del sistema\n"
    "/ping — test de vida\n"
    "/help — esta ayuda\n\n"
    "(Pronto: /ads /marketplaces /social /cro con análisis en vivo)"
)

BRIEF_CHILE = (
    "🟢 SLEVE · Brief Chile (30 días)\n"
    "• Ventas sitio: $76,6M CLP · 2.349 ped. · AOV $24.851\n"
    "• Conversión: 1,25% · fuga de checkout 77%\n"
    "• Top: Pulse ANC 2Gen $27,4M · One 2Gen $9,4M\n"
    "• Ads: Google 1,98% conv (3x Meta) · TikTok 0,43% (ineficiente)\n"
    "🚨 TikTok quema · fuga checkout · México inactivo\n"
    "(Datos demo/baseline — en vivo al conectar Multivende/Windsor)"
)

ESTADO = (
    "📊 Estado SLEVE\n"
    "🟢 Shopify CL · GA4 · Google Ads · Klaviyo · Telegram\n"
    "🟡 Meta Ads (ordenar) · Dashboard v0.1\n"
    "🔴 Multivende · TikTok · Metricool · Gorgias · Shopify multi-tienda\n"
    "8 especialistas mapeados · orquestador activo"
)


def handle_command(text, chat_id):
    cmd = text.strip().lower().split()[0] if text.strip() else ""
    if cmd in ("/start", "/help"):
        send(HELP, chat_id)
    elif cmd == "/ping":
        send("pong ✅", chat_id)
    elif cmd == "/brief":
        send(BRIEF_CHILE, chat_id)
    elif cmd == "/estado":
        send(ESTADO, chat_id)
    else:
        # TODO Fase 2: enrutar al orquestador (Claude Agent SDK) → especialistas.
        send("Recibido. Comandos: /brief /estado /ping /help", chat_id)


# ----------------------------------------------------------------------------
# Health server (Railway necesita un puerto abierto)
# ----------------------------------------------------------------------------
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"SLEVE agent ok")

    def log_message(self, *args):
        pass  # silencio


def run_health():
    HTTPServer(("0.0.0.0", PORT), Health).serve_forever()


# ----------------------------------------------------------------------------
# Loop principal: long-polling de Telegram
# ----------------------------------------------------------------------------
def poll_loop():
    print("[agent] iniciando long-polling de Telegram", flush=True)
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset
            resp = tg("getUpdates", params)
            for upd in resp.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message") or {}
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "")
                if not text:
                    continue
                # Seguridad: solo responder al chat autorizado
                if CHAT_ID and chat_id != CHAT_ID:
                    print(f"[agent] ignorado chat no autorizado {chat_id}", flush=True)
                    continue
                print(f"[agent] cmd: {text}", flush=True)
                handle_command(text, chat_id)
        except Exception as e:  # noqa: BLE001
            print(f"[poll] error: {e}", flush=True)
            time.sleep(5)


def main():
    if not TOKEN:
        raise SystemExit("ERROR: falta TELEGRAM_BOT_TOKEN en el entorno.")
    threading.Thread(target=run_health, daemon=True).start()
    if CHAT_ID:
        send("🟢 SLEVE Agent online (Railway). Escribe /help.")
    poll_loop()


if __name__ == "__main__":
    main()
