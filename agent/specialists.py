#!/usr/bin/env python3
"""
Especialistas del agente E-commerce. Cada función es un dominio (como los analyzers por
retailer del Trade). HOY devuelven texto con el baseline real/demo de Chile. MAÑANA cada
uno consultará su fuente real (Shopify, Windsor, Multivende, Klaviyo, Metricool) — ver TODO.

Convención: cada función acepta `titular=False`. Si titular=True devuelve 1 línea para el
brief consolidado; si no, el detalle del dominio.
"""

# TODO: reemplazar los textos demo por consultas reales (db.py / APIs). Mantener el formato.


def performance_ads(titular: bool = False) -> str:
    if titular:
        return "• Ads: MER 3.4x · Google 1,98% conv (3x Meta) · TikTok 0,43% (ineficiente)"
    return ("📈 Performance Ads (Chile)\n"
            "• MER 3.4x · ROAS Meta 2.9 · Google 3.9 · TikTok 1.8\n"
            "• Google convierte 3x mejor que Meta → reasignar inversión\n"
            "• TikTok quema (0,43% conv) → revisar\n"
            "(demo — fuente real: Meta MCP + Windsor)")


def marketplaces(titular: bool = False) -> str:
    if titular:
        return "• Marketplaces: pendiente conectar Multivende (Falabella/Walmart/Ripley/París/MercadoLibre)"
    return ("🛒 Marketplaces (Chile)\n"
            "• Pendiente conectar Multivende (centraliza los 5 marketplaces 3P)\n"
            "• Una vez conectado: ventas, comisiones, buy box, quiebres, conciliación\n"
            "(sin datos — falta app dev de Multivende)")


def organico(titular: bool = False) -> str:
    if titular:
        return "• Orgánico: 178k sesiones · AI search emergente (chatgpt/perplexity)"
    return ("🔎 Orgánico & Descubribilidad (Chile)\n"
            "• 178k sesiones/30d · Google orgánico 0,78% conv\n"
            "• Aparece tráfico de AI search (chatgpt, perplexity) → capturar\n"
            "(GA4 + Search Console vía Windsor)")


def tienda_cro(titular: bool = False) -> str:
    if titular:
        return "• Tienda/CRO: conversión 1,25% · fuga de checkout 77% (palanca #1)"
    return ("🛍️ Tienda / CRO (Chile)\n"
            "• Ventas $76,6M/30d · 2.349 pedidos · AOV $24.851\n"
            "• Conversión 1,25% · FUGA DE CHECKOUT 77% ← mayor oportunidad\n"
            "• Top: Pulse ANC 2Gen $27,4M · One 2Gen $9,4M\n"
            "(Shopify)")


def social(titular: bool = False) -> str:
    if titular:
        return "• Social: pendiente conectar Metricool (IG/FB/TikTok/YouTube)"
    return ("📱 Social & Contenido (Chile)\n"
            "• Pendiente conectar Metricool\n"
            "• Una vez conectado: alcance, engagement, social→venta\n"
            "(sin datos — autorizar Metricool en Windsor)")


def retencion_crm(titular: bool = False) -> str:
    if titular:
        return "• Retención: email (Klaviyo) ~3% conv, alto valor por sesión"
    return ("✉️ Retención / CRM (Chile)\n"
            "• Klaviyo conectado · email ~3% conv (muy por sobre el promedio)\n"
            "• Oportunidad: flow de recuperación de checkout (fuga 77%)\n"
            "(Klaviyo)")
