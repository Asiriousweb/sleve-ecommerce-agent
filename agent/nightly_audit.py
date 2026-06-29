#!/usr/bin/env python3
"""
Loop nocturno (macro-ciclo). Cada noche, si hubo cambios:
  • Housekeeping liviano (SIEMPRE, sin costo): snapshot del estado del día → memoria (volumen).
  • Auditoría INTELIGENTE de los .md (consolidar, optimizar, quitar duplicados, mantener
    HEARTBEAT/estado al día) → requiere ANTHROPIC_API_KEY con saldo + GITHUB_TOKEN para
    commitear/pushear los cambios. Mismo espíritu que el audit del agente Trade.

Lo agenda run_railway.py a las 02:30 (TZ del contenedor → poner TZ=America/Santiago).
"""
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # raíz del repo (deployed en /app)
DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
MEM = DATA_DIR / "memory"
STATE_FILE = DATA_DIR / ".nightly_state.json"          # huella de la última corrida (volumen)

# --- Config (todo override por env en Railway) ------------------------------
GITHUB_REPO = os.environ.get("GITHUB_REPO", "Asiriousweb/sleve-ecommerce-agent")
GIT_BRANCH = os.environ.get("GIT_BRANCH", "main")
GIT_AUTHOR_NAME = os.environ.get("GIT_AUTHOR_NAME", "SLEVE Agent (nocturno)")
GIT_AUTHOR_EMAIL = os.environ.get("GIT_AUTHOR_EMAIL", "agent@slevemobile.com")

MODEL = "claude-opus-4-8"

# .md que Claude PUEDE optimizar (raíz del repo). CHANGELOG.md se maneja aparte
# (es append-only y crece; no se reescribe). secrets/ jamás entra.
SKIP_MD = {"CHANGELOG.md"}

# Esquema de salida de Claude (structured outputs → JSON garantizado)
_SCHEMA = {
    "type": "object",
    "properties": {
        "resumen": {"type": "string"},
        "cambios": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "archivo": {"type": "string"},
                    "contenido": {"type": "string"},
                    "motivo": {"type": "string"},
                },
                "required": ["archivo", "contenido", "motivo"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["resumen", "cambios"],
    "additionalProperties": False,
}

_SYSTEM = (
    "Eres el editor nocturno del repositorio del agente SLEVE E-commerce. Tu trabajo es "
    "OPTIMIZAR la documentación .md: consolidar, quitar duplicados/contradicciones, mantener "
    "el estado al día (sobre todo HEARTBEAT.md) y dejar todo claro para seguir conectando "
    "fuentes. Reglas estrictas:\n"
    "- Conserva TODA la información real. No inventes datos, métricas ni hechos de negocio.\n"
    "- No toques secretos ni tokens.\n"
    "- Solo propone cambios cuando aportan (sé conservador). Si un archivo está bien, no lo incluyas.\n"
    "- Para cada archivo cambiado devuelve su CONTENIDO COMPLETO ya optimizado (no parches).\n"
    "- Actualiza HEARTBEAT.md con la fecha y el estado más reciente según el snapshot de datos.\n"
    "- Mantén el idioma (español) y el estilo de cada documento."
)


def _read_md(root: Path) -> dict:
    """Lee los .md de la raíz del repo que Claude puede optimizar."""
    out = {}
    for f in sorted(root.glob("*.md")):
        if f.name in SKIP_MD:
            continue
        try:
            out[f.name] = f.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return out


def _normalize_estado(estado: dict) -> dict:
    """Solo los datos que importan para 'hubo cambios' (sin timestamps volátiles)."""
    keys = ("ventas_clp", "pedidos", "sesiones", "meta_spend", "conversion", "roas")
    paises = {p: {k: (v or {}).get(k) for k in keys}
              for p, v in (estado.get("paises") or {}).items()}
    return {"paises": paises, "consolidado": estado.get("consolidado")}


def _fingerprint(estado: dict, md_files: dict) -> str:
    """Huella estable de (datos + .md). Si no cambia, no hay nada que auditar."""
    h = hashlib.sha256()
    h.update(json.dumps(_normalize_estado(estado), sort_keys=True, ensure_ascii=False).encode("utf-8"))
    for name in sorted(md_files):
        h.update(name.encode("utf-8") + b"\0" + md_files[name].encode("utf-8") + b"\0")
    return h.hexdigest()


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"[nightly] no pude guardar estado: {e}", flush=True)


def _ask_claude(md_files: dict, estado: dict) -> dict:
    """Le pasa los .md + el snapshot a Claude y devuelve {resumen, cambios:[...]}."""
    import anthropic

    bloques = [f"### {nombre}\n```markdown\n{txt}\n```" for nombre, txt in md_files.items()]
    prompt = (
        "Snapshot de datos de hoy (overview.json), úsalo para actualizar el estado:\n"
        f"```json\n{json.dumps(estado, ensure_ascii=False)[:6000]}\n```\n\n"
        "Documentos .md actuales del repo:\n\n" + "\n\n".join(bloques) + "\n\n"
        "Revisa y optimiza. Devuelve SOLO los archivos que cambian (contenido completo)."
    )

    client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno
    # streaming porque la salida (archivos completos) puede ser larga
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        msg = stream.get_final_message()

    if msg.stop_reason == "refusal":
        print("[nightly] Claude rechazó la auditoría (refusal) → omitida", flush=True)
        return {"resumen": "", "cambios": []}
    if msg.stop_reason == "max_tokens":
        print("[nightly] aviso: respuesta truncada (max_tokens); aplico lo recibido", flush=True)

    text = next((b.text for b in msg.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except Exception as e:  # noqa: BLE001
        print(f"[nightly] no pude parsear la respuesta de Claude: {e}", flush=True)
        return {"resumen": "", "cambios": []}


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _smart_md_audit(estado: dict, fecha: str) -> dict:
    """Clona el repo, deja que Claude optimice los .md y hace commit/push si hay cambios.

    Devuelve el estado final de los .md (para recalcular la huella)."""
    token = os.environ["GITHUB_TOKEN"]
    url = f"https://x-access-token:{token}@github.com/{GITHUB_REPO}.git"

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        _git(["clone", "--depth", "1", "--branch", GIT_BRANCH, url, str(repo)], cwd=tmp)
        _git(["config", "user.name", GIT_AUTHOR_NAME], cwd=repo)
        _git(["config", "user.email", GIT_AUTHOR_EMAIL], cwd=repo)

        md_files = _read_md(repo)
        if not md_files:
            print("[nightly] no hay .md para auditar", flush=True)
            return {}

        res = _ask_claude(md_files, estado)
        cambios = res.get("cambios") or []

        aplicados = []
        for c in cambios:
            nombre = (c.get("archivo") or "").strip()
            # seguridad: solo .md de la raíz, que ya existían y no están en SKIP
            if nombre not in md_files:
                print(f"[nightly] ignoro cambio fuera de alcance: {nombre}", flush=True)
                continue
            nuevo = c.get("contenido") or ""
            if nuevo and nuevo != md_files[nombre]:
                (repo / nombre).write_text(nuevo, encoding="utf-8")
                aplicados.append(nombre)
                print(f"[nightly] optimizado {nombre} — {c.get('motivo','')}", flush=True)

        # Bitácora en CHANGELOG.md (append, no reescribe)
        resumen = (res.get("resumen") or "").strip()
        if aplicados or resumen:
            chlog = repo / "CHANGELOG.md"
            entrada = (f"\n## Loop nocturno {fecha}\n"
                       f"- {resumen or 'Revisión sin cambios de fondo.'}\n"
                       f"- Archivos optimizados: {', '.join(aplicados) if aplicados else 'ninguno'}\n")
            with chlog.open("a", encoding="utf-8") as fh:
                fh.write(entrada)

        post_md = _read_md(repo)  # estado final de los .md (ya con las ediciones)

        _git(["add", "-A"], cwd=repo)
        # ¿hay algo staged?
        staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo)
        if staged.returncode == 0:
            print("[nightly] sin cambios que commitear", flush=True)
            return post_md

        msg = f"Auto-optimización nocturna {fecha}: {resumen[:60] or 'ajustes a .md'}"
        _git(["commit", "-m", msg], cwd=repo)
        _git(["push", "origin", GIT_BRANCH], cwd=repo)
        print(f"[nightly] commit + push hecho ({len(aplicados)} archivos)", flush=True)
        return post_md


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

    # 2) Auditoría inteligente de los .md (consolidar/optimizar) — requiere Claude + GitHub
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[nightly] sin ANTHROPIC_API_KEY → auditoría .md OMITIDA "
              "(cargar créditos en Anthropic para activarla)", flush=True)
        return
    if not os.environ.get("GITHUB_TOKEN"):
        print("[nightly] sin GITHUB_TOKEN → auditoría .md OMITIDA "
              "(crear token y ponerlo en Railway para commitear los cambios)", flush=True)
        return

    # Candado: si datos + .md están IGUAL que la última corrida, no actuamos (no se gasta).
    current_fp = _fingerprint(estado, _read_md(ROOT))
    if _load_state().get("fingerprint") == current_fp:
        print("[nightly] sin cambios desde la última corrida → auditoría OMITIDA (no se gasta)", flush=True)
        return

    try:
        post_md = _smart_md_audit(estado, fecha)
        _save_state({"fingerprint": _fingerprint(estado, post_md or _read_md(ROOT)),
                     "last_run": fecha})
    except Exception as e:  # noqa: BLE001
        print(f"[nightly] error en auditoría inteligente: {e}", flush=True)


if __name__ == "__main__":
    nightly_audit()
