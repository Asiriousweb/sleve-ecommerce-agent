#!/usr/bin/env python3
"""
Instalador OAuth multi-tienda de Shopify para el robot — token REAL por tienda
(directo y gratis, sin Windsor). Misma app instalada en cada tienda del país.

Flujo: el usuario abre  https://<robot>/shopify  → ve las 6 tiendas → clic "Instalar"
en cada una → autoriza → el robot canjea y guarda el token de esa tienda.

Env (Railway): SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, SHOPIFY_REDIRECT.
Tokens guardados en el VOLUMEN (DATA_DIR/shopify_tokens.json) → mantener volumen montado.
"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

CLIENT_ID = os.environ.get("SHOPIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()
SCOPES = os.environ.get("SHOPIFY_SCOPES", "read_orders,read_products,read_inventory,read_customers")
REDIRECT = os.environ.get(
    "SHOPIFY_REDIRECT",
    "https://sleve-ecommerce-agents-production.up.railway.app/shopify/callback",
)
DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
TOKENS_FILE = DATA_DIR / "shopify_tokens.json"

# país → dominio. Varias tiendas pueden mapear al mismo país (se suman, ej. Chile + B2B).
STORES = [
    ("Chile", "sleve-inc.myshopify.com"),
    ("Chile", "sleve-mobile-reseller-chile.myshopify.com"),   # B2B → suma a Chile
    ("Colombia", "sleve-mobile-colombia.myshopify.com"),
    ("México", "sleve-mobile-mexico.myshopify.com"),
    ("Perú", "sleve-mobile-peru.myshopify.com"),
    ("EEUU", "sleve-mobile-eeuu.myshopify.com"),
]


def _load() -> dict:
    if TOKENS_FILE.exists():
        try:
            return json.loads(TOKENS_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _save(d: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        TOKENS_FILE.write_text(json.dumps(d), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def install_url(shop: str) -> str:
    params = {"client_id": CLIENT_ID, "scope": SCOPES, "redirect_uri": REDIRECT, "state": shop}
    return f"https://{shop}/admin/oauth/authorize?{urllib.parse.urlencode(params)}"


def exchange(shop: str, code: str) -> str:
    url = f"https://{shop}/admin/oauth/access_token"
    data = urllib.parse.urlencode(
        {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code}
    ).encode("utf-8")
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
        tok = json.loads(r.read().decode("utf-8"))["access_token"]
    d = _load()
    d[shop] = tok
    _save(d)
    return tok


def get_token(shop: str):
    return _load().get(shop)


def index_html() -> str:
    """Página con las tiendas y su estado de conexión + links de instalación."""
    toks = _load()
    rows = []
    for pais, shop in STORES:
        ok = shop in toks
        estado = "🟢 Conectada" if ok else (
            f'<a href="/shopify/install?store={shop}">▶ Instalar</a>')
        rows.append(f"<tr><td>{pais}</td><td>{shop}</td><td>{estado}</td></tr>")
    cfg = "OK" if (CLIENT_ID and CLIENT_SECRET) else "⚠️ faltan SHOPIFY_CLIENT_ID/SECRET en Railway"
    return (
        "<html><body style='font-family:sans-serif;max-width:760px;margin:40px auto'>"
        "<h2>SLEVE · Conectar tiendas Shopify</h2>"
        f"<p>Config: {cfg}</p>"
        "<table cellpadding=8 style='border-collapse:collapse' border=1>"
        "<tr><th>País</th><th>Tienda</th><th>Estado</th></tr>"
        + "".join(rows) +
        "</table><p>Haz clic en <b>Instalar</b> en cada tienda y autoriza. "
        "El token se guarda solo.</p></body></html>"
    )
