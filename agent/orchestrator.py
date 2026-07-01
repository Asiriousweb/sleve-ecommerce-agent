#!/usr/bin/env python3
"""
Orquestador E-commerce — la cabeza del bot de Telegram.
Lee la MISMA data del dashboard (overview.json en el volumen) → responde comandos
en vivo SIN costo de API (headless), y `ask()` responde en lenguaje natural con la
Claude API (requiere ANTHROPIC_API_KEY; modelo configurable con TG_MODEL).

Regla #1: solo lectura. Cualquier acción que modifique algo se propone y espera
autorización — nunca se ejecuta desde aquí sin OK.
"""
import json
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
OVERVIEW = DATA_DIR / "overview.json"
PAISES = ["Chile", "Colombia", "México", "Perú"]
MODEL = os.environ.get("TG_MODEL", "claude-opus-4-8")  # poné claude-haiku-4-5 para minimizar costo

HELP = (
    "🔵 SLEVE E-commerce — comandos\n"
    "/resumen — venta total (sitio + Mercado Libre), ads y MER\n"
    "/ml — Mercado Libre por país\n"
    "/ads — gasto y campañas (Meta/Google)\n"
    "/acciones — urgencias detectadas\n"
    "/pais <chile|colombia|mexico|peru>\n"
    "/estado — conexiones\n"
    "/ping — test de vida\n\n"
    "También podés escribirme en lenguaje natural (ej: \"¿cómo va Mercado Libre Chile este mes?\")."
)


def _ov() -> dict:
    try:
        return json.loads(OVERVIEW.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _usd(n) -> str:
    try:
        return "US$" + format(round(n), ",d")
    except Exception:  # noqa: BLE001
        return "US$0"


def _ds(ov: dict, periodo: str = "7d") -> dict:
    P = ov.get("periodos") or {}
    if periodo in P and (P[periodo] or {}).get("paises"):
        return P[periodo]
    return {"consolidado": ov.get("consolidado") or {}, "paises": ov.get("paises") or {}, "rango": ov.get("rango")}


def _norm_pais(s: str):
    s = (s or "").strip().lower()
    for p in PAISES:
        if p.lower().replace("é", "e").replace("ú", "u") in s.replace("é", "e").replace("ú", "u"):
            return p
    return None


def resumen(periodo: str = "7d") -> str:
    ov = _ov(); ds = _ds(ov, periodo); c = ds.get("consolidado") or {}
    if not c:
        return "Aún no hay datos (el robot está levantando el overview). Probá en un minuto."
    sitio = c.get("ventas_sitio_usd", c.get("ventas_usd", 0))
    meli = c.get("ventas_meli_usd", 0)
    total = c.get("ventas_total_usd", sitio + meli)
    return (f"🔵 Resumen · {ds.get('rango') or periodo}\n"
            f"Venta TOTAL: {_usd(total)} ({c.get('pedidos_total', c.get('pedidos', 0))} pedidos)\n"
            f"  • Sitio propio: {_usd(sitio)} ({c.get('pedidos_sitio', c.get('pedidos', 0))} ped)\n"
            f"  • Mercado Libre: {_usd(meli)} ({c.get('pedidos_meli', 0)} ped · {c.get('publicaciones_meli', 0)} pubs)\n"
            f"Gasto Ads: {_usd(c.get('ad_spend_usd'))} (Meta {_usd(c.get('meta_spend_usd'))})\n"
            f"MER blended: {c.get('mer_total_usd', c.get('mer_usd', 0))}x · Contribución: {_usd(total - (c.get('ad_spend_usd') or 0))}")


def mercadolibre(periodo: str = "7d") -> str:
    ov = _ov(); ds = _ds(ov, periodo); ps = ds.get("paises") or {}
    out = [f"🟡 Mercado Libre · {ds.get('rango') or periodo}"]
    hay = False
    for pais in PAISES:
        m = (ps.get(pais) or {}).get("meli")
        if m:
            hay = True
            out.append(f"{pais}: {m.get('ventas')} {m.get('moneda')} ({_usd((ps[pais] or {}).get('meli_ventas_usd'))}) · "
                       f"{m.get('pedidos')} ped · {m.get('publicaciones')} pubs")
    if not hay:
        out.append("Sin cuentas ML conectadas (o sin ventas). Conectar en /meli.")
    return "\n".join(out)


def ads(periodo: str = "7d") -> str:
    ov = _ov(); ds = _ds(ov, periodo); ps = ds.get("paises") or {}
    out = [f"📈 Ads · {ds.get('rango') or periodo}"]
    for pais in PAISES:
        d = ps.get(pais) or {}
        if d.get("meta_spend") is None and not d.get("ad_spend"):
            continue
        out.append(f"{pais}: Meta {d.get('meta_spend', '—')} {d.get('meta_moneda', '')} · "
                   f"Google {d.get('ad_spend', '—')} {d.get('gads_moneda', '')} · MER {d.get('mer_usd', 0)}x")
        fat = [cr.get("nombre") for cr in (d.get("meta_creatives") or []) if cr.get("fatiga")]
        if fat:
            out.append(f"  ⚠️ fatiga: {', '.join(fat[:3])}")
    return "\n".join(out) if len(out) > 1 else "Sin datos de ads."


def acciones(periodo: str = "7d") -> str:
    ov = _ov(); ds = _ds(ov, periodo); ps = ds.get("paises") or {}; cat = ov.get("catalogo") or {}
    A = []
    for pais in PAISES:
        d = ps.get(pais) or {}
        q = d.get("cuadratura")
        if q and not q.get("ok"):
            A.append(f"🔴 {pais}: descuadre GA4 {q.get('ga4_transacciones')} > Shopify {q.get('shopify_pedidos')}.")
        if (d.get("sesiones") or 0) > 200 and (d.get("pedidos") or 0) == 0:
            A.append(f"🔴 {pais}: {d.get('sesiones')} sesiones y 0 ventas — activar o pausar.")
        if 0 < (d.get("mer_usd") or 0) < 2:
            A.append(f"🟡 {pais}: MER bajo ({d.get('mer_usd')}x).")
    for pais, cc in cat.items():
        if (cc.get("sin_descripcion") or 0) > 0:
            A.append(f"🟡 {pais}: {cc.get('sin_descripcion')} fichas sin descripción.")
        if cc.get("total") and (cc.get("no_activos", 0) / cc["total"]) > 0.5:
            A.append(f"🔵 {pais}: {cc.get('no_activos')}/{cc.get('total')} productos no activos.")
    return "🚨 Acciones / urgencias:\n" + ("\n".join(f"• {a}" for a in A) if A else "Sin urgencias. 🟢")


def pais(nombre: str, periodo: str = "7d") -> str:
    p = _norm_pais(nombre)
    if not p:
        return "País no reconocido. Usá: /pais chile | colombia | mexico | peru"
    ov = _ov(); ds = _ds(ov, periodo); d = (ds.get("paises") or {}).get(p) or {}
    m = d.get("meli")
    if m:
        ml_txt = f"{_usd(d.get('meli_ventas_usd'))} · {m.get('pedidos')} ped · {m.get('publicaciones')} pubs"
    else:
        ml_txt = "no conectado"
    return (f"🌎 {p} · {ds.get('rango') or periodo}\n"
            f"Sitio propio: {_usd(d.get('ventas_usd'))} · {d.get('pedidos', 0)} ped · conv {d.get('conversion', 0)}%\n"
            f"Mercado Libre: {ml_txt}\n"
            f"Ads: Meta {d.get('meta_spend', '—')} {d.get('meta_moneda', '')} · Google {d.get('ad_spend', '—')} {d.get('gads_moneda', '')} · MER {d.get('mer_usd', 0)}x\n"
            f"Email (Klaviyo): {(d.get('klaviyo') or {}).get('email_revenue', '—')}")


def estado() -> str:
    ov = _ov()
    return ("📊 Estado SLEVE E-commerce\n"
            "🟢 Shopify (6) · Meta · Google Ads · GA4 · Search Console · Klaviyo · Redes · Google Trends · Telegram · MCP\n"
            "🟢 Mercado Libre 3/4 (CL/MX/PE) · 🟡 CO (verificación)\n"
            "🟡 Multivende · Business Profile · Merchant Center · 🔴 TikTok · Gorgias\n"
            f"Última data: {ov.get('actualizado', '—')}")


def fallback(text: str) -> str:
    return ("No tengo el razonamiento en lenguaje natural encendido (falta ANTHROPIC_API_KEY con saldo en Railway).\n"
            "Mientras, usá comandos: /resumen /ml /ads /acciones /pais <país> /estado. /help para la lista.")


def _contexto(ov: dict) -> str:
    """Contexto compacto (los 3 períodos + acciones + catálogo + tendencias) para el modelo."""
    ctx = {"actualizado": ov.get("actualizado")}
    per = ov.get("periodos") or {}
    ctx["periodos"] = {k: {"consolidado": (per.get(k) or {}).get("consolidado"),
                           "paises": {p: {kk: (((per.get(k) or {}).get("paises") or {}).get(p) or {}).get(kk)
                                          for kk in ("ventas_usd", "meli_ventas_usd", "pedidos", "conversion",
                                                     "meta_spend", "ad_spend", "mer_usd", "meli", "cuadratura")}
                                      for p in PAISES}}
                       for k in ("7d", "30d", "mes") if per.get(k)}
    ctx["catalogo"] = ov.get("catalogo")
    ctx["tendencias"] = {p: [t.get("termino") for t in (ov.get("tendencias") or {}).get(p, [])[:8]] for p in PAISES}
    return json.dumps(ctx, ensure_ascii=False)[:12000]


def ask(text: str) -> str:
    """Lenguaje natural con la Claude API. Requiere ANTHROPIC_API_KEY. Solo lectura."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return fallback(text)
    try:
        import anthropic
    except Exception:  # noqa: BLE001
        return fallback(text)
    ov = _ov()
    system = (
        "Eres el Agente de E-commerce de SLEVE (electrónica/audio; opera en Chile, Colombia, "
        "México y Perú). Respondes por Telegram: claro, breve y al grano, en español, con los "
        "números del contexto (JSON en vivo del negocio: venta por canal sitio propio + Mercado "
        "Libre, ads Meta/Google, conversión, cuadratura, catálogo, tendencias; montos consolidados "
        "en USD). Si te piden una acción que modifica algo (pausar campañas, cambiar precios/stock, "
        "publicar, enviar), NO la ejecutes: propón el paso y aclara que requiere autorización. "
        "Si falta un dato, dilo. No inventes cifras.\n\nCONTEXTO:\n" + _contexto(ov))
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=MODEL, max_tokens=700,
            system=system,
            messages=[{"role": "user", "content": text}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip() or fallback(text)
    except Exception as e:  # noqa: BLE001
        return f"Error consultando el modelo: {str(e)[:150]}\n\n" + fallback(text)


# Compat con llamadas previas del bot
def build_daily_brief() -> str:
    return resumen("7d") + "\n\n" + acciones("7d")


def specialist_brief(name: str) -> str:
    return {"ads": ads, "marketplaces": mercadolibre}.get(name, lambda: HELP)()
