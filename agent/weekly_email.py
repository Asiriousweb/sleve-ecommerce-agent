#!/usr/bin/env python3
"""
Reporte semanal por EMAIL (lunes 8:00 Chile) — UN correo por país + 1 consolidado.

Cada correo trae los KPIs de e-commerce del país (venta sitio propio Shopify +
Mercado Libre + otros marketplaces + ads) con DOBLE evolución para leer la
tendencia con bases comparables:
  • semana vs semana anterior  (periodos 7d ↔ 7d_prev del overview)
  • mes vs mismo mes del año pasado  (bloque `yoy` del overview: 30d móvil YoY)

Destinatarios (responsable por país, se cargan en Railway):
  REPORT_EMAIL_CL / _CO / _MX / _PE  → responsable de cada país
  REPORT_CC                          → copia en cada correo de país (ej. Nicolás)
  REPORT_EMAIL                       → fallback + destinatario del consolidado

Envío (principal): Gmail SMTP + App Password (`GMAIL_EMAIL` + `GMAIL_APP_PASSWORD`),
la MISMA "app de Gmail" que usa el agente de Trade Marketing. Simple, sin depender
del admin del Workspace. Fallback: Gmail API con service account + delegación
(`GOOGLE_SA_JSON`, impersonando `REPORT_SENDER`) si no hay App Password.

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
# Envío: método principal = Gmail SMTP + App Password (la misma "app de Gmail" del agente Trade).
GMAIL_EMAIL = os.environ.get("GMAIL_EMAIL", "").strip()
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
# Fallback: Gmail API con service account + delegación de dominio (si no hay App Password).
GOOGLE_SA_JSON = os.environ.get("GOOGLE_SA_JSON", "").strip()
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
REPORT_EMAIL = os.environ.get("REPORT_EMAIL", "nmatulic@slevemobile.com").strip()
SENDER = os.environ.get("REPORT_SENDER", GMAIL_EMAIL or REPORT_EMAIL).strip()  # From del correo
REPORT_CC = os.environ.get("REPORT_CC", "").strip()             # copia en cada correo de país
DASH_URL = "https://ecommerce.slevemobile.com"
PAISES = ["Chile", "Colombia", "México", "Perú"]
BANDERA = {"Chile": "🇨🇱", "Colombia": "🇨🇴", "México": "🇲🇽", "Perú": "🇵🇪"}
COD = {"Chile": "CL", "Colombia": "CO", "México": "MX", "Perú": "PE"}

# Destinatario responsable por país (env var por país). Fallback al REPORT_EMAIL.
def _dest_pais(pais):
    return os.environ.get(f"REPORT_EMAIL_{COD[pais]}", "").strip() or REPORT_EMAIL


# ─────────────────────────── datos ───────────────────────────
def _ov():
    try:
        return json.loads(OVERVIEW.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _periodo(ov, clave):
    """Devuelve el dataset {consolidado, paises, rango} de un período del overview."""
    P = ov.get("periodos") or {}
    if clave in P and (P[clave] or {}).get("paises"):
        return P[clave]
    if clave == "7d":  # retrocompat: top-level = 7d
        return {"consolidado": ov.get("consolidado") or {}, "paises": ov.get("paises") or {},
                "rango": ov.get("rango")}
    return None


def _usd(n):
    try:
        return "US$" + format(round(n), ",d")
    except Exception:  # noqa: BLE001
        return "US$0"


def _kpis_pais(ds, pais):
    """Extrae y deriva los KPIs comparables de un país de un dataset (7d o 7d_prev)."""
    d = (ds.get("paises") or {}).get(pais) or {} if ds else {}
    m = d.get("meli") or {}
    vs = d.get("ventas_usd") or 0            # sitio (Shopify) USD
    vm = d.get("meli_ventas_usd") or 0       # Mercado Libre USD
    ps = d.get("pedidos") or 0               # pedidos sitio
    pm = m.get("pedidos") or 0               # pedidos ML
    ad = d.get("ad_spend_usd") or 0
    return {
        "venta_sitio": vs, "venta_ml": vm, "venta_total": vs + vm,
        "ped_sitio": ps, "ped_ml": pm, "ped_total": ps + pm,
        "sesiones": d.get("sesiones") or 0, "conversion": d.get("conversion") or 0,
        "ad_spend": ad, "meta_spend": d.get("meta_spend_usd") or 0,
        "google_spend": d.get("gads_spend_usd") or 0,
        "mer": round((vs + vm) / ad, 2) if ad else 0,   # MER blended (venta total / ads)
        "contrib": (vs + vm) - ad,
        "aov": round((vs + vm) / (ps + pm)) if (ps + pm) else 0,
        "publicaciones": m.get("publicaciones") or 0,
        "cpa": round(ad / (ps + pm)) if (ps + pm) else 0,
        "klaviyo": d.get("klaviyo") or {}, "search_console": d.get("search_console") or {},
        "social": d.get("social") or {}, "cuadratura": d.get("cuadratura") or {},
        "moneda": d.get("moneda"), "ventas_local": d.get("ventas_clp") or 0,
    }


def _kpis_consol(ds):
    """KPIs del consolidado (sumando los 4 países, en USD)."""
    if not ds:
        return {}
    c = ds.get("consolidado") or {}
    tot = c.get("ventas_total_usd", (c.get("ventas_sitio_usd") or 0) + (c.get("ventas_meli_usd") or 0))
    ad = c.get("ad_spend_usd") or 0
    return {
        "venta_sitio": c.get("ventas_sitio_usd") or 0, "venta_ml": c.get("ventas_meli_usd") or 0,
        "venta_total": tot, "ped_sitio": c.get("pedidos_sitio") or 0, "ped_ml": c.get("pedidos_meli") or 0,
        "ped_total": c.get("pedidos_total") or 0, "sesiones": c.get("sesiones") or 0,
        "conversion": c.get("conversion") or 0, "ad_spend": ad, "meta_spend": c.get("meta_spend_usd") or 0,
        "google_spend": max(0, ad - (c.get("meta_spend_usd") or 0)),
        "mer": c.get("mer_total_usd") or (round(tot / ad, 2) if ad else 0),
        "contrib": c.get("contrib_usd") or (tot - ad),
        "aov": c.get("aov_total_usd") or (round(tot / (c.get("pedidos_total") or 1)) if c.get("pedidos_total") else 0),
        "publicaciones": c.get("publicaciones_meli") or 0,
        "cpa": c.get("cpa_usd") or 0,
    }


# ─────────────────────────── formato ───────────────────────────
def _delta(now, prev, *, invert=False, pp=False):
    """Chip de variación now vs prev. pp=True → diferencia en puntos porcentuales.
    invert=True → que baje es bueno (CPA, gasto). Verde = mejora."""
    if prev in (None, 0) or now is None:
        return '<span style="color:#aab;font-size:11px;">— s/base</span>'
    if pp:
        diff = round(now - prev, 2)
        good = (diff >= 0) != invert
        arrow = "▲" if diff > 0 else ("▼" if diff < 0 else "▬")
        val = f"{abs(diff)}pp"
    else:
        ch = (now - prev) / prev * 100
        good = (ch >= 0) != invert
        arrow = "▲" if ch > 0 else ("▼" if ch < 0 else "▬")
        val = f"{abs(round(ch))}%"
    color = "#1a9d5a" if good else "#d1435b"
    return f'<span style="color:{color};font-size:11px;font-weight:700;white-space:nowrap;">{arrow} {val}</span>'


def _kpi_card(label, val, delta_html="", sub=""):
    return (f'<td style="padding:12px 14px;background:#f6f7f9;border-radius:10px;vertical-align:top;">'
            f'<div style="font-size:21px;font-weight:800;color:#111;line-height:1.1;">{val}</div>'
            f'<div style="margin-top:3px;">{delta_html}</div>'
            f'<div style="font-size:10px;color:#667;text-transform:uppercase;letter-spacing:.5px;margin-top:4px;">{label}</div>'
            + (f'<div style="font-size:11px;color:#889;">{sub}</div>' if sub else "")
            + '</td>')


def _h3(t):
    return f'<h3 style="margin:22px 0 8px;color:#111;font-size:15px;">{t}</h3>'


def _yoy_line(yoy_node, titulo):
    """Bloque 'mes vs mismo mes año pasado' (venta sitio + sesiones), con base comparable."""
    if not yoy_node:
        return ""
    rn, rp = yoy_node.get("rev_now_usd"), yoy_node.get("rev_prev_usd")
    sn, sp = yoy_node.get("ses_now"), yoy_node.get("ses_prev")
    rg, sg = yoy_node.get("rev_growth"), yoy_node.get("ses_growth")

    def chip(g):
        if g is None:
            return '<span style="color:#aab;font-size:11px;">— s/base</span>'
        color = "#1a9d5a" if g >= 0 else "#d1435b"
        arrow = "▲" if g > 0 else ("▼" if g < 0 else "▬")
        return f'<span style="color:{color};font-weight:700;">{arrow} {abs(round(g,1))}%</span>'

    return (
        f'<p style="margin:6px 0;font-size:13px;">🛒 <b>Venta sitio:</b> {_usd(rn)} '
        f'<span style="color:#889;">vs {_usd(rp)} (año pasado)</span> &nbsp; {chip(rg)}</p>'
        f'<p style="margin:6px 0;font-size:13px;">👣 <b>Sesiones:</b> {format(int(sn or 0),",d")} '
        f'<span style="color:#889;">vs {format(int(sp or 0),",d")} (año pasado)</span> &nbsp; {chip(sg)}</p>'
        f'<p style="margin:2px 0 0;color:#aab;font-size:11px;">{titulo}</p>')


def _acciones_pais(pais, kn, kp, cat):
    A, d = [], kn
    q = kn.get("cuadratura") or {}
    if q and not q.get("ok"):
        A.append(f"🔴 Descuadre de tracking: GA4 {q.get('ga4_transacciones')} vs Shopify {q.get('shopify_pedidos')} pedidos.")
    if kn["sesiones"] > 200 and kn["ped_total"] == 0:
        A.append(f"🔴 {format(kn['sesiones'],',d')} sesiones y 0 ventas — activar o pausar inversión.")
    if 0 < kn["mer"] < 2 and kn["ad_spend"] > 0:
        A.append(f"🟡 MER bajo ({kn['mer']}x) — ads poco rentables esta semana.")
    if kp and kp.get("venta_total"):
        ch = (kn["venta_total"] - kp["venta_total"]) / kp["venta_total"] * 100
        if ch <= -20:
            A.append(f"🔴 Venta total cae {abs(round(ch))}% vs semana anterior.")
        elif ch >= 20:
            A.append(f"🟢 Venta total sube {round(ch)}% vs semana anterior — ver qué funcionó.")
    cc = (cat or {}).get(pais) or {}
    if (cc.get("sin_descripcion") or 0) > 0:
        A.append(f"🟡 {cc['sin_descripcion']} fichas Shopify sin descripción (SEO/conversión).")
    if cc.get("total") and (cc.get("no_activos", 0) / cc["total"]) > 0.5:
        A.append(f"🔵 {cc['no_activos']}/{cc['total']} productos no activos en Shopify — revisar.")
    return A[:6] or ["Sin urgencias esta semana 🟢"]


# ─────────────────────────── plantilla común ───────────────────────────
def _wrap(titulo, sub, cuerpo):
    hoy = datetime.now(timezone.utc).strftime("%d-%m-%Y")
    return f"""<!doctype html><html><body style="margin:0;background:#eef0f3;font-family:Arial,Helvetica,sans-serif;color:#222;">
<div style="max-width:640px;margin:0 auto;padding:20px;">
  <div style="background:#0b0d10;border-radius:14px 14px 0 0;padding:20px 24px;">
    <div style="color:#fff;font-size:20px;font-weight:800;letter-spacing:.5px;">{titulo}</div>
    <div style="color:#9aa;font-size:12px;margin-top:4px;">{sub} · generado {hoy}</div>
  </div>
  <div style="background:#fff;padding:22px 24px;border-radius:0 0 14px 14px;">
    {cuerpo}
    <div style="margin-top:26px;text-align:center;">
      <a href="{DASH_URL}" style="background:#e5145f;color:#fff;text-decoration:none;padding:10px 22px;border-radius:8px;font-weight:700;font-size:14px;">Ver dashboard completo →</a>
    </div>
    <p style="color:#aab;font-size:11px;margin-top:18px;text-align:center;">Agente SLEVE E-commerce · datos en vivo · consolidado en USD · Δ = variación vs semana anterior</p>
  </div>
</div></body></html>"""


def _bloque_kpis(kn, kp):
    """Grid de KPIs headline con variación semana-vs-semana."""
    filas = [
        [("Venta total (USD)", _usd(kn["venta_total"]), _delta(kn["venta_total"], kp.get("venta_total") if kp else None),
          f"{kn['ped_total']} pedidos · sitio + ML"),
         ("Gasto Ads (USD)", _usd(kn["ad_spend"]), _delta(kn["ad_spend"], kp.get("ad_spend") if kp else None, invert=True),
          "Meta + Google")],
        [("MER blended", f"{kn['mer']}x", _delta(kn["mer"], kp.get("mer") if kp else None), "venta total / ads"),
         ("Contribución (USD)", _usd(kn["contrib"]), _delta(kn["contrib"], kp.get("contrib") if kp else None), "venta − ads")],
        [("Sesiones", format(int(kn["sesiones"]), ",d"), _delta(kn["sesiones"], kp.get("sesiones") if kp else None),
          f"conv {kn['conversion']}%"),
         ("Conversión", f"{kn['conversion']}%", _delta(kn["conversion"], kp.get("conversion") if kp else None, pp=True),
          f"AOV {_usd(kn['aov'])}")],
    ]
    out = '<table cellspacing=8 cellpadding=0 width=100%>'
    for fila in filas:
        out += "<tr>" + "".join(_kpi_card(l, v, d, s) for (l, v, d, s) in fila) + "</tr>"
    return out + "</table>"


def _bloque_canales(kn, kp):
    def linea(icon, nombre, kv, kp_key, extra=""):
        pv = kp.get(kp_key) if kp else None
        return (f'<p style="margin:7px 0;font-size:13px;">{icon} <b>{nombre}:</b> {_usd(kv)} '
                f'&nbsp;{_delta(kv, pv)} {extra}</p>')
    ml_extra = (f'<span style="color:#889;">· {kn["ped_ml"]} pedidos '
                f'{_delta(kn["ped_ml"], kp.get("ped_ml") if kp else None)} · {kn["publicaciones"]} publicaciones</span>')
    sitio_extra = (f'<span style="color:#889;">· {kn["ped_sitio"]} pedidos '
                   f'{_delta(kn["ped_sitio"], kp.get("ped_sitio") if kp else None)}</span>')
    return (linea("🛒", "Sitio propio (Shopify)", kn["venta_sitio"], "venta_sitio", sitio_extra)
            + linea("🟡", "Mercado Libre", kn["venta_ml"], "venta_ml", ml_extra)
            + '<p style="margin:7px 0;font-size:13px;color:#889;">🏬 <b>Otros marketplaces</b> '
              '(Falabella · Ripley · París · Hites): próximamente vía Multivende</p>')


def _bloque_ads(kn, kp):
    return (f'<p style="margin:6px 0;font-size:13px;">📘 <b>Meta:</b> {_usd(kn["meta_spend"])} '
            f'{_delta(kn["meta_spend"], kp.get("meta_spend") if kp else None, invert=True)} &nbsp;·&nbsp; '
            f'🔍 <b>Google:</b> {_usd(kn["google_spend"])} '
            f'{_delta(kn["google_spend"], kp.get("google_spend") if kp else None, invert=True)}</p>'
            f'<p style="margin:6px 0;font-size:13px;">CPA {_usd(kn["cpa"])} '
            f'{_delta(kn["cpa"], kp.get("cpa") if kp else None, invert=True)} &nbsp;·&nbsp; '
            f'MER {kn["mer"]}x <span style="color:#889;">(TikTok y ML Ads: próximamente)</span></p>')


def _bloque_extra(kn):
    """Klaviyo (email) + SEO + redes, sin delta (contexto)."""
    out = ""
    k = kn.get("klaviyo") or {}
    if k.get("email_revenue"):
        share = f' · {k.get("share_pct")}% de la venta' if k.get("share_pct") is not None else ""
        out += f'<p style="margin:6px 0;font-size:13px;">✉️ <b>Email (Klaviyo):</b> {_usd(round(k["email_revenue"]))}{share}</p>'
    sc = kn.get("search_console") or {}
    if sc.get("clicks"):
        out += (f'<p style="margin:6px 0;font-size:13px;">🔎 <b>SEO (Search Console):</b> '
                f'{format(int(sc.get("clicks") or 0),",d")} clics · pos. {sc.get("position", "—")} · CTR {sc.get("ctr","—")}%</p>')
    s = kn.get("social") or {}
    if s.get("ig_followers") or s.get("fb_followers"):
        ig = f'IG @{s.get("ig_username")} {format(int(s.get("ig_followers") or 0),",d")}' if s.get("ig_followers") else ""
        fb = f'FB {format(int(s.get("fb_followers") or 0),",d")}' if s.get("fb_followers") else ""
        out += f'<p style="margin:6px 0;font-size:13px;">📱 <b>Redes:</b> {" · ".join(x for x in (ig, fb) if x)}</p>'
    return out or '<p style="margin:6px 0;font-size:13px;color:#889;">Sin datos de email/SEO/redes esta semana.</p>'


# ─────────────────────────── correos ───────────────────────────
def build_pais(ov, pais):
    now, prev = _periodo(ov, "7d"), _periodo(ov, "7d_prev")
    kn = _kpis_pais(now, pais)
    kp = _kpis_pais(prev, pais) if prev else None
    yoy = (ov.get("yoy") or {}).get("paises", {}).get(pais)
    yoy_rango = (ov.get("yoy") or {}).get("rango_actual", "")
    rango = (now or {}).get("rango", "últimos 7 días")
    acc = _acciones_pais(pais, kn, kp, ov.get("catalogo"))
    acc_html = "".join(f'<li style="margin:5px 0;">{a}</li>' for a in acc)
    cuerpo = (
        _h3("Resumen de la semana") + _bloque_kpis(kn, kp)
        + _h3("Cómo va cada canal") + _bloque_canales(kn, kp)
        + _h3("Gasto publicitario") + _bloque_ads(kn, kp)
        + _h3("Mes vs mismo mes del año pasado") + _yoy_line(yoy, f"Base comparable: {yoy_rango} (30 días móviles YoY)")
        + _h3("Otros indicadores") + _bloque_extra(kn)
        + _h3("Acciones / alertas") + f'<ul style="margin:6px 0;padding-left:20px;font-size:13px;">{acc_html}</ul>')
    titulo = f"SLEVE {BANDERA[pais]} {pais} · Reporte semanal E-commerce"
    sub = f"{rango} · vs semana anterior · CL·CO·MX·PE"
    return _wrap(titulo, sub, cuerpo)


def build_consolidado(ov):
    now, prev = _periodo(ov, "7d"), _periodo(ov, "7d_prev")
    kn, kp = _kpis_consol(now), (_kpis_consol(prev) if prev else None)
    yoy = (ov.get("yoy") or {}).get("consolidado")
    yoy_rango = (ov.get("yoy") or {}).get("rango_actual", "")
    rango = (now or {}).get("rango", "últimos 7 días")

    # Tabla por país con variación semana-vs-semana en la venta total
    filas = ""
    for pais in PAISES:
        a = _kpis_pais(now, pais)
        b = _kpis_pais(prev, pais) if prev else None
        filas += (
            '<tr>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;">{BANDERA[pais]} {pais}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;font-weight:700;">{_usd(a["venta_total"])}<br>{_delta(a["venta_total"], b.get("venta_total") if b else None)}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{_usd(a["venta_sitio"])}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{_usd(a["venta_ml"])}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{a["ped_total"]}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{a["conversion"]}%</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{a["mer"]}x</td>'
            '</tr>')
    tabla = (
        '<table cellspacing=0 cellpadding=0 width=100% style="border-collapse:collapse;font-size:13px;">'
        '<tr style="background:#f6f7f9;color:#667;font-size:11px;text-transform:uppercase;">'
        '<td style="padding:8px 10px;">País</td><td style="padding:8px 10px;text-align:right;">Venta total</td>'
        '<td style="padding:8px 10px;text-align:right;">Sitio</td><td style="padding:8px 10px;text-align:right;">ML</td>'
        '<td style="padding:8px 10px;text-align:right;">Pedidos</td><td style="padding:8px 10px;text-align:right;">Conv.</td>'
        f'<td style="padding:8px 10px;text-align:right;">MER</td></tr>{filas}</table>')

    cuerpo = (
        _h3("Resumen consolidado (4 países)") + _bloque_kpis(kn, kp)
        + _h3("Por país") + tabla
        + _h3("Cómo va cada canal") + _bloque_canales(kn, kp)
        + _h3("Gasto publicitario") + _bloque_ads(kn, kp)
        + _h3("Mes vs mismo mes del año pasado") + _yoy_line(yoy, f"Base comparable: {yoy_rango} (30 días móviles YoY)"))
    titulo = "SLEVE 🌎 Consolidado · Reporte semanal E-commerce"
    sub = f"{rango} · vs semana anterior · CL·CO·MX·PE"
    return _wrap(titulo, sub, cuerpo)


# ─────────────────────────── envío ───────────────────────────
def send(html, subject, to, cc=""):
    """Envía un correo HTML. Principal: Gmail SMTP + App Password (misma app del agente Trade).
    Fallback: Gmail API con service account + delegación (si no hay App Password)."""
    # ── Método principal: SMTP + App Password ──
    if GMAIL_EMAIL and GMAIL_APP_PASSWORD:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.header import Header
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_EMAIL
        msg["To"] = to
        if cc and cc != to:
            msg["Cc"] = cc
        msg["Subject"] = Header(subject, "utf-8")   # emojis/acentos en el asunto → UTF-8
        msg.attach(MIMEText(html, "html", "utf-8"))
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
                server.send_message(msg)            # envía a To + Cc de los headers, maneja UTF-8
            return f"ok→{to}" + (f" (cc {cc})" if cc and cc != to else "")
        except Exception as e:  # noqa: BLE001
            return f"error smtp: {str(e)[:160]}"
    # ── Fallback: Gmail API con service account ──
    if not GOOGLE_SA_JSON:
        return "sin credenciales (falta GMAIL_APP_PASSWORD o GOOGLE_SA_JSON)"
    import requests
    from google.oauth2 import service_account
    import google.auth.transport.requests as gart
    creds = service_account.Credentials.from_service_account_info(
        json.loads(GOOGLE_SA_JSON), scopes=GMAIL_SCOPES, subject=SENDER)
    creds.refresh(gart.Request())
    msg = MIMEText(html, "html", "utf-8")
    msg["To"] = to
    msg["From"] = SENDER
    msg["Subject"] = subject
    if cc and cc != to:
        msg["Cc"] = cc
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    r = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                      headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
                      json={"raw": raw}, timeout=60)
    if r.status_code == 200:
        return f"ok→{to}" + (f" (cc {cc})" if cc and cc != to else "")
    return f"error {r.status_code}: {r.text[:160]}"


def weekly_report(test=False):
    """Arma y envía los 5 correos: uno por país (al responsable + copia) + consolidado.
    `test=True` → manda TODO solo a REPORT_EMAIL (sin CC), asunto con [PRUEBA]; no toca a los responsables."""
    ov = _ov()
    hoy = datetime.now(timezone.utc).strftime("%d-%m-%Y")
    pfx = "[PRUEBA] " if test else ""
    res = []
    for pais in PAISES:
        try:
            html = build_pais(ov, pais)
            to = REPORT_EMAIL if test else _dest_pais(pais)
            cc = "" if test else REPORT_CC
            r = send(html, f"{pfx}SLEVE {BANDERA[pais]} {pais} · Reporte semanal ({hoy})", to, cc)
        except Exception as e:  # noqa: BLE001
            r = f"error build {pais}: {str(e)[:120]}"
        res.append(f"{COD[pais]}:{r}")
    try:
        html = build_consolidado(ov)
        r = send(html, f"{pfx}SLEVE 🌎 Consolidado · Reporte semanal ({hoy})", REPORT_EMAIL)
    except Exception as e:  # noqa: BLE001
        r = f"error build consolidado: {str(e)[:120]}"
    res.append(f"GLOBAL:{r}")
    out = " · ".join(res)
    print(f"[weekly_email] {out}", flush=True)
    return out


if __name__ == "__main__":
    print(weekly_report())
