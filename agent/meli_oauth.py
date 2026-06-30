#!/usr/bin/env python3
"""
Conector OAuth de Mercado Libre para el robot — DIRECTO (gratis), UNA APP POR PAÍS.
Cada país tiene su propia app de ML (admins distintos) → credenciales por país,
con fallback a las globales (para Chile, que se conectó con la app inicial).
Reemplaza a Nubimetrics; luego se cuadra con Multivende.

Flujo (igual que Shopify): el usuario abre  https://<robot>/meli  → ve los 4 países →
clic "Conectar" → inicia sesión con la cuenta ML de ese país → autoriza → el robot
canjea el code por access_token + refresh_token y lo guarda. Token dura 6h → se renueva solo.

Env por país (Railway): MELI_CLIENT_ID_CL/CO/MX/PE + MELI_CLIENT_SECRET_CL/CO/MX/PE.
Fallback global: MELI_CLIENT_ID / MELI_CLIENT_SECRET (usado si no hay del país).
Redirect (común a todas las apps): MELI_REDIRECT.
Tokens en el VOLUMEN (DATA_DIR/meli_tokens.json) → mantener el volumen montado.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

REDIRECT = os.environ.get(
    "MELI_REDIRECT",
    "https://sleve-ecommerce-agents-production.up.railway.app/meli/callback",
)
DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
TOKENS_FILE = DATA_DIR / "meli_tokens.json"

API = "https://api.mercadolibre.com"
AUTH_DOMAIN = {
    "Chile": "https://auth.mercadolibre.cl",
    "Colombia": "https://auth.mercadolibre.com.co",
    "México": "https://auth.mercadolibre.com.mx",
    "Perú": "https://auth.mercadolibre.com.pe",
}
PAIS_CC = {"Chile": "CL", "Colombia": "CO", "México": "MX", "Perú": "PE"}
SITE_TO_PAIS = {"MLC": "Chile", "MCO": "Colombia", "MLM": "México", "MPE": "Perú"}
PAISES = ["Chile", "Colombia", "México", "Perú"]


def _creds(pais: str):
    """(client_id, client_secret) de la app del país. Fallback al global SOLO para Chile
    (que se conectó con la app inicial); CO/MX/PE requieren su propia app, o no hay botón."""
    cc = PAIS_CC.get(pais, "")
    cid = os.environ.get(f"MELI_CLIENT_ID_{cc}", "").strip()
    sec = os.environ.get(f"MELI_CLIENT_SECRET_{cc}", "").strip()
    if not (cid and sec) and pais == "Chile":
        cid = cid or os.environ.get("MELI_CLIENT_ID", "").strip()
        sec = sec or os.environ.get("MELI_CLIENT_SECRET", "").strip()
    return cid, sec


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
    cid, _ = _creds(pais)
    dom = AUTH_DOMAIN.get(pais, "https://auth.mercadolibre.com")
    params = {"response_type": "code", "client_id": cid, "redirect_uri": REDIRECT, "state": pais}
    return f"{dom}/authorization?{urllib.parse.urlencode(params)}"


def exchange(code: str, pais: str) -> str:
    """Canjea el code con las credenciales del país (state). Verifica que la cuenta sea de ese país."""
    cid, sec = _creds(pais)
    if not (cid and sec):
        raise RuntimeError(f"faltan MELI_CLIENT_ID_{PAIS_CC.get(pais)}/SECRET en Railway")
    tok = _post_token({
        "grant_type": "authorization_code", "client_id": cid, "client_secret": sec,
        "code": code, "redirect_uri": REDIRECT})
    access = tok["access_token"]
    me = _api_get("/users/me", access)
    site = me.get("site_id", "")
    pais_real = SITE_TO_PAIS.get(site, site)
    if pais_real != pais:
        raise RuntimeError(f"autorizaste una cuenta de {pais_real} pero elegiste {pais}. "
                           "Reconecta con la cuenta de Mercado Libre correcta.")
    d = _load()
    d[pais] = {
        "access_token": access, "refresh_token": tok.get("refresh_token"),
        "user_id": me.get("id"), "site_id": site, "nickname": me.get("nickname"),
        "expires_at": time.time() + int(tok.get("expires_in", 21600)) - 120,
    }
    _save(d)
    return pais


def disconnect(pais: str) -> None:
    d = _load()
    if pais in d:
        del d[pais]
        _save(d)


def _refresh(pais: str, rec: dict) -> dict:
    cid, sec = _creds(pais)
    tok = _post_token({
        "grant_type": "refresh_token", "client_id": cid, "client_secret": sec,
        "refresh_token": rec.get("refresh_token")})
    rec["access_token"] = tok["access_token"]
    if tok.get("refresh_token"):
        rec["refresh_token"] = tok["refresh_token"]
    rec["expires_at"] = time.time() + int(tok.get("expires_in", 21600)) - 120
    d = _load()
    d[pais] = rec
    _save(d)
    return rec


def get_account(pais: str):
    """(access_token, user_id) válidos para el país, refrescando si expiró. None si no conectado."""
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
        cid, sec = _creds(pais)
        if rec:
            estado = (f"🟢 {rec.get('nickname') or 'conectada'} (user {rec.get('user_id')}) "
                      f'· <a href="/meli/disconnect?pais={urllib.parse.quote(pais)}">desconectar</a>')
        elif cid and sec:
            estado = f'<a href="/meli/install?pais={urllib.parse.quote(pais)}">▶ Conectar</a>'
        else:
            estado = f"⚠️ falta MELI_CLIENT_ID_{PAIS_CC.get(pais)} / SECRET en Railway"
        rows.append(f"<tr><td>{pais}</td><td>{estado}</td></tr>")
    return (
        "<html><body style='font-family:sans-serif;max-width:760px;margin:40px auto'>"
        "<h2>SLEVE · Conectar Mercado Libre (una app por país)</h2>"
        f"<p>Redirect (común a las 4 apps): <code>{REDIRECT}</code></p>"
        "<table cellpadding=8 style='border-collapse:collapse' border=1>"
        "<tr><th>País</th><th>Estado</th></tr>" + "".join(rows) +
        "</table><p>Cada país usa su propia app (credenciales <code>MELI_CLIENT_ID_CL/CO/MX/PE</code>). "
        "Haz clic en <b>Conectar</b> e inicia sesión con la cuenta ML de ese país. "
        "El token se guarda y se renueva solo.</p></body></html>"
    )
