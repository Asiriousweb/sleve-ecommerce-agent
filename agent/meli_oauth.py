#!/usr/bin/env python3
"""
Conector OAuth de Mercado Libre para el robot — DIRECTO (gratis), una cuenta por país.
Reemplaza a Nubimetrics para la data de ML; luego se cuadra con Multivende.

Flujo (igual que Shopify): el usuario abre  https://<robot>/meli  → ve los 4 países →
clic "Conectar" → inicia sesión con la cuenta ML de ese país → autoriza → el robot canjea
el code por access_token + refresh_token y lo guarda. El token dura 6h → se renueva solo.

Cada cuenta ML pertenece a un site (MLC/MCO/MLM/MPE) → el país se deriva de /users/me,
no del state, así no importa con qué cuenta autorice.

Env (Railway): MELI_CLIENT_ID, MELI_CLIENT_SECRET, MELI_REDIRECT.
Tokens en el VOLUMEN (DATA_DIR/meli_tokens.json) → mantener el volumen montado.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

CLIENT_ID = os.environ.get("MELI_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("MELI_CLIENT_SECRET", "").strip()
REDIRECT = os.environ.get(
    "MELI_REDIRECT",
    "https://sleve-ecommerce-agents-production.up.railway.app/meli/callback",
)
DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
TOKENS_FILE = DATA_DIR / "meli_tokens.json"

API = "https://api.mercadolibre.com"
# Dominio de login (autorización) por país.
AUTH_DOMAIN = {
    "Chile": "https://auth.mercadolibre.cl",
    "Colombia": "https://auth.mercadolibre.com.co",
    "México": "https://auth.mercadolibre.com.mx",
    "Perú": "https://auth.mercadolibre.com.pe",
}
SITE_TO_PAIS = {"MLC": "Chile", "MCO": "Colombia", "MLM": "México", "MPE": "Perú"}
PAISES = ["Chile", "Colombia", "México", "Perú"]


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


def _post_token(params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(f"{API}/oauth/token", data=data, headers={
        "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _api_get(path: str, token: str) -> dict:
    req = urllib.request.Request(f"{API}{path}", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def install_url(pais: str) -> str:
    dom = AUTH_DOMAIN.get(pais, "https://auth.mercadolibre.com")
    params = {"response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT, "state": pais}
    return f"{dom}/authorization?{urllib.parse.urlencode(params)}"


def exchange(code: str) -> str:
    """Canjea el code por tokens, identifica el país vía /users/me y guarda."""
    tok = _post_token({
        "grant_type": "authorization_code", "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET, "code": code, "redirect_uri": REDIRECT})
    access = tok["access_token"]
    me = _api_get("/users/me", access)
    site = me.get("site_id", "")
    pais = SITE_TO_PAIS.get(site, site or "?")
    d = _load()
    d[pais] = {
        "access_token": access, "refresh_token": tok.get("refresh_token"),
        "user_id": me.get("id"), "site_id": site, "nickname": me.get("nickname"),
        "expires_at": time.time() + int(tok.get("expires_in", 21600)) - 120,
    }
    _save(d)
    return pais


def _refresh(pais: str, rec: dict) -> dict:
    tok = _post_token({
        "grant_type": "refresh_token", "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET, "refresh_token": rec.get("refresh_token")})
    rec["access_token"] = tok["access_token"]
    if tok.get("refresh_token"):
        rec["refresh_token"] = tok["refresh_token"]
    rec["expires_at"] = time.time() + int(tok.get("expires_in", 21600)) - 120
    d = _load()
    d[pais] = rec
    _save(d)
    return rec


def get_account(pais: str):
    """Devuelve (access_token, user_id) válidos para el país, refrescando si expiró. None si no conectado."""
    rec = _load().get(pais)
    if not rec:
        return None
    if time.time() >= rec.get("expires_at", 0):
        try:
            rec = _refresh(pais, rec)
        except Exception:  # noqa: BLE001
            return None
    return rec.get("access_token"), rec.get("user_id")


def index_html() -> str:
    toks = _load()
    rows = []
    for pais in PAISES:
        rec = toks.get(pais)
        estado = (f"🟢 {rec.get('nickname') or 'conectada'} (user {rec.get('user_id')})" if rec
                  else f'<a href="/meli/install?pais={urllib.parse.quote(pais)}">▶ Conectar</a>')
        rows.append(f"<tr><td>{pais}</td><td>{estado}</td></tr>")
    cfg = "OK" if (CLIENT_ID and CLIENT_SECRET) else "⚠️ faltan MELI_CLIENT_ID/SECRET en Railway"
    return (
        "<html><body style='font-family:sans-serif;max-width:760px;margin:40px auto'>"
        "<h2>SLEVE · Conectar Mercado Libre</h2>"
        f"<p>Config: {cfg}</p><p>Redirect configurado: <code>{REDIRECT}</code></p>"
        "<table cellpadding=8 style='border-collapse:collapse' border=1>"
        "<tr><th>País</th><th>Estado</th></tr>" + "".join(rows) +
        "</table><p>Haz clic en <b>Conectar</b> en cada país e inicia sesión con la cuenta ML "
        "de ese país. El token se guarda y se renueva solo.</p></body></html>"
    )
