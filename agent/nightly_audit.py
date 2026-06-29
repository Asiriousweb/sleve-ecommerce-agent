#!/usr/bin/env python3
"""
Loop nocturno (macro-ciclo). Cada noche, si hubo cambios:
  • Housekeeping liviano (siempre): snapshot del estado del día → memoria (volumen).
  • Auditoría inteligente de los .md (consolidar, optimizar, quitar duplicados) → requiere
    ANTHROPIC_API_KEY con saldo (hook abajo). Es el mismo espíritu del audit del agente Trade.

Lo agenda run_railway.py a las 02:30 (TZ del contenedor → poner TZ=America/Santiago).
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
MEM = DATA_DIR / "memory"


def nightly_audit() -> None:
    MEM.mkdir(parents=True, exist_ok=True)
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    over = DATA_DIR / "overview.json"
    estado = {}
    if over.exists():
        try:
            estado = json.loads(over.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass

    # 1) Snapshot del día (housekeeping, sin costo)
    nota = [f"# Snapshot nocturno {fecha}", "", f"fuente: {estado.get('fuente')}", ""]
    for p, v in (estado.get("paises") or {}).items():
        nota.append(f"- {p}: ventas={v.get('ventas_clp')} pedidos={v.get('pedidos')} "
                    f"sesiones={v.get('sesiones')} meta_spend={v.get('meta_spend')} "
                    f"conv={v.get('conversion')}")
    nota.append("")
    nota.append(f"shopify: {estado.get('_shopify')}")
    nota.append(f"meta: {estado.get('_meta')}")
    (MEM / f"{fecha}.md").write_text("\n".join(nota), encoding="utf-8")
    print(f"[nightly {fecha}] snapshot guardado en {MEM}", flush=True)

    # 2) Auditoría inteligente de los .md (consolidar/optimizar) — requiere Claude
    if os.environ.get("ANTHROPIC_API_KEY"):
        # TODO Fase 2: revisar los .md del repo con Claude (Anthropic API / CLI headless),
        # detectar desactualizado/duplicado, aplicar fixes y commit/push (necesita GITHUB_TOKEN).
        print("[nightly] ANTHROPIC_API_KEY presente → auditoría .md (pendiente de implementar)", flush=True)
    else:
        print("[nightly] sin ANTHROPIC_API_KEY → auditoría .md OMITIDA "
              "(cargar créditos en Anthropic para activarla)", flush=True)


if __name__ == "__main__":
    nightly_audit()
