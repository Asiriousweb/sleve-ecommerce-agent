#!/usr/bin/env python3
"""
Refrescador de datos del agente E-commerce. Corre cada 2h (lo agenda run_railway.py).
Trae la data de cada fuente y la deja en un JSON en el volumen, listo para el dashboard.

IMPORTANTE: el robot usa SUS PROPIAS llaves (env vars), no los MCPs de la sesión Claude.
- WINDSOR_API_KEY → una sola llave abre todas las fuentes de Windsor (Google Ads, GA4,
  Search Console, TikTok, Metricool, Gorgias, Meta). Ver pull_windsor().
- Directas (cuando se agreguen): SHOPIFY_TOKEN, KLAVIYO_API_KEY, MULTIVENDE_TOKEN.

HOY: si no hay llaves, escribe el baseline de Chile (placeholder) para que el pipeline
funcione end-to-end. A medida que se agregan llaves, cada pull_* trae datos reales.
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT = DATA_DIR / "overview.json"

WINDSOR_API_KEY = os.environ.get("WINDSOR_API_KEY", "").strip()
WINDSOR_BASE = "https://connectors.windsor.ai/all"


def _log(m):
    print(f"[refresh {datetime.now(timezone.utc):%F %T}Z] {m}", flush=True)


def pull_windsor(connector: str, fields: list[str], date_preset: str = "last_7d"):
    """Lee datos reales de una fuente Windsor con la API key del robot.
    Devuelve lista de dicts, o None si no hay key / falla.
    NOTA: confirmar el formato exacto del endpoint Windsor al integrar la key real."""
    if not WINDSOR_API_KEY:
        return None
    params = {
        "api_key": WINDSOR_API_KEY,
        "connector": connector,
        "fields": ",".join(fields),
        "date_preset": date_preset,
        "_renderer": "json",
    }
    url = f"{WINDSOR_BASE}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode("utf-8")).get("data")
    except Exception as e:  # noqa: BLE001
        _log(f"windsor {connector} error: {e}")
        return None


def _baseline():
    """Placeholder con el baseline real de Chile (hasta enchufar las llaves)."""
    return {
        "pais": "Chile",
        "kpis": {
            "ventas_clp": 70_500_000, "pedidos": 2847, "unidades": 5261,
            "aov": 24851, "mer": 3.4, "conversion": 1.25, "sesiones": 178000,
        },
        "fuente": "baseline (placeholder)",
    }


def build_overview() -> dict:
    """Arma el overview. Intenta fuentes reales (Windsor); cae al baseline si no hay llaves."""
    data = _baseline()
    # --- HOOKS para datos reales (se activan al tener WINDSOR_API_KEY) ---
    ga4 = pull_windsor("googleanalytics4", ["source", "medium", "sessions", "transactions"])
    if ga4:
        data["ga4_fuentes"] = ga4
        data["fuente"] = "windsor (en vivo)"
    gads = pull_windsor("google_ads", ["account_name", "spend", "conversions", "conversion_value"])
    if gads:
        data["google_ads"] = gads
    # TODO: shopify/klaviyo/multivende directos (con sus llaves), meta vía windsor.
    return data


def refresh() -> None:
    overview = {
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "cadencia": "cada 2h",
        "data": build_overview(),
    }
    OUT.write_text(json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"overview.json actualizado ({overview['data']['fuente']}) → {OUT}")


if __name__ == "__main__":
    refresh()
    print(OUT.read_text(encoding="utf-8")[:400])
