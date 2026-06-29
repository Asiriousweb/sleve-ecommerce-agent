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
# Moneda de la VENTA (Shopify) por país. Ojo: el gasto de ads puede ir en otra moneda
# (ej. Meta/Google Ads de Chile en USD) → se captura aparte.
MONEDA_VENTAS = {"Chile": "CLP", "Colombia": "COP", "México": "MXN", "Perú": "PEN", "EEUU": "USD"}
# Fallback de tasas (monto * factor = USD) si la API de FX no responde.
_FX_FALLBACK = {"USD": 1.0, "CLP": 1 / 950.0, "COP": 1 / 4000.0, "MXN": 1 / 18.0, "PEN": 1 / 3.75}

# Shopify directo multi-tienda — un token por tienda vía OAuth (ver shopify_oauth.py).
import shopify_oauth
SHOPIFY_API_VERSION = "2025-10"

# Meta Ads directo (Marketing API) — gratis. Token de System User (Business Manager) con ads_read.
META_TOKEN = os.environ.get("META_TOKEN", "").strip()
META_API_VERSION = "v21.0"

# Klaviyo directo (REST, gratis) — UNA Private API Key (pk_...) POR cuenta/país.
# Cada país es una cuenta Klaviyo distinta (Chile/Colombia/México/Perú) con su PROPIO
# id de métrica "Placed Order" → se autodescubre por cuenta. (La "Sleve Mobile" duplicada
# de Chile se ignora: solo se usa la key que pongas en KLAVIYO_KEY_CL.)
KLAVIYO_REVISION = "2024-10-15"
KLAVIYO_KEY_ENVS = {"Chile": "KLAVIYO_KEY_CL", "Colombia": "KLAVIYO_KEY_CO",
                    "México": "KLAVIYO_KEY_MX", "Perú": "KLAVIYO_KEY_PE"}
KLAVIYO_TZ_BY = {"Chile": "America/Santiago", "Colombia": "America/Bogota",
                 "México": "America/Mexico_City", "Perú": "America/Lima"}

# Google directo (GA4 Data API + Search Console) — UNA service account (GOOGLE_SA_JSON).
# GA4 directo REEMPLAZA a Windsor cuando está configurado (con fallback a Windsor si falla).
GOOGLE_SA_JSON = os.environ.get("GOOGLE_SA_JSON", "").strip()
GA4_PROPS = {"Chile": os.environ.get("GA4_PROP_CL", "").strip(),
             "Colombia": os.environ.get("GA4_PROP_CO", "").strip(),
             "México": os.environ.get("GA4_PROP_MX", "").strip(),
             "Perú": os.environ.get("GA4_PROP_PE", "").strip()}
# Search Console: URL exacta de la propiedad por país (ej. "https://slevemobile.com/" o "sc-domain:slevemobile.com")
SC_SITES = {"Chile": os.environ.get("SC_SITE_CL", "").strip(),
            "Colombia": os.environ.get("SC_SITE_CO", "").strip(),
            "México": os.environ.get("SC_SITE_MX", "").strip(),
            "Perú": os.environ.get("SC_SITE_PE", "").strip()}
GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
SC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Google Ads directo (Ads API) — reusa la service account vía delegación de dominio (Workspace).
# Reemplaza a Windsor para Ads cuando esté configurado (con fallback). Necesita developer token
# con Basic access aprobado + delegación autorizada (scope adwords) en el Admin de Workspace.
GADS_DEV_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "").strip()
GADS_LOGIN_CID = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").strip().replace("-", "")  # MCC
GADS_IMPERSONATE = os.environ.get("GOOGLE_ADS_IMPERSONATE", "").strip()  # usuario del dominio
GADS_API_VERSION = os.environ.get("GOOGLE_ADS_API_VERSION", "v23").strip()  # vigente jun-2026
GADS_SCOPES = ["https://www.googleapis.com/auth/adwords"]
GADS_CIDS = {"Chile": os.environ.get("GADS_CID_CL", "").strip().replace("-", ""),
             "Colombia": os.environ.get("GADS_CID_CO", "").strip().replace("-", ""),
             "México": os.environ.get("GADS_CID_MX", "").strip().replace("-", ""),
             "Perú": os.environ.get("GADS_CID_PE", "").strip().replace("-", "")}


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


def _fx_to_usd():
    """Factor por moneda (monto * factor = USD). Tasas del día (open.er-api, gratis) con fallback."""
    try:
        with urllib.request.urlopen("https://open.er-api.com/v6/latest/USD", timeout=30) as r:
            rates = json.loads(r.read().decode("utf-8")).get("rates", {})
        out = {}
        for ccy in ("USD", "CLP", "COP", "MXN", "PEN"):
            rt = rates.get(ccy)
            out[ccy] = (1.0 / rt) if rt else _FX_FALLBACK.get(ccy, 1.0)
        return out
    except Exception:  # noqa: BLE001
        return dict(_FX_FALLBACK)


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
    Devuelve ({pais: {spend, currency}}, debug). Ojo: Chile suele estar en USD."""
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
        currency = (a.get("currency") or "USD").strip()
        try:
            iu = f"{base}/{a.get('id')}/insights?fields=spend&date_preset=last_7d&access_token={tok}"
            with urllib.request.urlopen(iu, timeout=60) as r:
                ins = json.loads(r.read().decode("utf-8")).get("data", [])
            spend = sum(_num(x.get("spend")) for x in ins)
        except Exception:  # noqa: BLE001
            spend = 0
        if spend > 0:
            c = _country(name)
            cur = by_country.setdefault(c, {"spend": 0.0, "currency": currency})
            cur["spend"] += spend
            n += 1
    return by_country, f"ok ({n} cuentas con gasto)"


def _klaviyo_get(path, key):
    req = urllib.request.Request("https://a.klaviyo.com" + path, headers={
        "Authorization": f"Klaviyo-API-Key {key}", "revision": KLAVIYO_REVISION,
        "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def _klaviyo_placed_order_id(key):
    """Autodescubre el id de la métrica 'Placed Order' de esa cuenta (es por-cuenta)."""
    path = "/api/metrics/?fields%5Bmetric%5D=name,integration"
    for _ in range(6):  # sigue paginación por si acaso
        d = _klaviyo_get(path, key)
        for m in d.get("data", []):
            if (m.get("attributes", {}).get("name") or "").strip().lower() == "placed order":
                return m.get("id")
        nxt = (d.get("links") or {}).get("next")
        if not nxt:
            break
        path = nxt.replace("https://a.klaviyo.com", "")
    return None


def _klaviyo_one(pais, key):
    """Revenue atribuido (email/SMS) de UNA cuenta Klaviyo, 7d. (data|None, debug)."""
    try:
        metric_id = _klaviyo_placed_order_id(key)
    except urllib.error.HTTPError as he:
        return None, f"HTTP {he.code}: {he.read().decode('utf-8', 'ignore')[:120]}"
    except Exception as e:  # noqa: BLE001
        return None, f"metrics: {e}"
    if not metric_id:
        return None, "sin métrica Placed Order"
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00")
    until = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")
    body = json.dumps({"data": {"type": "metric-aggregate", "attributes": {
        "metric_id": metric_id, "measurements": ["sum_value", "count"],
        "by": ["$attributed_channel"], "interval": "day",
        "timezone": KLAVIYO_TZ_BY.get(pais, "UTC"),
        "filter": [f"greater-or-equal(datetime,{since})", f"less-than(datetime,{until})"],
    }}}).encode("utf-8")
    req = urllib.request.Request(
        "https://a.klaviyo.com/api/metric-aggregates/", data=body, headers={
            "Authorization": f"Klaviyo-API-Key {key}", "revision": KLAVIYO_REVISION,
            "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as he:
        return None, f"HTTP {he.code}: {he.read().decode('utf-8', 'ignore')[:120]}"
    except Exception as e:  # noqa: BLE001
        return None, f"agg: {e}"
    rows = ((d.get("data", {}) or {}).get("attributes", {}) or {}).get("data", [])
    by_ch = {}
    for row in rows:
        ch = (row.get("dimensions") or ["?"])[0]
        m = row.get("measurements", {})
        rev = sum(_num(x) for x in (m.get("sum_value") or []))
        cnt = sum(_num(x) for x in (m.get("count") or []))
        if rev or cnt:
            by_ch[ch] = {"revenue": round(rev), "pedidos": int(cnt)}
    email = by_ch.get("$email_channel", {})
    return ({"email_revenue": email.get("revenue", 0),
             "email_pedidos": email.get("pedidos", 0),
             "by_channel": by_ch}, f"ok ({len(by_ch)} canales)")


def pull_klaviyo():
    """Multi-cuenta: una Private API Key por país. Devuelve ({pais: data}, {pais: debug})."""
    keys = {}
    for pais, env in KLAVIYO_KEY_ENVS.items():
        v = os.environ.get(env, "").strip()
        if v:
            keys[pais] = v
    if "Chile" not in keys:  # back-compat con la env vieja
        legacy = os.environ.get("KLAVIYO_API_KEY", "").strip()
        if legacy:
            keys["Chile"] = legacy
    if not keys:
        return {}, "sin KLAVIYO_KEY_* (CL/CO/MX/PE)"
    out, dbg = {}, {}
    for pais, key in keys.items():
        data, d = _klaviyo_one(pais, key)
        dbg[pais] = d
        if data:
            out[pais] = data
    return out, dbg


def _google_token(scopes, subject=None):
    """Access token de la service account (GOOGLE_SA_JSON). `subject` = usuario a impersonar
    (delegación de dominio, para Google Ads)."""
    from google.oauth2 import service_account
    import google.auth.transport.requests as gart
    creds = service_account.Credentials.from_service_account_info(
        json.loads(GOOGLE_SA_JSON), scopes=scopes, subject=subject)
    creds.refresh(gart.Request())
    return creds.token


def pull_google_ads():
    """Gasto/conversiones por país (Google Ads API, directo vía delegación). (rows|None, debug).
    rows con shape de Windsor (account_name/spend/conversion_value) para reemplazarlo."""
    cids = {p: c for p, c in GADS_CIDS.items() if c}
    if not (GOOGLE_SA_JSON and GADS_DEV_TOKEN and GADS_LOGIN_CID and cids):
        return None, "sin config (developer token / login CID / GADS_CID_*)"
    import requests
    try:
        token = _google_token(GADS_SCOPES, subject=GADS_IMPERSONATE or None)
    except Exception as e:  # noqa: BLE001
        return None, f"token/delegación: {str(e)[:120]}"
    headers = {"Authorization": f"Bearer {token}", "developer-token": GADS_DEV_TOKEN,
               "login-customer-id": GADS_LOGIN_CID, "Content-Type": "application/json"}
    query = ("SELECT metrics.cost_micros, metrics.conversions, metrics.conversions_value "
             "FROM customer WHERE segments.date DURING LAST_7_DAYS")
    rows, errs, ok = [], [], 0
    for pais, cid in cids.items():
        try:
            u = f"https://googleads.googleapis.com/{GADS_API_VERSION}/customers/{cid}/googleAds:search"
            r = requests.post(u, headers=headers, json={"query": query}, timeout=60)
            if r.status_code != 200:
                errs.append(f"{pais}(HTTP {r.status_code}: {r.text[:80]})")
                continue
            spend = val = 0.0
            for row in r.json().get("results", []):
                m = row.get("metrics", {})
                spend += _num(m.get("costMicros")) / 1e6
                val += _num(m.get("conversionsValue"))
            rows.append({"account_name": pais, "spend": spend, "conversion_value": val})
            ok += 1
        except Exception as e:  # noqa: BLE001
            errs.append(f"{pais}({str(e)[:60]})")
    if ok == 0:
        return None, "todas fallaron: " + " · ".join(errs)
    return rows, f"ok ({ok}/{len(cids)})" + (" · " + " · ".join(errs) if errs else "")


def pull_ga4_direct():
    """GA4 directo (Data API) por país. Devuelve (rows|None, debug). None → usar Windsor.
    Resiliente: si una propiedad falla, sigue con las demás."""
    props = {p: pid for p, pid in GA4_PROPS.items() if pid}
    if not GOOGLE_SA_JSON:
        return None, "sin GOOGLE_SA_JSON"
    if not props:
        return None, "sin GA4_PROP_* (CL/CO/MX/PE)"
    import requests
    try:
        token = _google_token(GA4_SCOPES)
    except Exception as e:  # noqa: BLE001
        return None, f"token/JSON inválido: {str(e)[:120]}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    out, errs, ok = [], [], 0
    for pais, pid in props.items():
        body = {"dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
                "dimensions": [{"name": "sessionSource"}, {"name": "sessionMedium"}],
                "metrics": [{"name": "sessions"}, {"name": "transactions"}], "limit": 100000}
        try:
            r = requests.post(
                f"https://analyticsdata.googleapis.com/v1beta/properties/{pid}:runReport",
                headers=headers, json=body, timeout=60)
            if r.status_code != 200:
                errs.append(f"{pais}(HTTP {r.status_code}: {r.text[:80]})")
                continue
            for row in r.json().get("rows", []):
                dv = [x.get("value") for x in row.get("dimensionValues", [])]
                mv = [x.get("value") for x in row.get("metricValues", [])]
                out.append({"account_name": pais,
                            "source": dv[0] if dv else "", "medium": dv[1] if len(dv) > 1 else "",
                            "sessions": mv[0] if mv else 0, "transactions": mv[1] if len(mv) > 1 else 0})
            ok += 1
        except Exception as e:  # noqa: BLE001
            errs.append(f"{pais}({str(e)[:60]})")
    if ok == 0:
        return None, "todas fallaron: " + " · ".join(errs)
    dbg = f"ok ({ok}/{len(props)} props)" + (" · errores: " + " · ".join(errs) if errs else "")
    return out, dbg


def pull_search_console():
    """Clics/impresiones por país (Search Console). Devuelve ({pais: {...}}, debug)."""
    sites = {p: s for p, s in SC_SITES.items() if s}
    if not GOOGLE_SA_JSON:
        return {}, "sin GOOGLE_SA_JSON"
    if not sites:
        return {}, "sin SC_SITE_* (CL/CO/MX/PE)"
    import requests
    import urllib.parse as _up
    try:
        token = _google_token(SC_SCOPES)
    except Exception as e:  # noqa: BLE001
        return {}, f"token/JSON: {str(e)[:120]}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # SC tiene ~2-3 días de lag → ventana amplia para asegurar filas
    since = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    until = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    out, errs = {}, []
    for pais, site in sites.items():
        try:
            u = (f"https://searchconsole.googleapis.com/webmasters/v3/sites/"
                 f"{_up.quote(site, safe='')}/searchAnalytics/query")
            r = requests.post(u, headers=headers,
                              json={"startDate": since, "endDate": until}, timeout=60)
            if r.status_code != 200:
                errs.append(f"{pais}(HTTP {r.status_code}: {r.text[:80]})")
                continue
            rows = r.json().get("rows", [])
            if not rows:
                errs.append(f"{pais}(sin filas)")
                continue
            row = rows[0]
            out[pais] = {"clicks": round(_num(row.get("clicks"))),
                         "impressions": round(_num(row.get("impressions"))),
                         "ctr": round(_num(row.get("ctr")) * 100, 2),
                         "position": round(_num(row.get("position")), 1)}
        except Exception as e:  # noqa: BLE001
            errs.append(f"{pais}({str(e)[:60]})")
    dbg = f"ok ({len(out)} sitios)" + (" · " + " · ".join(errs) if errs else "")
    return out, dbg


def build_overview() -> dict:
    """Agrega GA4 + Google Ads por país. Devuelve estructura lista para el dashboard."""
    ga4, ga4_dbg = pull_ga4_direct()  # GA4 directo (gratis) si está configurado
    ga4_src = "directo" if ga4 is not None else "windsor"
    if ga4 is None:
        ga4 = pull_windsor("googleanalytics4", ["account_name", "source", "medium", "sessions", "transactions"])
    gads_direct, gads_dbg = pull_google_ads()  # Google Ads directo (delegación) si está configurado
    gads_src = "directo" if gads_direct is not None else "windsor"
    gads = gads_direct if gads_direct is not None else pull_windsor(
        "google_ads", ["account_name", "spend", "conversions", "conversion_value"])

    if ga4 is None and gads is None:
        return {"fuente": "baseline (placeholder)", "paises": {}, "consolidado": {}}

    fx = _fx_to_usd()  # factor por moneda (monto * factor = USD)
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
            d["moneda"] = MONEDA_VENTAS.get(pais, "USD")
            d["ventas_usd"] = round((d.get("ventas_clp") or 0) * fx.get(d["moneda"], 1.0))
            d["cuadratura"] = {
                "ga4_transacciones": d.get("transacciones", 0),
                "shopify_pedidos": d["pedidos"],
                "ok": d.get("transacciones", 0) <= d["pedidos"],
            }

    # Meta Ads directo (gasto por país) — guarda gasto nativo + moneda + USD
    meta_by, meta_dbg = pull_meta()
    for c, info in meta_by.items():
        d = paises.setdefault(c, {"sesiones": 0, "transacciones": 0, "ad_spend": 0,
                                  "ad_value": 0, "conversion": 0, "roas": 0, "traffic": []})
        d["meta_spend"] = round(info["spend"])
        d["meta_moneda"] = info["currency"]
        d["meta_spend_usd"] = round(info["spend"] * fx.get(info["currency"], 1.0))

    # Klaviyo directo (revenue email/SMS) — multi-cuenta, una key por país
    kla_by, kla_dbg = pull_klaviyo()
    for pais, data in kla_by.items():
        d = paises.get(pais)
        if d is not None:
            ventas = d.get("ventas_clp") or 0
            data["share_pct"] = round(data["email_revenue"] / ventas * 100, 1) if ventas else None
            d["klaviyo"] = data

    # Search Console directo (clics/impresiones/CTR/posición por país)
    sc_by, sc_dbg = pull_search_console()
    for pais, sc in sc_by.items():
        d = paises.get(pais)
        if d is not None:
            d["search_console"] = sc

    consol = {
        "sesiones": sum(d["sesiones"] for d in paises.values()),
        "transacciones": sum(d["transacciones"] for d in paises.values()),
        "ad_spend": sum(d["ad_spend"] for d in paises.values()),
        "ad_value": sum(d["ad_value"] for d in paises.values()),
    }
    consol["conversion"] = round(consol["transacciones"] / consol["sesiones"] * 100, 2) if consol["sesiones"] else 0
    consol["roas"] = round(consol["ad_value"] / consol["ad_spend"], 2) if consol["ad_spend"] else 0
    # Consolidado normalizado a USD (sí se puede sumar): venta total + gasto Meta + MER(Meta)
    consol["ventas_usd"] = sum((d.get("ventas_usd") or 0) for d in paises.values())
    consol["meta_spend_usd"] = sum((d.get("meta_spend_usd") or 0) for d in paises.values())
    consol["mer_meta_usd"] = (round(consol["ventas_usd"] / consol["meta_spend_usd"], 2)
                              if consol["meta_spend_usd"] else 0)
    consol["base_moneda"] = "USD"

    return {"fuente": f"GA4 {ga4_src} (en vivo)", "rango": "últimos 7 días",
            "consolidado": consol, "paises": paises, "_shopify": shop_dbg, "_meta": meta_dbg,
            "_klaviyo": kla_dbg, "_search_console": sc_dbg, "_ga4": ga4_dbg,
            "_google_ads": gads_dbg, "_fx": {k: round(v, 8) for k, v in fx.items()},
            "nota": f"GA4 {ga4_src} + Search Console + Google Ads ({gads_src}). "
                    "Shopify + Meta Ads + Klaviyo directos. Consolidado normalizado a USD."}


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
