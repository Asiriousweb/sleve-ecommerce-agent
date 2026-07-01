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


def _fechas(dias=7):
    hoy = datetime.now(timezone.utc)
    ini = hoy - timedelta(days=dias)
    return {"from_dt": ini.strftime("%Y-%m-%dT00:00:00"), "to_dt": hoy.strftime("%Y-%m-%dT23:59:59"),
            "start": ini.strftime("%Y%m%d"), "end": hoy.strftime("%Y%m%d")}


def probe(pais="Chile"):
    """Diagnóstico exhaustivo: prueba varios endpoints para descubrir cuáles responden y su
    estructura (posts con datetime, timelines/aggregation para seguidores, lista de marcas)."""
    blog = BLOG_B2C.get(pais)
    f = _fechas(7)
    ensayos = {
        "brands(simpleProfiles)": "/admin/simpleProfiles",
        "posts/instagram": f"/v2/analytics/posts/instagram?from={f['from_dt']}&to={f['to_dt']}",
        "posts/facebook": f"/v2/analytics/posts/facebook?from={f['from_dt']}&to={f['to_dt']}",
        "posts/youtube": f"/v2/analytics/posts/youtube?from={f['from_dt']}&to={f['to_dt']}",
        "timeline/Followers": f"/stats/timeline/Followers?start={f['start']}&end={f['end']}",
        "timeline/Communities": f"/stats/timeline/Communities?start={f['start']}&end={f['end']}",
        "aggregation/Followers": f"/stats/aggregation/Followers?start={f['start']}&end={f['end']}",
    }
    out = {"pais": pais, "blogId": blog, "userId": USER_ID, "token_set": bool(TOKEN)}
    for nombre, ep in ensayos.items():
        try:
            d = _get(ep, blog)
            if isinstance(d, dict):
                info = {"ok": True, "tipo": "dict", "keys": list(d.keys())[:40]}
                # Si trae 'data' como lista con items → muestro el primer item COMPLETO (métricas del post)
                dat = d.get("data")
                if isinstance(dat, list) and dat and isinstance(dat[0], dict):
                    info["item0_keys"] = list(dat[0].keys())
                    info["item0"] = json.dumps(dat[0], ensure_ascii=False)[:2500]
            elif isinstance(d, list):
                info = {"ok": True, "tipo": "list", "len": len(d),
                        "keys_item0": list(d[0].keys())[:40] if d and isinstance(d[0], dict) else None}
            else:
                info = {"ok": True, "tipo": type(d).__name__}
            info["muestra"] = json.dumps(d, ensure_ascii=False)[:1200]
            out[nombre] = info
        except urllib.error.HTTPError as he:
            body = he.read().decode("utf-8", "ignore")
            # Recorta el HTML de los 404 (SPA de Metricool); deja legible el JSON de error
            body = body[:250] if not body.strip().startswith("<") else "(HTML — path no existe)"
            out[nombre] = f"HTTP {he.code}: {body}"
        except Exception as e:  # noqa: BLE001
            out[nombre] = f"ERROR: {str(e)[:200]}"
    return out


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _resumen_red(posts):
    """Agrega los posts de una red: cantidad, alcance, interacciones, likes/comments/shares + top post.
    Tolerante a los campos que varían por red (views/reach/impressions; likes/comments/shares/saves)."""
    alcance = inter = likes = comments = shares = 0.0
    top = None
    for p in posts:
        a = _num(p.get("reach") or p.get("impressions") or p.get("views"))
        lk, cm = _num(p.get("likes")), _num(p.get("comments"))
        sh, sv = _num(p.get("shares")), _num(p.get("saves"))
        e = lk + cm + sh + sv
        alcance += a; inter += e; likes += lk; comments += cm; shares += sh
        if top is None or a > top["alcance"]:
            top = {"titulo": (p.get("title") or p.get("text") or "")[:120],
                   "alcance": round(a), "interacciones": round(e),
                   "url": p.get("watchUrl") or p.get("url") or p.get("postUrl")}
    return {"posts": len(posts), "alcance": round(alcance), "interacciones": round(inter),
            "likes": round(likes), "comments": round(comments), "shares": round(shares), "top": top}


def _consolidar(redes):
    posts = sum(r["posts"] for r in redes.values())
    alcance = sum(r["alcance"] for r in redes.values())
    inter = sum(r["interacciones"] for r in redes.values())
    tops = [dict(t, red=red) for red, r in redes.items() if (t := r.get("top"))]
    tops.sort(key=lambda t: t["alcance"], reverse=True)
    return {"redes": redes, "posts_total": posts, "alcance_total": alcance,
            "interacciones_total": inter,
            "engagement_rate": round(inter / alcance * 100, 2) if alcance else 0,
            "top_posts": tops[:5]}


def pull_metricool(dias=7):
    """Engagement/alcance por post y por país (marcas B2C + LinkedIn corporativo).
    Devuelve ({pais: {...}}, debug). Complemento de las fuentes directas (regla: directo = verdad)."""
    if not TOKEN:
        return {}, "sin METRICOOL_USER_TOKEN"
    f = _fechas(dias)
    qs = f"from={f['from_dt']}&to={f['to_dt']}"
    out, dbg = {}, []
    for pais in PAISES:
        redes = {}
        for red in REDES_B2C:  # instagram, facebook, tiktok, youtube (marca B2C)
            blog = BLOG_B2C.get(pais)
            if not blog:
                continue
            try:
                d = _get(f"/v2/analytics/posts/{red}?{qs}", blog)
                redes[red] = _resumen_red(d.get("data") or [])
            except Exception as e:  # noqa: BLE001
                dbg.append(f"{pais}/{red}:{str(e)[:40]}")
        li = BLOG_LI.get(pais)  # LinkedIn desde la marca corporativa
        if li:
            try:
                d = _get(f"/v2/analytics/posts/linkedin?{qs}", li)
                redes["linkedin"] = _resumen_red(d.get("data") or [])
            except Exception as e:  # noqa: BLE001
                dbg.append(f"{pais}/linkedin:{str(e)[:40]}")
        if redes:
            out[pais] = _consolidar(redes)
    tot = sum(v["posts_total"] for v in out.values())
    return out, (f"ok ({len(out)} países, {tot} posts)" + (" · " + " · ".join(dbg) if dbg else ""))


if __name__ == "__main__":
    print(json.dumps(probe("Chile"), ensure_ascii=False, indent=2))
