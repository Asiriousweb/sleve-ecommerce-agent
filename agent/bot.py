#!/usr/bin/env python3
"""
Bot de Telegram del agente E-commerce (long-polling, sin dependencias externas).
Comandos deterministas (no necesita ANTHROPIC_API_KEY). El razonamiento en lenguaje
natural (vía Anthropic API) se agrega en orchestrator.ask() — ver TODO.

Credenciales: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (en Railway = env vars; local = ../secrets/.env).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.telegram.org/bot{token}/{method}"


def _load_local_env():
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


def _tg(method, params):
    url = API.format(token=TOKEN, method=method)
    data = urllib.parse.urlencode(params).encode("utf-8")
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def send_message(text, chat_id=None):
    try:
        _tg("sendMessage", {"chat_id": chat_id or CHAT_ID, "text": text,
                            "disable_web_page_preview": "true"})
    except Exception as e:  # noqa: BLE001
        print(f"[bot] send error: {e}", flush=True)


def _handle(text, chat_id):
    # import diferido para no acoplar el arranque
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import orchestrator
    parts = text.strip().split()
    cmd = parts[0].lower() if parts else ""
    arg = " ".join(parts[1:]) if len(parts) > 1 else ""
    if cmd in ("/start", "/help"):
        send_message(orchestrator.HELP, chat_id)
    elif cmd == "/ping":
        send_message("pong ✅ (ecommerce)", chat_id)
    elif cmd in ("/resumen", "/brief"):
        send_message(orchestrator.resumen("7d"), chat_id)
    elif cmd in ("/ml", "/marketplaces", "/mercadolibre"):
        send_message(orchestrator.mercadolibre("7d"), chat_id)
    elif cmd == "/ads":
        send_message(orchestrator.ads("7d"), chat_id)
    elif cmd in ("/acciones", "/urgencias"):
        send_message(orchestrator.acciones("7d"), chat_id)
    elif cmd == "/pais":
        send_message(orchestrator.pais(arg or "chile", "7d"), chat_id)
    elif cmd == "/estado":
        send_message(orchestrator.estado(), chat_id)
    else:
        # Texto libre → lenguaje natural (Claude API si hay ANTHROPIC_API_KEY; si no, guía)
        send_message(orchestrator.ask(text), chat_id)


def main():
    if not TOKEN:
        raise SystemExit("ERROR: falta TELEGRAM_BOT_TOKEN")
    print("[bot] long-polling iniciado", flush=True)
    if CHAT_ID:
        send_message("🔵 SLEVE E-commerce Agent online. /help para comandos.")
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset
            resp = _tg("getUpdates", params)
            for upd in resp.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message") or {}
                cid = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "")
                if not text:
                    continue
                if CHAT_ID and cid != CHAT_ID:
                    continue  # solo el chat autorizado
                print(f"[bot] cmd: {text}", flush=True)
                _handle(text, cid)
        except Exception as e:  # noqa: BLE001
            print(f"[bot] poll error: {e}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
