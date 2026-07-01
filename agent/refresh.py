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
HIST = DATA_DIR / "history.json"  # serie histórica (un punto por día) para tendencias

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

# Mercado Libre directo (OAuth, gratis) — una cuenta por país (ver meli_oauth.py).
try:
    import meli_oauth
except Exception:  # noqa: BLE001
    meli_oauth = None

# YouTube (Data API v3) — canal orgánico POR PAÍS. API key (público: subs/vistas/videos).
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
YOUTUBE_HANDLES = {
    "Chile": os.environ.get("YOUTUBE_HANDLE_CL", "SleveChileOficial").lstrip("@"),
    "Colombia": os.environ.get("YOUTUBE_HANDLE_CO", "SleveColombiaOficial").lstrip("@"),
    "México": os.environ.get("YOUTUBE_HANDLE_MX", "SleveMexicoOficial").lstrip("@"),
    "Perú": os.environ.get("YOUTUBE_HANDLE_PE", "SlevePeruOficial").lstrip("@"),
}

# Meta Ads directo (Marketing API) — gratis. Token de System User (Business Manager) con ads_read.
META_TOKEN = os.environ.get("META_TOKEN", "").strip()
META_API_VERSION = "v21.0"
# Redes orgánico: los tokens de System User no usan me/accounts → se consultan las
# páginas vía el negocio (owned_pages). Necesita el Business ID + scopes pages/IG en el token.
META_BUSINESS_ID = os.environ.get("META_BUSINESS_ID", "").strip()

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


def pull_shopify(shop, token, since=None, until=None):
    """Ventas de una tienda (Admin API GraphQL, directo). Rango opcional since/until (YYYY-MM-DD)."""
    if not (shop and token):
        return None, "sin token"
    since = since or (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    filtro = f"created_at:>={since}" + (f" created_at:<={until}" if until else "")
    url = f"https://{shop}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    q = ('query($cursor:String){orders(first:250,after:$cursor,query:"%s"){'
         'pageInfo{hasNextPage endCursor} nodes{totalPriceSet{shopMoney{amount}}}}}' % filtro)
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


def pull_meli(since, until):
    """Ventas + publicaciones activas de Mercado Libre por país (cuenta OAuth). {pais: {...}}, debug."""
    if meli_oauth is None:
        return {}, "meli_oauth no disponible"
    out, dbg = {}, []
    for pais in meli_oauth.PAISES:
        acc = meli_oauth.get_account(pais)
        if not acc:
            continue
        token, uid = acc
        moneda = MONEDA_VENTAS.get(pais, "USD")
        ventas = pedidos = 0
        try:
            base = (f"{meli_oauth.API}/orders/search?seller={uid}"
                    f"&order.date_created.from={since}T00:00:00.000-00:00"
                    f"&order.date_created.to={until}T23:59:59.000-00:00&sort=date_desc&limit=50")
            off = 0
            while off < 20000:  # pagina hasta agotar (tope de seguridad ~20k órdenes)
                d = _meli_get(f"{base}&offset={off}", token)
                res = d.get("results", [])
                if not res:
                    break
                for o in res:
                    if o.get("status") == "cancelled":
                        continue
                    ventas += _num(o.get("total_amount"))
                    pedidos += 1
                total = _num((d.get("paging") or {}).get("total"))
                off += 50
                if total and off >= total:
                    break
        except Exception as e:  # noqa: BLE001
            dbg.append(f"{pais} orders: {str(e)[:60]}")
        pubs = None
        try:
            it = _meli_get(f"{meli_oauth.API}/users/{uid}/items/search?status=active&limit=1", token)
            pubs = int(_num((it.get("paging") or {}).get("total")))
        except Exception:  # noqa: BLE001
            pass
        out[pais] = {"ventas": round(ventas), "pedidos": pedidos, "moneda": moneda, "publicaciones": pubs}
    return out, ("ok (" + ", ".join(f"{p}:{v['pedidos']}ped" for p, v in out.items()) + ")" if out
                 else "sin cuentas ML conectadas") + ((" · " + " · ".join(dbg)) if dbg else "")


def _meli_get(url, token):
    """GET a ML con reintentos ante rate limit (429) / errores transitorios (5xx)."""
    import time as _t
    last = None
    for intento in range(4):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as he:
            last = he
            if he.code in (429, 500, 502, 503, 504):
                ra = he.headers.get("Retry-After")
                _t.sleep(float(ra) if (ra and ra.isdigit()) else (1.5 * (intento + 1)))
                continue
            raise
        except Exception as e:  # noqa: BLE001
            last = e
            _t.sleep(1.0 * (intento + 1))
    if last:
        raise last
    return {}


def _meta_get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def _meta_campaigns(act, tok, preset="last_7d"):
    """Campañas (con insights del preset) de una cuenta. Top por gasto."""
    base = f"https://graph.facebook.com/{META_API_VERSION}"
    params = {"fields": f"name,effective_status,insights.date_preset({preset})"
                        "{spend,impressions,clicks,ctr,purchase_roas,actions}",
              "limit": 100, "access_token": tok}
    out = []
    try:
        data = _meta_get(f"{base}/{act}/campaigns?{urllib.parse.urlencode(params)}").get("data", [])
    except Exception:  # noqa: BLE001
        return []
    for c in data:
        ins = (c.get("insights", {}) or {}).get("data", [])
        m = ins[0] if ins else {}
        spend = _num(m.get("spend"))
        roas = _num((m.get("purchase_roas") or [{}])[0].get("value")) if m.get("purchase_roas") else 0
        compras = sum(_num(a.get("value")) for a in (m.get("actions") or []) if "purchase" in (a.get("action_type") or ""))
        out.append({"nombre": c.get("name"), "estado": c.get("effective_status"), "spend": round(spend),
                    "impresiones": int(_num(m.get("impressions"))), "ctr": round(_num(m.get("ctr")), 2),
                    "roas": round(roas, 2), "compras": int(compras)})
    out.sort(key=lambda x: x["spend"], reverse=True)
    return out[:12]


def _meta_creatives(act, tok, preset="last_7d"):
    """Anuncios/creativos (insights del preset) de una cuenta → detecta fatiga (frecuencia alta)."""
    base = f"https://graph.facebook.com/{META_API_VERSION}"
    params = {"fields": f"name,effective_status,insights.date_preset({preset})"
                        "{spend,impressions,ctr,frequency}",
              "limit": 300, "access_token": tok}
    out = []
    try:
        data = _meta_get(f"{base}/{act}/ads?{urllib.parse.urlencode(params)}").get("data", [])
    except Exception:  # noqa: BLE001
        return []
    for a in data:
        ins = (a.get("insights", {}) or {}).get("data", [])
        m = ins[0] if ins else {}
        spend = _num(m.get("spend"))
        if spend <= 0:
            continue
        freq, ctr = _num(m.get("frequency")), _num(m.get("ctr"))
        out.append({"nombre": a.get("name"), "estado": a.get("effective_status"), "spend": round(spend),
                    "ctr": round(ctr, 2), "frecuencia": round(freq, 2),
                    "fatiga": bool(freq >= 3.0 or (freq >= 2.0 and ctr < 1.0))})
    out.sort(key=lambda x: x["spend"], reverse=True)
    return out[:10]


def pull_meta(preset="last_7d"):
    """Gasto de Meta Ads por país + campañas y creativos (Marketing API directa) en un preset.
    Devuelve ({pais: {spend, currency, campaigns, creatives}}, debug). Chile suele estar en USD."""
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
            iu = f"{base}/{a.get('id')}/insights?fields=spend&date_preset={preset}&access_token={tok}"
            with urllib.request.urlopen(iu, timeout=60) as r:
                ins = json.loads(r.read().decode("utf-8")).get("data", [])
            spend = sum(_num(x.get("spend")) for x in ins)
        except Exception:  # noqa: BLE001
            spend = 0
        if spend > 0:
            c = _country(name)
            cur = by_country.setdefault(c, {"spend": 0.0, "currency": currency, "campaigns": [], "creatives": []})
            cur["spend"] += spend
            cur["campaigns"] += _meta_campaigns(a.get("id"), META_TOKEN, preset)
            cur["creatives"] += _meta_creatives(a.get("id"), META_TOKEN, preset)
            n += 1
    for cur in by_country.values():
        cur["campaigns"] = sorted(cur.get("campaigns", []), key=lambda x: x["spend"], reverse=True)[:12]
        cur["creatives"] = sorted(cur.get("creatives", []), key=lambda x: x["spend"], reverse=True)[:10]
    return by_country, f"ok ({n} cuentas con gasto)"


def pull_social():
    """Redes orgánico (Páginas FB + IG) por país, vía system user token + owned_pages del negocio.
    Devuelve ({pais: {...}}, debug)."""
    if not META_TOKEN:
        return {}, "sin META_TOKEN"
    if not META_BUSINESS_ID:
        return {}, "sin META_BUSINESS_ID"
    base = f"https://graph.facebook.com/{META_API_VERSION}"
    tok = urllib.parse.quote(META_TOKEN)
    fields = ("name,fan_count,followers_count,"
              "instagram_business_account%7Busername,followers_count,media_count%7D")
    try:
        u = f"{base}/{META_BUSINESS_ID}/owned_pages?fields={fields}&limit=100&access_token={tok}"
        with urllib.request.urlopen(u, timeout=60) as r:
            pages = json.loads(r.read().decode("utf-8")).get("data", [])
    except urllib.error.HTTPError as he:
        return {}, f"HTTP {he.code}: {he.read().decode('utf-8', 'ignore')[:160]}"
    except Exception as e:  # noqa: BLE001
        return {}, f"error: {e}"
    by_country, n = {}, 0
    for p in pages:
        name = p.get("name") or ""
        if "sleve" not in name.lower():
            continue  # solo páginas SLEVE (omite Candylicious, etc.)
        ig = p.get("instagram_business_account") or {}
        d = by_country.setdefault(_country(name), {"fb_followers": 0, "ig_followers": 0,
                                                    "ig_posts": 0, "ig_username": None, "paginas": 0})
        d["fb_followers"] += int(_num(p.get("followers_count") or p.get("fan_count")))
        d["ig_followers"] += int(_num(ig.get("followers_count")))
        d["ig_posts"] += int(_num(ig.get("media_count")))
        d["ig_username"] = ig.get("username") or d["ig_username"]
        d["paginas"] += 1
        n += 1
    return by_country, f"ok ({n} páginas SLEVE)"


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


def _klaviyo_one(pais, key, dias=7):
    """Revenue atribuido (email/SMS) de UNA cuenta Klaviyo en `dias`. (data|None, debug)."""
    try:
        metric_id = _klaviyo_placed_order_id(key)
    except urllib.error.HTTPError as he:
        return None, f"HTTP {he.code}: {he.read().decode('utf-8', 'ignore')[:120]}"
    except Exception as e:  # noqa: BLE001
        return None, f"metrics: {e}"
    if not metric_id:
        return None, "sin métrica Placed Order"
    since = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%dT00:00:00")
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


def _yt_get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def pull_youtube():
    """Canales de YouTube por país (Data API v3, público): subs/vistas/videos + top. {país: {...}}, debug."""
    if not YOUTUBE_API_KEY:
        return {}, "sin YOUTUBE_API_KEY"
    base = "https://www.googleapis.com/youtube/v3"
    out, dbg = {}, []
    for pais, handle in YOUTUBE_HANDLES.items():
        if not handle:
            continue
        try:
            ch = _yt_get(f"{base}/channels?part=statistics,snippet&forHandle={handle}&key={YOUTUBE_API_KEY}")
            items = ch.get("items", [])
            if not items:
                dbg.append(f"{pais}:@{handle} no encontrado")
                continue
            c0 = items[0]; st = c0.get("statistics", {}); chid = c0.get("id")
            info = {"handle": handle, "nombre": c0.get("snippet", {}).get("title"),
                    "suscriptores": int(_num(st.get("subscriberCount"))),
                    "vistas": int(_num(st.get("viewCount"))),
                    "videos": int(_num(st.get("videoCount"))), "top": []}
            sd = _yt_get(f"{base}/search?part=snippet&channelId={chid}&order=viewCount&type=video&maxResults=5&key={YOUTUBE_API_KEY}")
            vids = [it["id"]["videoId"] for it in sd.get("items", []) if it.get("id", {}).get("videoId")]
            if vids:
                vd = _yt_get(f"{base}/videos?part=statistics,snippet&id={','.join(vids)}&key={YOUTUBE_API_KEY}")
                for v in vd.get("items", []):
                    vs = v.get("statistics", {})
                    info["top"].append({"titulo": v.get("snippet", {}).get("title"),
                                        "vistas": int(_num(vs.get("viewCount"))),
                                        "likes": int(_num(vs.get("likeCount"))),
                                        "comentarios": int(_num(vs.get("commentCount")))})
            out[pais] = info
        except Exception as e:  # noqa: BLE001
            dbg.append(f"{pais}:{str(e)[:50]}")
    subs = sum(v.get("suscriptores", 0) for v in out.values())
    return out, (f"ok ({len(out)} canales, {subs} subs)" + (" · " + " · ".join(dbg) if dbg else "")) if out else ("sin canales · " + " · ".join(dbg))


def _youtube_cached():
    """YouTube (snapshot del canal). Cacheado ~6h (youtube.json)."""
    f = DATA_DIR / "youtube.json"
    ahora = datetime.now(timezone.utc)
    try:
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("data") and (ahora - datetime.fromisoformat(c.get("ts"))) < timedelta(hours=6):
            return c["data"]
    except Exception:  # noqa: BLE001
        pass
    data, _dbg = pull_youtube()
    if data:
        try:
            f.write_text(json.dumps({"ts": ahora.isoformat(), "data": data}, ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        return data
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("data") or {}
    except Exception:  # noqa: BLE001
        return {}


def pull_klaviyo(dias=7):
    """Multi-cuenta: una Private API Key por país, en una ventana de `dias`. ({pais: data}, {pais: debug})."""
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
        data, d = _klaviyo_one(pais, key, dias)
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


def pull_google_ads(during="LAST_7_DAYS"):
    """Gasto/conversiones por país (Google Ads API, directo vía delegación) en un rango GAQL.
    (rows|None, camps_by, debug). `during` = literal DURING (LAST_7_DAYS/LAST_30_DAYS/THIS_MONTH)."""
    cids = {p: c for p, c in GADS_CIDS.items() if c}
    if not (GOOGLE_SA_JSON and GADS_DEV_TOKEN and GADS_LOGIN_CID and cids):
        return None, {}, "sin config (developer token / login CID / GADS_CID_*)"
    import requests
    try:
        token = _google_token(GADS_SCOPES, subject=GADS_IMPERSONATE or None)
    except Exception as e:  # noqa: BLE001
        return None, {}, f"token/delegación: {str(e)[:120]}"
    headers = {"Authorization": f"Bearer {token}", "developer-token": GADS_DEV_TOKEN,
               "login-customer-id": GADS_LOGIN_CID, "Content-Type": "application/json"}
    query = ("SELECT campaign.name, campaign.status, customer.currency_code, metrics.cost_micros, "
             "metrics.conversions, metrics.conversions_value FROM campaign "
             f"WHERE segments.date DURING {during} ORDER BY metrics.cost_micros DESC")
    rows, camps_by, errs, ok = [], {}, [], 0
    for pais, cid in cids.items():
        try:
            u = f"https://googleads.googleapis.com/{GADS_API_VERSION}/customers/{cid}/googleAds:search"
            r = requests.post(u, headers=headers, json={"query": query}, timeout=60)
            if r.status_code != 200:
                errs.append(f"{pais}(HTTP {r.status_code}: {r.text[:80]})")
                continue
            spend = val = 0.0
            currency = MONEDA_VENTAS.get(pais, "USD")
            camps = []
            for row in r.json().get("results", []):
                m = row.get("metrics", {})
                cost = _num(m.get("costMicros")) / 1e6
                cval = _num(m.get("conversionsValue"))
                spend += cost
                val += cval
                currency = (row.get("customer", {}) or {}).get("currencyCode") or currency
                camp = row.get("campaign", {}) or {}
                camps.append({"nombre": camp.get("name"), "estado": camp.get("status"),
                              "spend": round(cost), "conversiones": round(_num(m.get("conversions")), 1),
                              "valor": round(cval), "roas": round(cval / cost, 2) if cost else 0})
            rows.append({"account_name": pais, "spend": spend, "conversion_value": val, "currency": currency})
            camps_by[pais] = sorted(camps, key=lambda x: x["spend"], reverse=True)[:12]
            ok += 1
        except Exception as e:  # noqa: BLE001
            errs.append(f"{pais}({str(e)[:60]})")
    if ok == 0:
        return None, {}, "todas fallaron: " + " · ".join(errs)
    return rows, camps_by, f"ok ({ok}/{len(cids)})" + (" · " + " · ".join(errs) if errs else "")


def pull_ga4_direct(since="7daysAgo", until="today"):
    """GA4 directo (Data API) por país en un rango. Devuelve (rows|None, debug). None → usar Windsor.
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
        body = {"dateRanges": [{"startDate": since, "endDate": until}],
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


def pull_search_console(dias=10):
    """Clics/impresiones por país (Search Console) en una ventana de `dias`. ({pais: {...}}, debug)."""
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
    # SC tiene ~2-3 días de lag → until = ayer; ventana = `dias` hacia atrás
    since = (datetime.now(timezone.utc) - timedelta(days=max(dias, 3))).strftime("%Y-%m-%d")
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


def _hoy_local():
    """Fecha 'hoy' en hora de Chile (mercado principal) para los cortes de período.
    Evita que a fin de mes UTC (ya día siguiente) 'este mes' salte antes que en Chile."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Santiago")).date()
    except Exception:  # noqa: BLE001 — fallback UTC-4 (Chile estándar)
        return (datetime.now(timezone.utc) - timedelta(hours=4)).date()


def _periodo_params(periodo):
    """Rangos por período para cada fuente. GA4 acepta fechas relativas/ISO; Meta usa preset;
    Google Ads usa literal DURING; Klaviyo/SC usan días hacia atrás; Shopify usa fechas ISO.
    Los cortes se anclan a hora de Chile (_hoy_local)."""
    hoy = _hoy_local()
    if periodo == "30d":
        return {"ga4": ("30daysAgo", "today"), "meta": "last_30d", "gads": "LAST_30_DAYS",
                "kla": 30, "sc": 33, "shop": ((hoy - timedelta(days=30)).isoformat(), hoy.isoformat()),
                "label": "últimos 30 días"}
    if periodo == "mes":
        d1 = hoy.replace(day=1)
        nd = (hoy - d1).days + 1
        return {"ga4": (d1.isoformat(), "today"), "meta": "this_month", "gads": "THIS_MONTH",
                "kla": nd, "sc": nd + 3, "shop": (d1.isoformat(), hoy.isoformat()),
                "label": "este mes"}
    if periodo == "mes_anterior":
        _MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        fin = hoy.replace(day=1) - timedelta(days=1)   # último día del mes anterior
        d1 = fin.replace(day=1)                         # primer día del mes anterior
        nd = (hoy - d1).days + 1                        # ventana hasta hoy (para Klaviyo/SC, aprox)
        return {"ga4": (d1.isoformat(), fin.isoformat()), "meta": "last_month", "gads": "LAST_MONTH",
                "kla": nd, "sc": nd + 3, "shop": (d1.isoformat(), fin.isoformat()),
                "label": f"{_MESES[d1.month]} {d1.year}"}
    return {"ga4": ("7daysAgo", "today"), "meta": "last_7d", "gads": "LAST_7_DAYS",
            "kla": 7, "sc": 10, "shop": ((hoy - timedelta(days=7)).isoformat(), hoy.isoformat()),
            "label": "últimos 7 días"}


def build_overview(periodo="7d") -> dict:
    """Agrega TODAS las fuentes por país en un período. Estructura uniforme para el dashboard."""
    P = _periodo_params(periodo)
    ga4, ga4_dbg = pull_ga4_direct(*P["ga4"])  # GA4 directo (gratis) si está configurado
    ga4_src = "directo" if ga4 is not None else "windsor"
    if ga4 is None:
        ga4 = pull_windsor("googleanalytics4", ["account_name", "source", "medium", "sessions", "transactions"])
    gads_direct, gads_camps, gads_dbg = pull_google_ads(P["gads"])  # Google Ads directo (delegación)
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

    # Google Ads → gasto y valor por país (+ moneda de la cuenta de Ads)
    for row in (gads or []):
        pais = _country(row.get("account_name", ""))
        paises[pais]["ad_spend"] += _num(row.get("spend"))
        paises[pais]["ad_value"] += _num(row.get("conversion_value"))
        if row.get("currency"):
            paises[pais]["gads_moneda"] = row["currency"]
    for pais, camps in (gads_camps or {}).items():
        if pais in paises:
            paises[pais]["gads_campaigns"] = camps

    # Métricas derivadas + top de tráfico por país
    for p, d in paises.items():
        ses, tr = d["sesiones"], d["transacciones"]
        # Conversión base con GA4 (se sobrescribe abajo con pedidos Shopify, que cuadran mejor)
        d["conversion_ga4"] = round(tr / ses * 100, 2) if ses else 0
        d["conversion"] = d["conversion_ga4"]
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
        res, dbg = pull_shopify(domain, tok, *P["shop"])
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
            # Conversión real = pedidos Shopify / sesiones GA4 (cuadra con Shopify; GA4 sub-cuenta)
            if d.get("sesiones"):
                d["conversion"] = round(d["pedidos"] / d["sesiones"] * 100, 2)
            d["cuadratura"] = {
                "ga4_transacciones": d.get("transacciones", 0),
                "shopify_pedidos": d["pedidos"],
                "gap_tracking": d["pedidos"] - d.get("transacciones", 0),
                "ok": d.get("transacciones", 0) <= d["pedidos"],
            }

    # Meta Ads directo (gasto por país) — guarda gasto nativo + moneda + USD
    meta_by, meta_dbg = pull_meta(P["meta"])
    for c, info in meta_by.items():
        d = paises.setdefault(c, {"sesiones": 0, "transacciones": 0, "ad_spend": 0,
                                  "ad_value": 0, "conversion": 0, "roas": 0, "traffic": []})
        d["meta_spend"] = round(info["spend"])
        d["meta_moneda"] = info["currency"]
        d["meta_spend_usd"] = round(info["spend"] * fx.get(info["currency"], 1.0))
        d["meta_campaigns"] = info.get("campaigns", [])
        d["meta_creatives"] = info.get("creatives", [])

    # Klaviyo directo (revenue email/SMS) — multi-cuenta, una key por país
    kla_by, kla_dbg = pull_klaviyo(P["kla"])
    for pais, data in kla_by.items():
        d = paises.get(pais)
        if d is not None:
            ventas = d.get("ventas_clp") or 0
            data["share_pct"] = round(data["email_revenue"] / ventas * 100, 1) if ventas else None
            d["klaviyo"] = data

    # Mercado Libre directo (ventas + publicaciones por país) — marketplace
    meli_by, meli_dbg = pull_meli(*P["shop"])
    for pais, m in meli_by.items():
        d = paises.get(pais)
        if d is not None:
            d["meli"] = m
            d["meli_ventas_usd"] = round((m.get("ventas") or 0) * fx.get(m.get("moneda", "USD"), 1.0))

    # Search Console directo (clics/impresiones/CTR/posición por país)
    sc_by, sc_dbg = pull_search_console(P["sc"])
    for pais, sc in sc_by.items():
        d = paises.get(pais)
        if d is not None:
            d["search_console"] = sc

    # Redes sociales orgánico (Páginas FB + IG) por país
    soc_by, soc_dbg = pull_social()
    for pais, s in soc_by.items():
        d = paises.get(pais)
        if d is not None:
            d["social"] = s

    # P&L / blended en USD por país: gasto Ads (Meta + Google) → USD, MER, contribución
    for pais, d in paises.items():
        gads_ccy = d.get("gads_moneda") or MONEDA_VENTAS.get(pais, "USD")
        d["gads_spend_usd"] = round((d.get("ad_spend") or 0) * fx.get(gads_ccy, 1.0))
        d["ad_spend_usd"] = round((d.get("meta_spend_usd") or 0) + d["gads_spend_usd"])
        vu = d.get("ventas_usd") or 0
        d["mer_usd"] = round(vu / d["ad_spend_usd"], 2) if d["ad_spend_usd"] else 0
        d["contrib_usd"] = round(vu - d["ad_spend_usd"])  # margen tras ads (falta COGS)

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
    consol["ad_spend_usd"] = sum((d.get("ad_spend_usd") or 0) for d in paises.values())
    consol["contrib_usd"] = sum((d.get("contrib_usd") or 0) for d in paises.values())
    consol["pedidos"] = sum((d.get("pedidos") or 0) for d in paises.values())
    consol["mer_meta_usd"] = (round(consol["ventas_usd"] / consol["meta_spend_usd"], 2)
                              if consol["meta_spend_usd"] else 0)
    consol["mer_usd"] = (round(consol["ventas_usd"] / consol["ad_spend_usd"], 2)
                         if consol["ad_spend_usd"] else 0)
    consol["aov_usd"] = round(consol["ventas_usd"] / consol["pedidos"]) if consol["pedidos"] else 0
    consol["cpa_usd"] = round(consol["ad_spend_usd"] / consol["pedidos"]) if consol["pedidos"] else 0
    consol["base_moneda"] = "USD"
    # Desglose por canal: sitio propio (Shopify) vs Mercado Libre vs total
    consol["ventas_sitio_usd"] = consol["ventas_usd"]  # alias claro (Shopify)
    consol["pedidos_sitio"] = consol["pedidos"]
    consol["ventas_meli_usd"] = sum((d.get("meli_ventas_usd") or 0) for d in paises.values())
    consol["pedidos_meli"] = sum(((d.get("meli") or {}).get("pedidos") or 0) for d in paises.values())
    consol["publicaciones_meli"] = sum(((d.get("meli") or {}).get("publicaciones") or 0) for d in paises.values())
    consol["ventas_total_usd"] = consol["ventas_sitio_usd"] + consol["ventas_meli_usd"]
    consol["pedidos_total"] = consol["pedidos_sitio"] + consol["pedidos_meli"]
    consol["aov_total_usd"] = round(consol["ventas_total_usd"] / consol["pedidos_total"]) if consol["pedidos_total"] else 0
    consol["mer_total_usd"] = (round(consol["ventas_total_usd"] / consol["ad_spend_usd"], 2)
                               if consol["ad_spend_usd"] else 0)

    return {"fuente": f"GA4 {ga4_src} (en vivo)", "rango": P["label"], "periodo": periodo,
            "consolidado": consol, "paises": paises, "_shopify": shop_dbg, "_meta": meta_dbg,
            "_klaviyo": kla_dbg, "_search_console": sc_dbg, "_ga4": ga4_dbg, "_meli": meli_dbg,
            "_google_ads": gads_dbg, "_social": soc_dbg, "_fx": {k: round(v, 8) for k, v in fx.items()},
            "nota": f"GA4 {ga4_src} + Search Console + Google Ads ({gads_src}). "
                    "Shopify + Meta Ads + Klaviyo directos. Consolidado normalizado a USD."}


def _update_history(overview):
    """Upsert un punto diario en history.json (volumen) y devuelve los últimos 30.
    Cada punto = ventana 7d móvil de ese día → sirve de indicador de tendencia."""
    try:
        hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else []
    except Exception:  # noqa: BLE001
        hist = []
    c = (overview.get("consolidado") or {})
    if c.get("ventas_usd"):
        hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        punto = {"fecha": hoy, "ventas_usd": c.get("ventas_usd"), "pedidos": c.get("pedidos"),
                 "sesiones": c.get("sesiones"), "ad_spend_usd": c.get("ad_spend_usd"),
                 "contrib_usd": c.get("contrib_usd"), "mer_usd": c.get("mer_usd"),
                 "conversion": c.get("conversion")}
        hist = [h for h in hist if h.get("fecha") != hoy] + [punto]
        hist = hist[-90:]
        try:
            HIST.write_text(json.dumps(hist, ensure_ascii=False), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            _log(f"history write err: {e}")
    return hist[-30:]


def _growth(now, prev):
    return round((now - prev) / prev * 100, 1) if prev else None


def _ga4_totals(since, until):
    """Sesiones + transacciones por país en un rango (GA4 Data API). {país: {...}}."""
    props = {p: pid for p, pid in GA4_PROPS.items() if pid}
    if not (GOOGLE_SA_JSON and props):
        return {}
    import requests
    try:
        token = _google_token(GA4_SCOPES)
    except Exception:  # noqa: BLE001
        return {}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    out = {}
    for pais, pid in props.items():
        try:
            body = {"dateRanges": [{"startDate": since, "endDate": until}],
                    "metrics": [{"name": "sessions"}, {"name": "transactions"}]}
            r = requests.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{pid}:runReport",
                              headers=headers, json=body, timeout=60)
            if r.status_code != 200:
                continue
            rows = r.json().get("rows", [])
            if rows:
                mv = [x.get("value") for x in rows[0].get("metricValues", [])]
                out[pais] = {"sesiones": int(_num(mv[0] if mv else 0)),
                             "transacciones": int(_num(mv[1] if len(mv) > 1 else 0))}
        except Exception:  # noqa: BLE001
            continue
    return out


def build_yoy(fx):
    """Comparativo: 30d actual vs mismos 30d del año anterior. Venta (Shopify→USD) + sesiones (GA4)."""
    try:
        hoy = datetime.now(timezone.utc).date()
        n_since, n_until = (hoy - timedelta(days=30)).isoformat(), hoy.isoformat()
        p_since, p_until = (hoy - timedelta(days=395)).isoformat(), (hoy - timedelta(days=365)).isoformat()
        ga_now, ga_prev = _ga4_totals(n_since, n_until), _ga4_totals(p_since, p_until)
        rev_now, rev_prev = {}, {}
        for pais, domain in shopify_oauth.STORES:
            tok = shopify_oauth.get_token(domain)
            if not tok:
                continue
            rn, _ = pull_shopify(domain, tok, n_since, n_until)
            rp, _ = pull_shopify(domain, tok, p_since, p_until)
            if rn:
                rev_now[pais] = rev_now.get(pais, 0) + rn["ventas"]
            if rp:
                rev_prev[pais] = rev_prev.get(pais, 0) + rp["ventas"]
        paises = {}
        for pais in PAISES:
            f = fx.get(MONEDA_VENTAS.get(pais, "USD"), _FX_FALLBACK.get(MONEDA_VENTAS.get(pais, "USD"), 1.0))
            rn_usd, rp_usd = round((rev_now.get(pais) or 0) * f), round((rev_prev.get(pais) or 0) * f)
            g, gp = ga_now.get(pais, {}), ga_prev.get(pais, {})
            paises[pais] = {"rev_now_usd": rn_usd, "rev_prev_usd": rp_usd, "rev_growth": _growth(rn_usd, rp_usd),
                            "ses_now": g.get("sesiones", 0), "ses_prev": gp.get("sesiones", 0),
                            "ses_growth": _growth(g.get("sesiones", 0), gp.get("sesiones", 0))}
        cn = sum(p["rev_now_usd"] for p in paises.values())
        cp = sum(p["rev_prev_usd"] for p in paises.values())
        sn = sum(p["ses_now"] for p in paises.values())
        sp = sum(p["ses_prev"] for p in paises.values())
        return {"periodo": "30d", "rango_actual": f"{n_since} … {n_until}", "rango_prev": f"{p_since} … {p_until}",
                "paises": paises, "consolidado": {"rev_now_usd": cn, "rev_prev_usd": cp, "rev_growth": _growth(cn, cp),
                                                  "ses_now": sn, "ses_prev": sp, "ses_growth": _growth(sn, sp)}}
    except Exception as e:  # noqa: BLE001
        _log(f"yoy error: {e}")
        return {}


def _yoy_cached(fx):
    """YoY pesado → se calcula 1 vez al día y se cachea (yoy.json en el volumen)."""
    f = DATA_DIR / "yoy.json"
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("fecha") == hoy and c.get("data"):
            return c["data"]
    except Exception:  # noqa: BLE001
        pass
    data = build_yoy(fx)
    if data:
        try:
            f.write_text(json.dumps({"fecha": hoy, "data": data}, ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return data


def build_rango(fx, since, until):
    """Agregado por país en un rango [since, until]: venta+pedidos (Shopify), sesiones+conv (GA4)."""
    try:
        ga = _ga4_totals(since, until)
        rev, ped = {}, {}
        for pais, domain in shopify_oauth.STORES:
            tok = shopify_oauth.get_token(domain)
            if not tok:
                continue
            r, _ = pull_shopify(domain, tok, since, until)
            if r:
                rev[pais] = rev.get(pais, 0) + r["ventas"]
                ped[pais] = ped.get(pais, 0) + r["pedidos"]
        paises, tot_usd = {}, 0
        for pais in PAISES:
            moneda = MONEDA_VENTAS.get(pais, "USD")
            f = fx.get(moneda, _FX_FALLBACK.get(moneda, 1.0))
            ventas = rev.get(pais, 0)
            pedidos = ped.get(pais, 0)
            g = ga.get(pais, {})
            ses, trans = g.get("sesiones", 0), g.get("transacciones", 0)
            ventas_usd = round(ventas * f)
            tot_usd += ventas_usd
            paises[pais] = {"ventas": ventas, "ventas_usd": ventas_usd, "moneda": moneda,
                            "pedidos": pedidos, "sesiones": ses, "transacciones": trans,
                            # conversión = pedidos Shopify / sesiones GA4 (cuadra con Shopify)
                            "conversion": round(pedidos / ses * 100, 2) if ses else 0,
                            "aov": round(ventas / pedidos) if pedidos else 0,
                            "aov_usd": round(ventas_usd / pedidos) if pedidos else 0}
        ped_tot = sum(p["pedidos"] for p in paises.values())
        ses_tot = sum(p["sesiones"] for p in paises.values())
        return {"rango": f"{since} … {until}", "paises": paises,
                "consolidado": {"ventas_usd": tot_usd, "pedidos": ped_tot, "sesiones": ses_tot,
                                "aov_usd": round(tot_usd / ped_tot) if ped_tot else 0}}
    except Exception as e:  # noqa: BLE001
        _log(f"build_rango error: {e}")
        return {}


def _rango_cached(nombre, fx, since, until):
    """Cachea 1×día un agregado de rango (pesado: Shopify+GA4). Archivo {nombre}.json."""
    f = DATA_DIR / f"{nombre}.json"
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("fecha") == hoy and c.get("data"):
            return c["data"]
    except Exception:  # noqa: BLE001
        pass
    data = build_rango(fx, since, until)
    if data:
        try:
            f.write_text(json.dumps({"fecha": hoy, "data": data}, ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return data


def _p30_cached(fx):
    """Últimos 30 días, cacheado 1×día."""
    hoy = datetime.now(timezone.utc).date()
    return _rango_cached("p30", fx, (hoy - timedelta(days=30)).isoformat(), hoy.isoformat())


def _mes_cached(fx):
    """Mes en curso (del día 1 a hoy), cacheado 1×día."""
    hoy = datetime.now(timezone.utc).date()
    return _rango_cached("mes", fx, hoy.replace(day=1).isoformat(), hoy.isoformat())


def _shopify_catalog(shop, token):
    """Completitud de productos de una tienda: total, sin imagen, sin descripción, no activos."""
    if not (shop and token):
        return None
    url = f"https://{shop}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    q = ('query($c:String){products(first:250,after:$c){pageInfo{hasNextPage endCursor} '
         'nodes{status featuredImage{id} descriptionHtml}}}')
    tot = img = desc = inact = 0
    cursor = None
    for _ in range(8):  # hasta ~2000 productos
        body = json.dumps({"query": q, "variables": {"c": cursor}}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json", "X-Shopify-Access-Token": token})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            break
        prods = d.get("data", {}).get("products", {})
        for n in prods.get("nodes", []):
            tot += 1
            if not n.get("featuredImage"):
                img += 1
            if not (n.get("descriptionHtml") or "").strip():
                desc += 1
            if n.get("status") != "ACTIVE":
                inact += 1
        pg = prods.get("pageInfo", {})
        if pg.get("hasNextPage"):
            cursor = pg.get("endCursor")
        else:
            break
    return {"total": tot, "sin_imagen": img, "sin_descripcion": desc, "no_activos": inact}


def _top_products(shop, token, since):
    """Productos más vendidos de una tienda (line items de órdenes del rango). {título: {unidades, ventas}}."""
    if not (shop and token):
        return {}
    url = f"https://{shop}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    # orders(50) × lineItems(10) = bajo costo de query (evita THROTTLED de Shopify)
    q = ('query($cursor:String){orders(first:50,after:$cursor,query:"created_at:>=%s"){'
         'pageInfo{hasNextPage endCursor} nodes{lineItems(first:10){nodes{'
         'title quantity originalTotalSet{shopMoney{amount}}}}}}}' % since)
    agg, cursor = {}, None
    for _ in range(40):  # hasta ~2000 órdenes
        body = json.dumps({"query": q, "variables": {"cursor": cursor}}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json", "X-Shopify-Access-Token": token})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            break
        orders = d.get("data", {}).get("orders", {})
        for o in orders.get("nodes", []):
            for li in o.get("lineItems", {}).get("nodes", []):
                t = (li.get("title") or "—").strip()
                a = agg.setdefault(t, {"unidades": 0, "ventas": 0.0})
                a["unidades"] += int(_num(li.get("quantity")))
                a["ventas"] += _num(li.get("originalTotalSet", {}).get("shopMoney", {}).get("amount"))
        pg = orders.get("pageInfo", {})
        if pg.get("hasNextPage"):
            cursor = pg.get("endCursor")
        else:
            break
    return agg


def _top_products_cached(fx):
    """Productos top 7d por país (Shopify line items). Cacheado ~6h (productos.json)."""
    f = DATA_DIR / "productos.json"
    ahora = datetime.now(timezone.utc)
    try:
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("data") and (ahora - datetime.fromisoformat(c.get("ts"))) < timedelta(hours=6):
            return c["data"]
    except Exception:  # noqa: BLE001
        pass
    since = (ahora - timedelta(days=7)).strftime("%Y-%m-%d")
    out = {}
    for pais, domain in shopify_oauth.STORES:
        tok = shopify_oauth.get_token(domain)
        if not tok:
            continue
        agg = _top_products(domain, tok, since)
        if not agg:
            continue
        dest = out.setdefault(pais, {})
        for t, v in agg.items():  # cada tienda suma a su país (ej. reseller CL → Chile)
            d = dest.setdefault(t, {"unidades": 0, "ventas": 0.0})
            d["unidades"] += v["unidades"]
            d["ventas"] += v["ventas"]
    # rankea top 12 por venta y agrega ventas_usd
    res = {}
    for pais, prods in out.items():
        moneda = MONEDA_VENTAS.get(pais, "USD")
        fac = fx.get(moneda, _FX_FALLBACK.get(moneda, 1.0))
        top = sorted(prods.items(), key=lambda kv: kv[1]["ventas"], reverse=True)[:12]
        res[pais] = [{"nombre": t, "unidades": v["unidades"], "ventas": round(v["ventas"]),
                      "ventas_usd": round(v["ventas"] * fac), "moneda": moneda} for t, v in top]
    if res:
        try:
            f.write_text(json.dumps({"ts": ahora.isoformat(), "data": res}, ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        _log(f"_productos: ok ({sum(len(v) for v in res.values())} items, {len(res)} países)")
    return res


# Google Trends — búsquedas en alza por país vía el feed RSS oficial (gratis, sin browser).
# Es la vía limpia: no requiere Chromium headless en el container (pesado y frágil); urllib + XML.
_TRENDS_GEO = {"Chile": "CL", "Colombia": "CO", "México": "MX", "Perú": "PE"}
# Términos relevantes para SLEVE (electrónica/audio) → se resaltan como oportunidad.
_TRENDS_KW = ("audifon", "auricular", "parlante", "bluetooth", "speaker", "celular", "smartphone",
              "iphone", "samsung", "xiaomi", "cargador", "smartwatch", "reloj intelig", "audio",
              "sonido", "consola", "playstation", "xbox", "nintendo", "tablet", "notebook",
              "laptop", "cámara", "drone", "powerbank", "carga", "jbl", "sony", "anker")


def pull_trends():
    """Top búsquedas en alza (24h) por país desde Google Trends RSS. Marca las afines a SLEVE."""
    import xml.etree.ElementTree as ET
    out = {}
    for pais, geo in _TRENDS_GEO.items():
        url = f"https://trends.google.com/trending/rss?geo={geo}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (SLEVE-Agent)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                root = ET.fromstring(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        items = []
        for it in root.iter("item"):
            t = (it.findtext("title") or "").strip()
            if not t:
                continue
            traf = ""
            for ch in it:
                if ch.tag.endswith("approx_traffic"):
                    traf = (ch.text or "").strip()
            rel = any(k in t.lower() for k in _TRENDS_KW)
            items.append({"termino": t, "trafico": traf, "relevante": rel})
            if len(items) >= 20:
                break
        if items:
            out[pais] = items
    if out:
        _log(f"_trends: ok ({sum(len(v) for v in out.values())} términos, {len(out)} países)")
    return out


def _trends_cached():
    """Tendencias por país. Cacheado ~3h (trends.json) para no golpear el feed en cada refresh."""
    f = DATA_DIR / "trends.json"
    ahora = datetime.now(timezone.utc)
    try:
        c = json.loads(f.read_text(encoding="utf-8"))
        ts = datetime.fromisoformat(c.get("ts"))
        if c.get("data") and (ahora - ts) < timedelta(hours=3):
            return c["data"]
    except Exception:  # noqa: BLE001
        pass
    data = pull_trends()
    if data:
        try:
            f.write_text(json.dumps({"ts": ahora.isoformat(), "data": data}, ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        return data
    # si falló, devuelve lo último cacheado aunque esté algo viejo
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("data") or {}
    except Exception:  # noqa: BLE001
        return {}


def _catalog_cached():
    """Completitud de catálogo Shopify por país. Cacheado 1×día (catalog.json)."""
    f = DATA_DIR / "catalog.json"
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("fecha") == hoy and c.get("data"):
            return c["data"]
    except Exception:  # noqa: BLE001
        pass
    out = {}
    for pais, domain in shopify_oauth.STORES:
        tok = shopify_oauth.get_token(domain)
        if not tok:
            continue
        c = _shopify_catalog(domain, tok)
        if c:
            d = out.setdefault(pais, {"total": 0, "sin_imagen": 0, "sin_descripcion": 0, "no_activos": 0})
            for k in c:
                d[k] += c[k]
    if out:
        try:
            f.write_text(json.dumps({"fecha": hoy, "data": out}, ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return out


def _slim_periodo(o):
    """Solo lo que el dashboard consume por período (estructura uniforme; sin debug)."""
    return {k: o.get(k) for k in ("consolidado", "paises", "rango", "periodo")} if o else {}


def _overview_periodo_cached(periodo):
    """Overview COMPLETO de un período (30d/mes) → pesado, se calcula 1×día y se cachea."""
    f = DATA_DIR / f"ov_{periodo}.json"
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("fecha") == hoy and c.get("data"):
            return c["data"]
    except Exception:  # noqa: BLE001
        pass
    data = _slim_periodo(build_overview(periodo))
    if data.get("paises"):
        try:
            f.write_text(json.dumps({"fecha": hoy, "data": data}, ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return data


def _invalidar_caches_diarios() -> None:
    """Borra los cachés 1×día para forzar recálculo (ej. tras conectar una fuente nueva)."""
    for name in ("ov_30d.json", "ov_mes.json", "ov_mes_anterior.json", "yoy.json", "catalog.json", "productos.json"):
        try:
            (DATA_DIR / name).unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass


def refresh(full: bool = False) -> None:
    if full:  # recálculo completo: invalida cachés diarios (30d/mes/yoy/catálogo/productos)
        _invalidar_caches_diarios()
    ov = build_overview("7d")  # principal (cada 2h) — top-level = 7d (retrocompatible)
    overview = {
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "cadencia": "cada 2h",
        **ov,
    }
    overview["historia"] = _update_history(overview)
    overview["yoy"] = _yoy_cached(overview.get("_fx") or {})
    overview["productos"] = _top_products_cached(overview.get("_fx") or {})
    overview["catalogo"] = _catalog_cached()
    overview["tendencias"] = _trends_cached()
    overview["youtube"] = _youtube_cached()
    # Datasets por período (MISMA estructura completa) → filtro global uniforme del dashboard
    overview["periodos"] = {
        "7d": _slim_periodo(ov),
        "30d": _overview_periodo_cached("30d"),
        "mes": _overview_periodo_cached("mes"),
        "mes_anterior": _overview_periodo_cached("mes_anterior"),
    }
    OUT.write_text(json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"overview.json actualizado ({overview.get('fuente')}) → {OUT}")


if __name__ == "__main__":
    refresh()
    print(OUT.read_text(encoding="utf-8")[:600])
