#!/usr/bin/env python3
"""
Metricool directo (API v2) — analytics de redes orgánico por país.

Hub de social orgánico (patrón MeLi, no vía Windsor). Auth: header `X-Mc-Auth`
(token) + params `userId`/`blogId` en cada llamada. Base https://app.metricool.com/api.

Solo el TOKEN es secreto → va en env `METRICOOL_USER_TOKEN` (cargado en Railway).
Los userId/blogId NO son secretos → defaults acá, override por env si hiciera falta.

Estructura de marcas SLEVE en Metricool (1 marca por país):
  • B2C  = "SLEVE MOBILE {país}"  (IG/FB/TikTok/YouTube/Threads…)
  • LI   = "SLEVE {país} LINKEDIN" (LinkedIn corporativo)

Endpoints (descubiertos del CLI oficial Purple-Horizons/metricool-cli):
  /v2/analytics/{red}/profile        → seguidores + métricas de perfil
  /v2/analytics/posts/{red}?from&to  → engagement por post
  /stats/timeline/{métrica}?start&end→ evolución temporal (YYYYMMDD)
"""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = "https://app.metricool.com/api"
TOKEN = os.environ.get("METRICOOL_USER_TOKEN", "").strip()
USER_ID = os.environ.get("METRICOOL_USER_ID", "2242712").strip()

# blogId por país (no secretos). Override por env var si cambian.
BLOG_B2C = {
    "Chile":    os.environ.get("METRICOOL_BLOG_CL", "2787256"),
    "Colombia": os.environ.get("METRICOOL_BLOG_CO", "2802473"),
    "México":   os.environ.get("METRICOOL_BLOG_MX", "4740435"),
    "Perú":     os.environ.get("METRICOOL_BLOG_PE", "2803017"),
}
BLOG_LI = {
    "Chile":    os.environ.get("METRICOOL_LI_CL", "5422593"),
    "Colombia": os.environ.get("METRICOOL_LI_CO", "5422618"),
    "México":   os.environ.get("METRICOOL_LI_MX", "5422620"),
    "Perú":     os.environ.get("METRICOOL_LI_PE", "5422614"),
}
# Extras (fuera de los 4 países del dashboard; guardados por completitud).
BLOG_EXTRA = {"EEUU_LI": "5422600", "Global_LI": "5980526"}

PAISES = ["Chile", "Colombia", "México", "Perú"]
REDES_B2C = ["instagram", "facebook", "tiktok", "youtube"]  # redes B2C a traer del hub


def _get(endpoint, blog_id):
    """GET a la API de Metricool con auth + userId/blogId. Devuelve dict/list (JSON)."""
    if not TOKEN:
        raise RuntimeError("sin METRICOOL_USER_TOKEN")
    sep = "&" if "?" in endpoint else "?"
    url = f"{BASE}{endpoint}{sep}userId={USER_ID}&blogId={blog_id}"
    req = urllib.request.Request(url, headers={
        "X-Mc-Auth": TOKEN, "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def _rango(dias=7):
    hoy = datetime.now(timezone.utc).date()
    return (hoy - timedelta(days=dias)).isoformat(), hoy.isoformat()


def probe(pais="Chile"):
    """Diagnóstico: trae respuestas CRUDAS de un país para descubrir la estructura real.
    Perfil IG + perfil FB + posts IG (7d). No expone el token. Recorta el volumen."""
    blog = BLOG_B2C.get(pais)
    since, until = _rango(7)
    ensayos = {
        "instagram/profile": "/v2/analytics/instagram/profile",
        "facebook/profile": "/v2/analytics/facebook/profile",
        "posts/instagram": f"/v2/analytics/posts/instagram?from={since}&to={until}",
    }
    out = {"pais": pais, "blogId": blog, "userId": USER_ID, "token_set": bool(TOKEN)}
    for nombre, ep in ensayos.items():
        try:
            d = _get(ep, blog)
            # Resumen de estructura: tipo + keys de primer nivel + muestra recortada
            if isinstance(d, dict):
                info = {"tipo": "dict", "keys": list(d.keys())[:40]}
            elif isinstance(d, list):
                info = {"tipo": "list", "len": len(d),
                        "keys_item0": list(d[0].keys())[:40] if d and isinstance(d[0], dict) else None}
            else:
                info = {"tipo": type(d).__name__}
            info["muestra"] = json.dumps(d, ensure_ascii=False)[:1500]
            out[nombre] = info
        except urllib.error.HTTPError as he:
            out[nombre] = f"HTTP {he.code}: {he.read().decode('utf-8', 'ignore')[:200]}"
        except Exception as e:  # noqa: BLE001
            out[nombre] = f"ERROR: {str(e)[:200]}"
    return out


def pull_metricool():
    """Analytics de redes por país (se completa el parsing tras validar la estructura con probe).
    Por ahora devuelve ({}, 'pendiente probe') hasta confirmar los campos reales."""
    if not TOKEN:
        return {}, "sin METRICOOL_USER_TOKEN"
    return {}, "pendiente: correr /metricool/probe y ajustar parsing"


if __name__ == "__main__":
    print(json.dumps(probe("Chile"), ensure_ascii=False, indent=2))
