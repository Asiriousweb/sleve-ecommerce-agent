#!/usr/bin/env python3
"""
MCP remoto (Streamable HTTP) READ-ONLY del agente E-commerce.

Implementa el protocolo MCP a mano (JSON-RPC) sobre el MISMO servidor HTTP del
robot (run_railway.py sirve POST /mcp), para no agregar dependencias ni un 2º
puerto (Railway expone uno solo). Pensado para conectarse desde Claude vía el
subdominio mcp-ecommerce.slevemobile.com.

Seguridad: solo LECTURA. Si MCP_TOKEN está seteado, exige Authorization: Bearer.
Las acciones de control (pausar campañas, presupuestos) son una fase posterior y
SIEMPRE pasarán por confirmación.
"""
import json
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
OVERVIEW = DATA_DIR / "overview.json"
PROTO_DEFAULT = "2024-11-05"
PAISES = ["Chile", "Colombia", "México", "Perú"]


def _load():
    try:
        return json.loads(OVERVIEW.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _ds(ov, periodo):
    """Dataset (consolidado + paises) del período pedido."""
    P = ov.get("periodos") or {}
    if periodo in P and P[periodo].get("paises"):
        return P[periodo]
    return {"consolidado": ov.get("consolidado") or {}, "paises": ov.get("paises") or {}, "rango": ov.get("rango")}


def _usd(n):
    try:
        return "US$" + format(round(n), ",d")
    except Exception:  # noqa: BLE001
        return "US$0"


# ---- Herramientas (solo lectura) -------------------------------------------
def _t_resumen_global(periodo="7d"):
    ov = _load(); ds = _ds(ov, periodo); c = ds.get("consolidado") or {}
    return (f"Resumen global · {ds.get('rango') or periodo}\n"
            f"- Venta total: {_usd(c.get('ventas_usd'))} ({c.get('pedidos',0)} pedidos)\n"
            f"- Gasto Ads (Meta+Google): {_usd(c.get('ad_spend_usd'))}\n"
            f"- MER blended: {c.get('mer_usd',0)}x · MER solo Meta: {c.get('mer_meta_usd',0)}x\n"
            f"- Contribución (venta − ads): {_usd(c.get('contrib_usd'))}\n"
            f"- AOV: {_usd(c.get('aov_usd'))} · CPA: {_usd(c.get('cpa_usd'))}\n"
            f"- Conversión: {c.get('conversion',0)}% · Sesiones: {c.get('sesiones',0)}")


def _t_ventas_por_pais(periodo="7d"):
    ov = _load(); ds = _ds(ov, periodo); ps = ds.get("paises") or {}
    out = [f"Ventas por país · {ds.get('rango') or periodo}"]
    for pais in PAISES:
        d = ps.get(pais) or {}
        out.append(f"- {pais}: {_usd(d.get('ventas_usd'))} · {d.get('pedidos',0)} pedidos · "
                   f"conv {d.get('conversion',0)}% · {d.get('sesiones',0)} sesiones · MER {d.get('mer_usd',0)}x")
    return "\n".join(out)


def _t_adquisicion(pais=None, periodo="7d"):
    ov = _load(); ds = _ds(ov, periodo); ps = ds.get("paises") or {}
    objetivo = [pais] if pais else PAISES
    out = [f"Adquisición (ads) · {ds.get('rango') or periodo}"]
    for pa in objetivo:
        d = ps.get(pa) or {}
        out.append(f"\n{pa}: gasto Meta {d.get('meta_spend','—')} {d.get('meta_moneda','')} · "
                   f"gasto Google {d.get('ad_spend','—')} {d.get('gads_moneda','')} · MER {d.get('mer_usd',0)}x · ROAS {d.get('roas',0)}x")
        camps = (d.get("meta_campaigns") or [])[:5]
        for c in camps:
            out.append(f"   · [Meta] {c.get('nombre')} — {c.get('estado')} — gasto {c.get('spend')} — ROAS {c.get('roas')}x")
        fat = [cr for cr in (d.get("meta_creatives") or []) if cr.get("fatiga")]
        if fat:
            out.append(f"   ⚠️ {len(fat)} creativo(s) con fatiga: " + ", ".join(c.get("nombre", "?") for c in fat[:3]))
    return "\n".join(out)


def _t_publicaciones(pais=None):
    ov = _load(); cat = ov.get("catalogo") or {}
    objetivo = [pais] if pais else list(cat.keys())
    out = ["Publicaciones (completitud de fichas Shopify)"]
    for pa in objetivo:
        d = cat.get(pa) or {}
        if not d:
            continue
        out.append(f"- {pa}: {d.get('total',0)} productos · sin imagen {d.get('sin_imagen',0)} · "
                   f"sin descripción {d.get('sin_descripcion',0)} · no activos {d.get('no_activos',0)}")
    return "\n".join(out) if len(out) > 1 else "Sin datos de catálogo aún."


def _t_tendencias(pais=None):
    ov = _load(); tr = ov.get("tendencias") or {}
    objetivo = [pais] if pais else list(tr.keys())
    out = ["Tendencias (Google Trends · búsquedas en alza 24h)"]
    for pa in objetivo:
        items = tr.get(pa) or []
        if not items:
            continue
        top = " · ".join(f"{i+1}. {x.get('termino')}" for i, x in enumerate(items[:8]))
        rel = [x.get("termino") for x in items if x.get("relevante")]
        out.append(f"- {pa}: {top}" + (f"\n   afín a SLEVE: {', '.join(rel)}" if rel else ""))
    return "\n".join(out) if len(out) > 1 else "Sin tendencias cargadas aún."


def _t_cuadratura(periodo="7d"):
    ov = _load(); ds = _ds(ov, periodo); ps = ds.get("paises") or {}
    out = [f"Cuadratura GA4 ↔ Shopify · {ds.get('rango') or periodo}"]
    for pais in PAISES:
        q = (ps.get(pais) or {}).get("cuadratura")
        if not q:
            continue
        out.append(f"- {pais}: {'✓' if q.get('ok') else '✗'} GA4 {q.get('ga4_transacciones')} vs "
                   f"Shopify {q.get('shopify_pedidos')} pedidos · gap de tracking {q.get('gap_tracking')}")
    return "\n".join(out) if len(out) > 1 else "Sin cuadratura disponible."


def _t_acciones(periodo="7d"):
    ov = _load(); ds = _ds(ov, periodo); ps = ds.get("paises") or {}; cat = ov.get("catalogo") or {}
    A = []
    for pais in PAISES:
        d = ps.get(pais) or {}
        q = d.get("cuadratura")
        if q and not q.get("ok"):
            A.append(f"🔴 {pais}: descuadre GA4 {q.get('ga4_transacciones')} > Shopify {q.get('shopify_pedidos')} — revisar tracking.")
        if (d.get("sesiones") or 0) > 200 and (d.get("pedidos") or 0) == 0:
            A.append(f"🔴 {pais}: {d.get('sesiones')} sesiones y 0 ventas — activar o pausar inversión.")
        if 0 < (d.get("mer_usd") or 0) < 2:
            A.append(f"🟡 {pais}: MER bajo ({d.get('mer_usd')}x) — ads poco rentables.")
    for pais, c in cat.items():
        if (c.get("sin_descripcion") or 0) > 0:
            A.append(f"🟡 {pais}: {c.get('sin_descripcion')} fichas sin descripción en Shopify.")
        if c.get("total") and (c.get("no_activos", 0) / c["total"]) > 0.5:
            A.append(f"🔵 {pais}: {c.get('no_activos')}/{c.get('total')} productos no activos — revisar catálogo.")
    return "Acciones / urgencias detectadas:\n" + ("\n".join(f"- {a}" for a in A) if A else "Sin urgencias. 🟢")


_TOOLS = [
    ("resumen_global", "KPIs consolidados en USD del período (venta, ads, MER, contribución, AOV, CPA, conversión).",
     {"periodo": {"type": "string", "enum": ["7d", "30d", "mes"], "description": "Ventana (default 7d)"}}, _t_resumen_global),
    ("ventas_por_pais", "Venta, pedidos, conversión y MER por país (CL/CO/MX/PE) en el período.",
     {"periodo": {"type": "string", "enum": ["7d", "30d", "mes"]}}, _t_ventas_por_pais),
    ("adquisicion", "Ads por país: gasto Meta/Google, MER, ROAS, top campañas y creativos con fatiga.",
     {"pais": {"type": "string"}, "periodo": {"type": "string", "enum": ["7d", "30d", "mes"]}}, _t_adquisicion),
    ("publicaciones", "Completitud de fichas Shopify por país: sin imagen, sin descripción, no activos.",
     {"pais": {"type": "string"}}, _t_publicaciones),
    ("tendencias", "Google Trends: búsquedas en alza por país, marca las afines a electrónica/audio.",
     {"pais": {"type": "string"}}, _t_tendencias),
    ("cuadratura", "Estado de cuadratura GA4 ↔ Shopify por país (gap de tracking).",
     {"periodo": {"type": "string", "enum": ["7d", "30d", "mes"]}}, _t_cuadratura),
    ("acciones", "Urgencias y acciones rápidas detectadas (descuadres, MER bajo, catálogo, países sin venta).",
     {"periodo": {"type": "string", "enum": ["7d", "30d", "mes"]}}, _t_acciones),
]
_BY_NAME = {name: fn for name, _, _, fn in _TOOLS}


def _tools_spec():
    out = []
    for name, desc, props, _ in _TOOLS:
        out.append({"name": name, "description": desc,
                    "inputSchema": {"type": "object", "properties": props}})
    return out


def handle(msg: dict):
    """Procesa un mensaje JSON-RPC del protocolo MCP. Devuelve dict (respuesta) o None (notificación)."""
    mid = msg.get("id")
    method = msg.get("method") or ""
    if method == "initialize":
        proto = (msg.get("params") or {}).get("protocolVersion") or PROTO_DEFAULT
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": proto,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "sleve-ecommerce", "version": "1.0.0"},
            "instructions": "Datos en vivo del e-commerce de SLEVE (CL/CO/MX/PE). Solo lectura."}}
    if method.startswith("notifications/"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": _tools_spec()}}
    if method == "tools/call":
        p = msg.get("params") or {}
        name = p.get("name"); args = p.get("arguments") or {}
        fn = _BY_NAME.get(name)
        if not fn:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"tool desconocida: {name}"}}
        try:
            text = fn(**args)
            return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}], "isError": False}}
        except Exception as e:  # noqa: BLE001
            return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"método no soportado: {method}"}}
