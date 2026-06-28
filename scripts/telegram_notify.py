#!/usr/bin/env python3
"""
telegram_notify.py — Canal de reporte del Agente SLEVE por Telegram.

Sin dependencias externas (usa solo la librería estándar de Python 3).
Lee las credenciales desde variables de entorno o desde secrets/.env:
    TELEGRAM_BOT_TOKEN   (de @BotFather)
    TELEGRAM_CHAT_ID     (id del chat del usuario; se descubre con --get-chat-id)

Uso:
    python3 scripts/telegram_notify.py --get-chat-id     # descubre tu chat_id
    python3 scripts/telegram_notify.py --test            # envía un mensaje de prueba
    python3 scripts/telegram_notify.py "Tu mensaje"      # envía un mensaje

Como módulo:
    from telegram_notify import send_message
    send_message("Hola desde el agente SLEVE")
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.telegram.org/bot{token}/{method}"
SECRETS_ENV = Path(__file__).resolve().parent.parent / "secrets" / ".env"


def _load_env():
    """Carga secrets/.env (KEY=VALUE) en os.environ sin pisar lo ya definido."""
    if SECRETS_ENV.exists():
        for line in SECRETS_ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def _get(name):
    _load_env()
    val = os.environ.get(name, "").strip()
    return val


def _api_call(method, params):
    token = _get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "ERROR: falta TELEGRAM_BOT_TOKEN. Ponlo en secrets/.env "
            "(copia secrets/.env.example) o como variable de entorno."
        )
    url = API_BASE.format(token=token, method=method)
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        raise SystemExit(f"ERROR Telegram HTTP {e.code}: {body}")
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"ERROR de red al hablar con Telegram: {e}")


def send_message(text, parse_mode="Markdown", chat_id=None):
    """Envía un mensaje al chat del usuario. Devuelve la respuesta de la API."""
    chat_id = chat_id or _get("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise SystemExit(
            "ERROR: falta TELEGRAM_CHAT_ID. Corre primero: "
            "python3 scripts/telegram_notify.py --get-chat-id"
        )
    resp = _api_call(
        "sendMessage",
        {"chat_id": chat_id, "text": text, "parse_mode": parse_mode,
         "disable_web_page_preview": "true"},
    )
    if not resp.get("ok"):
        raise SystemExit(f"ERROR: Telegram rechazó el envío: {resp}")
    return resp


def get_chat_id():
    """Lista los chats recientes que han escrito al bot (para hallar el chat_id)."""
    resp = _api_call("getUpdates", {})
    if not resp.get("ok"):
        raise SystemExit(f"ERROR getUpdates: {resp}")
    updates = resp.get("result", [])
    if not updates:
        print(
            "No hay mensajes todavía.\n"
            "1) Abre tu bot en Telegram y presiona Start (o escríbele algo).\n"
            "2) Vuelve a correr: python3 scripts/telegram_notify.py --get-chat-id"
        )
        return
    seen = {}
    for u in updates:
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat", {})
        if chat.get("id") and chat["id"] not in seen:
            seen[chat["id"]] = chat
    print("Chats detectados (usa el id en TELEGRAM_CHAT_ID):")
    for cid, chat in seen.items():
        nombre = chat.get("title") or " ".join(
            filter(None, [chat.get("first_name"), chat.get("last_name")])
        ) or chat.get("username", "")
        print(f"  chat_id = {cid}   ({chat.get('type')}: {nombre})")


def main(argv):
    if not argv:
        print(__doc__)
        return
    if argv[0] == "--get-chat-id":
        get_chat_id()
    elif argv[0] == "--test":
        send_message("✅ *Agente SLEVE* conectado a Telegram. Canal de reporte operativo.")
        print("Mensaje de prueba enviado.")
    else:
        send_message(" ".join(argv))
        print("Mensaje enviado.")


if __name__ == "__main__":
    main(sys.argv[1:])
