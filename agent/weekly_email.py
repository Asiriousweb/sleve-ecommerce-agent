#!/usr/bin/env python3
"""
Reporte semanal por EMAIL (lunes) con los KPIs de todos los canales:
sitio propio (Shopify) + Mercado Libre + otros marketplaces + gasto en ads.

Envío vía Gmail API con la MISMA service account de Google (GOOGLE_SA_JSON) +
delegación de dominio, impersonando una cuenta del Workspace de SLEVE. Sin
passwords ni servicios de pago.

Requiere: agregar el scope `https://www.googleapis.com/auth/gmail.send` a la
delegación de dominio de la SA en el Google Workspace Admin, e impersonar
REPORT_EMAIL (por defecto nmatulic@slevemobile.com).

Lo agenda run_railway.py los lunes. Prueba on-demand: GET /weekly-email
"""
import base64
import json
import os
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
OVERVIEW = DATA_DIR / "overview.json"
GOOGLE_SA_JSON = os.environ.get("GOOGLE_SA_JSON", "").strip()
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
REPORT_EMAIL = os.environ.get("REPORT_EMAIL", "nmatulic@slevemobile.com").strip()
SENDER = os.environ.get("REPORT_SENDER", REPORT_EMAIL).strip()  # cuenta del Workspace que envía
DASH_URL = "https://ecommerce.slevemobile.com"
PAISES = ["Chile", "Colombia", "México", "Perú"]
BANDERA = {"Chile": "🇨🇱", "Colombia": "🇨🇴", "México": "🇲🇽", "Perú": "🇵🇪"}


def _ov():
    try:
        return json.loads(OVERVIEW.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _ds(ov, periodo="7d"):
    P = ov.get("periodos") or {}
    if periodo in P and (P[periodo] or {}).get("paises"):
        return P[periodo]
    return {"consolidado": ov.get("consolidado") or {}, "paises": ov.get("paises") or {}, "rango": ov.get("rango")}


def _usd(n):
    try:
        return "US$" + format(round(n), ",d")
    except Exception:  # noqa: BLE001
        return "US$0"


def _acciones(ds, cat):
    ps = ds.get("paises") or {}
    A = []
    for pais in PAISES:
        d = ps.get(pais) or {}
        q = d.get("cuadratura")
        if q and not q.get("ok"):
            A.append(f"🔴 {pais}: descuadre GA4 {q.get('ga4_transacciones')} &gt; Shopify {q.get('shopify_pedidos')} — revisar tracking.")
        if (d.get("sesiones") or 0) > 200 and (d.get("pedidos") or 0) == 0:
            A.append(f"🔴 {pais}: {d.get('sesiones')} sesiones y 0 ventas — activar o pausar inversión.")
        if 0 < (d.get("mer_usd") or 0) < 2:
            A.append(f"🟡 {pais}: MER bajo ({d.get('mer_usd')}x) — ads poco rentables.")
    for pais, cc in (cat or {}).items():
        if (cc.get("sin_descripcion") or 0) > 0:
            A.append(f"🟡 {pais}: {cc.get('sin_descripcion')} fichas sin descripción.")
        if cc.get("total") and (cc.get("no_activos", 0) / cc["total"]) > 0.5:
            A.append(f"🔵 {pais}: {cc.get('no_activos')}/{cc.get('total')} productos no activos.")
    return A[:8]


def build_html(periodo="7d") -> str:
    ov = _ov(); ds = _ds(ov, periodo); c = ds.get("consolidado") or {}
    ps = ds.get("paises") or {}
    rango = ds.get("rango") or "últimos 7 días"
    hoy = datetime.now(timezone.utc).strftime("%d-%m-%Y")
    vSitio = c.get("ventas_sitio_usd", c.get("ventas_usd", 0))
    vMeli = c.get("ventas_meli_usd", 0)
    vTotal = c.get("ventas_total_usd", vSitio + vMeli)
    adUsd = c.get("ad_spend_usd", 0)
    metaUsd = c.get("meta_spend_usd", 0)
    googleUsd = max(0, adUsd - metaUsd)
    mer = c.get("mer_total_usd", c.get("mer_usd", 0))

    def kpi(label, val, sub=""):
        return (f'<td style="padding:10px 14px;background:#f6f7f9;border-radius:10px;">'
                f'<div style="font-size:22px;font-weight:800;color:#111;">{val}</div>'
                f'<div style="font-size:11px;color:#667;text-transform:uppercase;letter-spacing:.5px;margin-top:2px;">{label}</div>'
                f'<div style="font-size:11px;color:#889;">{sub}</div></td>')

    # KPIs headline
    kpis = ("<table cellspacing=8 cellpadding=0 width=100%><tr>"
            + kpi("Venta total (USD)", _usd(vTotal), f"{c.get('pedidos_total', c.get('pedidos', 0))} pedidos · sitio + marketplaces")
            + kpi("Gasto Ads (USD)", _usd(adUsd), "Meta + Google")
            + "</tr><tr>"
            + kpi("MER blended", f"{mer}x", "venta total / ads")
            + kpi("Contribución (USD)", _usd(vTotal - adUsd), "venta − ads")
            + "</tr></table>")

    # Por canal
    canal = (f'<p style="margin:6px 0;">🛒 <b>Sitio propio (Shopify):</b> {_usd(vSitio)} · {c.get("pedidos_sitio", c.get("pedidos", 0))} pedidos</p>'
             f'<p style="margin:6px 0;">🟡 <b>Mercado Libre:</b> {_usd(vMeli)} · {c.get("pedidos_meli", 0)} pedidos · {c.get("publicaciones_meli", 0)} publicaciones</p>'
             f'<p style="margin:6px 0;color:#889;">🏬 <b>Otros marketplaces</b> (Falabella · Ripley · París · Hites): próximamente vía Multivende</p>')

    # Tabla por país
    filas = ""
    for pais in PAISES:
        d = ps.get(pais) or {}
        m = d.get("meli") or {}
        tot = (d.get("ventas_usd") or 0) + (d.get("meli_ventas_usd") or 0)
        ped = (d.get("pedidos") or 0) + (m.get("pedidos") or 0)
        filas += (f'<tr>'
                  f'<td style="padding:8px 10px;border-bottom:1px solid #eee;">{BANDERA[pais]} {pais}</td>'
                  f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;font-weight:700;">{_usd(tot)}</td>'
                  f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{_usd(d.get("ventas_usd"))}</td>'
                  f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{_usd(d.get("meli_ventas_usd"))}</td>'
                  f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{ped}</td>'
                  f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{d.get("conversion", 0)}%</td>'
                  f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{d.get("mer_usd", 0)}x</td>'
                  f'</tr>')
    tabla = (f'<table cellspacing=0 cellpadding=0 width=100% style="border-collapse:collapse;font-size:13px;">'
             f'<tr style="background:#f6f7f9;color:#667;font-size:11px;text-transform:uppercase;">'
             f'<td style="padding:8px 10px;">País</td><td style="padding:8px 10px;text-align:right;">Venta total</td>'
             f'<td style="padding:8px 10px;text-align:right;">Sitio</td><td style="padding:8px 10px;text-align:right;">ML</td>'
             f'<td style="padding:8px 10px;text-align:right;">Pedidos</td><td style="padding:8px 10px;text-align:right;">Conv.</td>'
             f'<td style="padding:8px 10px;text-align:right;">MER</td></tr>{filas}</table>')

    acc = _acciones(ds, ov.get("catalogo"))
    acc_html = ("".join(f'<li style="margin:4px 0;">{a}</li>' for a in acc)) if acc else "<li>Sin urgencias 🟢</li>"

    return f"""<!doctype html><html><body style="margin:0;background:#eef0f3;font-family:Arial,Helvetica,sans-serif;color:#222;">
<div style="max-width:640px;margin:0 auto;padding:20px;">
  <div style="background:#0b0d10;border-radius:14px 14px 0 0;padding:20px 24px;">
    <div style="color:#fff;font-size:20px;font-weight:800;letter-spacing:1px;">SLEVE · Reporte semanal E-commerce</div>
    <div style="color:#9aa;font-size:12px;margin-top:4px;">{rango} · generado {hoy} · CL·CO·MX·PE</div>
  </div>
  <div style="background:#fff;padding:22px 24px;border-radius:0 0 14px 14px;">
    <h3 style="margin:0 0 8px;color:#111;">Resumen</h3>
    {kpis}
    <h3 style="margin:20px 0 8px;color:#111;">Cómo va cada canal</h3>
    {canal}
    <h3 style="margin:20px 0 8px;color:#111;">Por país</h3>
    {tabla}
    <h3 style="margin:20px 0 8px;color:#111;">Gasto publicitario</h3>
    <p style="margin:6px 0;">📘 Meta: <b>{_usd(metaUsd)}</b> &nbsp;·&nbsp; 🔍 Google: <b>{_usd(googleUsd)}</b>
    <span style="color:#889;"> (TikTok y ML Ads: próximamente)</span></p>
    <h3 style="margin:20px 0 8px;color:#111;">Acciones / urgencias</h3>
    <ul style="margin:6px 0;padding-left:20px;font-size:13px;">{acc_html}</ul>
    <div style="margin-top:24px;text-align:center;">
      <a href="{DASH_URL}" style="background:#e5145f;color:#fff;text-decoration:none;padding:10px 22px;border-radius:8px;font-weight:700;font-size:14px;">Ver dashboard completo →</a>
    </div>
    <p style="color:#aab;font-size:11px;margin-top:20px;text-align:center;">Agente SLEVE E-commerce · datos en vivo · consolidado en USD</p>
  </div>
</div></body></html>"""


def send(html: str, subject: str) -> str:
    if not GOOGLE_SA_JSON:
        return "sin GOOGLE_SA_JSON"
    import requests
    from google.oauth2 import service_account
    import google.auth.transport.requests as gart
    creds = service_account.Credentials.from_service_account_info(
        json.loads(GOOGLE_SA_JSON), scopes=GMAIL_SCOPES, subject=SENDER)
    creds.refresh(gart.Request())
    msg = MIMEText(html, "html", "utf-8")
    msg["To"] = REPORT_EMAIL
    msg["From"] = SENDER
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    r = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                      headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
                      json={"raw": raw}, timeout=60)
    if r.status_code == 200:
        return f"ok (enviado a {REPORT_EMAIL})"
    return f"error {r.status_code}: {r.text[:200]}"


def weekly_report() -> str:
    """Arma y envía el reporte semanal (últimos 7 días)."""
    html = build_html("7d")
    hoy = datetime.now(timezone.utc).strftime("%d-%m-%Y")
    res = send(html, f"SLEVE · Reporte semanal E-commerce ({hoy})")
    print(f"[weekly_email] {res}", flush=True)
    return res


if __name__ == "__main__":
    print(weekly_report())
