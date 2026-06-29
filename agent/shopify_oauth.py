#!/usr/bin/env python3
"""
Instalador OAuth de Shopify para el robot — obtiene un access token REAL de la tienda
(directo y gratis, sin Windsor). Flujo de 1 clic:

  1. Usuario abre  https://<robot>/shopify/install
  2. Shopify pide autorizar → vuelve a /shopify/callback con un `code`
  3. El robot canjea el code por el access token (offline, no expira) y lo guarda

Env vars (en Railway):
  SHOPIFY_STORE          = sleve-inc.myshopify.com
  SHOPIFY_CLIENT_ID      = (ID de cliente de la app del dev dashboard)
  SHOPIFY_CLIENT_SECRET  = (Secreto de la app)
  SHOPIFY_REDIRECT       = https://<robot>/shopify/callback  (debe coincidir con la app)
"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

STORE = os.environ.get("SHOPIFY_STORE", "").strip()
CLIENT_ID = os.environ.get("SHOPIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()
SCOPES = os.environ.get("SHOPIFY_SCOPES", "read_orders,read_products,read_inventory,read_customers")
REDIRECT = os.environ.get(
    "SHOPIFY_REDIRECT",
    "https://sleve-ecommerce-agents-production.up.railway.app/shopify/callback",
)
DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
TOKEN_FILE = DATA_DIR / "shopify_token.json"


def install_url() -> str:
    params = {
        "client_id": CLIENT_ID,
        "scope": SCOPES,
        "redirect_uri": REDIRECT,
        "state": "sleve-install",
    }
    return f"https://{STORE}/admin/oauth/authorize?{urllib.parse.urlencode(params)}"


def exchange(code: str) -> str:
    """Canjea el code por el access token y lo guarda en el volumen."""
    url = f"https://{STORE}/admin/oauth/access_token"
    data = urllib.parse.urlencode(
        {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code}
    ).encode("utf-8")
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
        tok = json.loads(r.read().decode("utf-8"))["access_token"]
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(json.dumps({"access_token": tok}), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return tok


def saved_token():
    """Token guardado por el OAuth (volumen), si existe."""
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text(encoding="utf-8")).get("access_token")
        except Exception:  # noqa: BLE001
            return None
    return None


def config_status() -> str:
    falta = [k for k, v in {
        "SHOPIFY_STORE": STORE, "SHOPIFY_CLIENT_ID": CLIENT_ID,
        "SHOPIFY_CLIENT_SECRET": CLIENT_SECRET}.items() if not v]
    return "ok" if not falta else "faltan: " + ", ".join(falta)
