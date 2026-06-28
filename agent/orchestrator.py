#!/usr/bin/env python3
"""
Orquestador E-commerce — la cabeza. NO procesa data cruda: pide a los especialistas,
consolida y arma el brief. En Fase 2, ask() usará la Anthropic API (claude-opus-4-8)
para responder en lenguaje natural delegando en los especialistas.
"""
import specialists

HELP = (
    "🔵 SLEVE E-commerce Agent — comandos\n"
    "/brief — resumen consolidado (todos los dominios)\n"
    "/ads — performance / ads\n"
    "/marketplaces — marketplaces (Multivende)\n"
    "/organico — tráfico, SEO, descubribilidad\n"
    "/cro — sitio / conversión\n"
    "/social — redes (Metricool)\n"
    "/retencion — email / CRM (Klaviyo)\n"
    "/estado — estado del sistema\n"
    "/ping — test de vida\n\n"
    "(Pronto: preguntas en lenguaje natural con razonamiento Claude)"
)

SPECIALISTS = {
    "ads": specialists.performance_ads,
    "marketplaces": specialists.marketplaces,
    "organico": specialists.organico,
    "cro": specialists.tienda_cro,
    "social": specialists.social,
    "retencion": specialists.retencion_crm,
}


def specialist_brief(name: str) -> str:
    fn = SPECIALISTS.get(name)
    return fn() if fn else f"Especialista '{name}' no existe. /help para ver los comandos."


def build_daily_brief() -> str:
    """Consolida un titular de cada especialista (lo que haría el orquestador cada mañana)."""
    partes = ["🔵 SLEVE · Brief E-commerce (Chile)", ""]
    for name, fn in SPECIALISTS.items():
        try:
            partes.append(fn(titular=True))
        except TypeError:
            partes.append(fn())
        except Exception as e:  # noqa: BLE001
            partes.append(f"• {name}: (error: {e})")
    partes.append("")
    partes.append("Escribe /ads /marketplaces /organico /cro /social /retencion para el detalle.")
    return "\n".join(partes)


def estado() -> str:
    return (
        "📊 Estado SLEVE E-commerce\n"
        "🟢 Shopify CL · GA4 · Google Ads · Klaviyo · Telegram\n"
        "🟡 Meta Ads · Dashboard\n"
        "🔴 Multivende · TikTok · Metricool · Gorgias\n"
        "Orquestador + 8 especialistas · servicio en Railway (Sleve_Agents)"
    )


def fallback(text: str) -> str:
    return ("Por ahora respondo comandos: /brief /ads /marketplaces /organico /cro "
            "/social /retencion /estado /ping /help.\n"
            "(El razonamiento en lenguaje natural llega en la Fase 2.)")


def ask(text: str) -> str:
    """TODO Fase 2: usar Anthropic API (claude-opus-4-8) para interpretar `text`,
    decidir qué especialistas consultar, y redactar la respuesta. Requiere ANTHROPIC_API_KEY.
    Implementar consultando la referencia de la Claude API."""
    return fallback(text)
