#!/usr/bin/env python3
"""
Refrescador de datos del agente E-commerce. Corre cada 2h (lo agenda run_railway.py).
Trae la data real de Windsor y la AGREGA por país, lista para el dashboard.

IMPORTANTE: el robot usa SUS PROPIAS llaves (env vars), no los MCPs de la sesión Claude.
- WINDSOR_API_KEY → una sola llave abre todas las fuentes de Windsor.
- Directas (a futuro): SHOPIFY_TOKEN (ventas $ reales), KLAVIYO_API_KEY, MULTIVENDE_TOKEN.

HOY trae REAL: GA4 (sesiones, transacciones, conversión, fuentes de tráfico) + Google Ads
(gasto, ROAS) por país. Ventas $ reales requieren Shopify (pendiente).
Sin WINDSOR_API_KEY escribe un baseline placeholder para que el pipeline igual funcione.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT = DATA_DIR / "overview.json"

WINDSOR_API_KEY = os.environ.get("WINDSOR_API_KEY", "").strip()
WINDSOR_BASE = "https://connectors.windsor.ai"  # el conector va en la ruta: /{connector}
RANGO = "last_7d"
PAISES = ["Chile", "Colombia", "México", "Perú"]

# Shopify directo multi-tienda — un token por tienda vía OAuth (ver shopify_oauth.py).
import shopify_oauth
SHOPIFY_API_VERSION = "2025-10"

# Meta Ads directo (Marketing API) — gratis. Token de System User (Business Manager) con ads_read.
META_TOKEN = os.environ.get("META_TOKEN", "").strip()
META_API_VERSION = "v21.0"


def _log(m):
    print(f"[refresh {datetime.now(timezone.utc):%F %T}Z] {m}", flush=True)


def _country(name: str) -> str:
    n = (name or "").lower()
    if "colombia" in n:
        return "Colombia"
    if "mexic" in n or "méxic" in n:
        return "México"
    if "peru" in n or "perú" in n:
        return "Perú"
    return "Chile"


def pull_windsor(connector: str, fields: list[str], date_preset: str = RANGO):
    if not WINDSOR_API_KEY:
        return None
    params = {"api_key": WINDSOR_API_KEY, "fields": ",".join(fields), "date_preset": date_preset}
    url = f"{WINDSOR_BASE}/{connector}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            payload = json.loads(r.read().decode("utf-8"))
        return payload.get("data", payload) if isinstance(payload, dict) else payload
    except Exception as e:  # noqa: BLE001
        _log(f"windsor {connector} error: {e}")
        return None


def _num(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def pull_shopify(shop, token):
    """Ventas de una tienda (Admin API GraphQL, directo). Devuelve (data|None, debug)."""
    if not (shop and token):
        return None, "sin token"
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://{shop}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    q = ('query($cursor:String){orders(first:250,after:$cursor,query:"created_at:>=%s"){'
         'pageInfo{hasNextPage endCursor} nodes{totalPriceSet{shopMoney{amount}}}}}' % since)
    ventas, pedidos, cursor = 0.0, 0, None
    for _ in range(20):  # tope de páginas (hasta 5000 pedidos)
        body = json.dumps({"query": q, "variables": {"cursor": cursor}}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json", "X-Shopify-Access-Token": token})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as he:
            return None, f"HTTP {he.code}: {he.read().decode('utf-8', 'ignore')[:180]}"
        except Exception as e:  # noqa: BLE001
            return None, f"red: {e}"
        if d.get("errors"):
            return None, f"graphql: {str(d['errors'])[:180]}"
        orders = d.get("data", {}).get("orders", {})
        for n in orders.get("nodes", []):
            ventas += _num(n.get("totalPriceSet", {}).get("shopMoney", {}).get("amount"))
            pedidos += 1
        page = orders.get("pageInfo", {})
        if page.get("hasNextPage"):
            cursor = page.get("endCursor")
        else:
            break
    return ({"ventas": round(ventas), "pedidos": pedidos,
             "aov": round(ventas / pedidos) if pedidos else 0}, f"ok ({pedidos} pedidos)")


def pull_meta():
    """Gasto de Meta Ads por país (Marketing API directa). Descubre las cuentas del token.
    Devuelve ({pais: spend}, debug)."""
    if not META_TOKEN:
        return {}, "sin META_TOKEN"
    base = f"https://graph.facebook.com/{META_API_VERSION}"
    tok = urllib.parse.quote(META_TOKEN)
    try:
        u = f"{base}/me/adaccounts?fields=name,currency&limit=200&access_token={tok}"
        with urllib.request.urlopen(u, timeout=60) as r:
            accts = json.loads(r.read().decode("utf-8")).get("data", [])
    except urllib.error.HTTPError as he:
        return {}, f"HTTP {he.code}: {he.read().decode('utf-8', 'ignore')[:160]}"
    except Exception as e:  # noqa: BLE001
        return {}, f"adaccounts error: {e}"
    by_country, n = {}, 0
    for a in accts:
        name = (a.get("name") or "").strip()
        if not name or any(x in name.upper() for x in ("NO USAR", "ELIMINAR")):
            continue
        try:
            iu = f"{base}/{a.get('id')}/insights?fields=spend&date_preset=last_7d&access_token={tok}"
            with urllib.request.urlopen(iu, timeout=60) as r:
                ins = json.loads(r.read().decode("utf-8")).get("data", [])
            spend = sum(_num(x.get("spend")) for x in ins)
        except Exception:  # noqa: BLE001
            spend = 0
        if spend > 0:
            c = _country(name)
            by_country[c] = by_country.get(c, 0) + spend
            n += 1
    return by_country, f"ok ({n} cuentas con gasto)"


def build_overview() -> dict:
    """Agrega GA4 + Google Ads por país. Devuelve estructura lista para el dashboard."""
    ga4 = pull_windsor("googleanalytics4", ["account_name", "source", "medium", "sessions", "transactions"])
    gads = pull_windsor("google_ads", ["account_name", "spend", "conversions", "conversion_value"])

    if ga4 is None and gads is None:
        return {"fuente": "baseline (placeholder)", "paises": {}, "consolidado": {}}

    paises = {p: {"sesiones": 0, "transacciones": 0, "ad_spend": 0.0, "ad_value": 0.0,
                  "_traffic": []} for p in PAISES}

    # GA4 → sesiones, transacciones y fuentes por país
    for row in (ga4 or []):
        pais = _country(row.get("account_name", ""))
        s, t = _num(row.get("sessions")), _num(row.get("transactions"))
        paises[pais]["sesiones"] += s
        paises[pais]["transacciones"] += t
        src = f'{row.get("source", "?")} / {row.get("medium", "?")}'
        paises[pais]["_traffic"].append({"fuente": src, "sesiones": int(s), "transacciones": int(t)})

    # Google Ads → gasto y valor por país
    for row in (gads or []):
        pais = _country(row.get("account_name", ""))
        paises[pais]["ad_spend"] += _num(row.get("spend"))
        paises[pais]["ad_value"] += _num(row.get("conversion_value"))

    # Métricas derivadas + top de tráfico por país
    for p, d in paises.items():
        ses, tr = d["sesiones"], d["transacciones"]
        d["conversion"] = round(tr / ses * 100, 2) if ses else 0
        d["roas"] = round(d["ad_value"] / d["ad_spend"], 2) if d["ad_spend"] else 0
        d["sesiones"] = int(ses)
        d["transacciones"] = int(tr)
        d["ad_spend"] = round(d["ad_spend"])
        d["ad_value"] = round(d["ad_value"])
        # top 8 fuentes por transacciones, luego sesiones
        top = sorted(d.pop("_traffic"), key=lambda x: (x["transacciones"], x["sesiones"]), reverse=True)[:8]
        for x in top:
            x["conv"] = round(x["transacciones"] / x["sesiones"] * 100, 2) if x["sesiones"] else 0
        d["traffic"] = top

    # Ventas reales por tienda (Shopify directo, multi-tienda) + cuadratura GA4 ↔ Shopify
    shop_dbg = {}
    for pais, domain in shopify_oauth.STORES:
        tok = shopify_oauth.get_token(domain)
        if not tok:
            shop_dbg[domain] = "sin token (instalar en /shopify)"
            continue
        res, dbg = pull_shopify(domain, tok)
        shop_dbg[domain] = dbg
        if res:
            d = paises.setdefault(pais, {"sesiones": 0, "transacciones": 0, "ad_spend": 0,
                                         "ad_value": 0, "conversion": 0, "roas": 0, "traffic": []})
            d["ventas_clp"] = d.get("ventas_clp", 0) + res["ventas"]
            d["pedidos"] = d.get("pedidos", 0) + res["pedidos"]
    # AOV + cuadratura (GA4 transacciones vs Shopify pedidos) por país con ventas
    for pais, d in paises.items():
        if d.get("pedidos"):
            d["aov"] = round(d["ventas_clp"] / d["pedidos"])
            d["cuadratura"] = {
                "ga4_transacciones": d.get("transacciones", 0),
                "shopify_pedidos": d["pedidos"],
                "ok": d.get("transacciones", 0) <= d["pedidos"],
            }

    # Meta Ads directo (gasto por país)
    meta_by, meta_dbg = pull_meta()
    for c, s in meta_by.items():
        d = paises.setdefault(c, {"sesiones": 0, "transacciones": 0, "ad_spend": 0,
                                  "ad_value": 0, "conversion": 0, "roas": 0, "traffic": []})
        d["meta_spend"] = round(s)

    consol = {
        "sesiones": sum(d["sesiones"] for d in paises.values()),
        "transacciones": sum(d["transacciones"] for d in paises.values()),
        "ad_spend": sum(d["ad_spend"] for d in paises.values()),
        "ad_value": sum(d["ad_value"] for d in paises.values()),
    }
    consol["conversion"] = round(consol["transacciones"] / consol["sesiones"] * 100, 2) if consol["sesiones"] else 0
    consol["roas"] = round(consol["ad_value"] / consol["ad_spend"], 2) if consol["ad_spend"] else 0

    return {"fuente": "windsor (en vivo)", "rango": "últimos 7 días",
            "consolidado": consol, "paises": paises, "_shopify": shop_dbg, "_meta": meta_dbg,
            "nota": "GA4 + Google Ads (Windsor). Shopify + Meta Ads directos."}


def refresh() -> None:
    overview = {
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "cadencia": "cada 2h",
        **build_overview(),
    }
    OUT.write_text(json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"overview.json actualizado ({overview.get('fuente')}) → {OUT}")


if __name__ == "__main__":
    refresh()
    print(OUT.read_text(encoding="utf-8")[:600])
