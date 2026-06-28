# SOURCES.md — Fuentes de datos: origen, confiabilidad y frescura

Catálogo de orígenes de datos. Antes de usar un dato, verifico aquí de dónde viene, qué tan confiable es y cada cuánto se actualiza. Un agente que no sabe el origen ni la frescura de su info mejora sobre arena.

> ⭐ **GA4 es la fuente primaria de analytics**: el análisis SIEMPRE parte de GA4 (qué pasa en la página / interacción) y de ahí se baja al detalle de cada plataforma. Ver ECOSYSTEM.md.
> 🔵 **Multivende es la fuente de verdad de venta/inventario multicanal** (centraliza y dispara stock a Shopify + marketplaces 3P).

**Confiabilidad:** Alta (fuente primaria/oficial) · Media (agregador/derivado) · Baja (scraping/manual).

| # | Fuente | Qué entrega | Vía | Confiabilidad | Frecuencia | Última verif. | Estado |
|---|---|---|---|---|---|---|---|
| 1 | **Shopify** | Ventas, tráfico, catálogo, stock, clientes, órdenes del sitio propio | MCP Shopify | Alta | Tiempo real | 2026-06-27 | 🟢 (Sleve Mobile Chile, Plus, CLP) |
| 2 | **Meta Ads** | Gasto, ROAS, CPA, impresiones, conversiones | MCP Facebook | Alta | ~Tiempo real (atribución con delay) | 2026-06-27 | 🟡 (varias cuentas CL/CO; otras pendientes de habilitar) |
| 3 | **Google Ads** | Gasto, conversiones, CPC | Windsor.ai | Alta | Diaria | 2026-06-27 | 🟢 (CL/CO/MX/PE) |
| 4 | **TikTok Ads** | Gasto, conversiones | Windsor.ai | Alta | Diaria | — | 🔴 (no conectado en Windsor aún) |
| 5 | **GA4** | Tráfico web, fuentes, conversión, embudo | Windsor.ai | Media-Alta (muestreo) | Diaria | 2026-06-27 | 🟢 (CL/CO/MX/PE) |
| 5b | **Search Console** | Posición orgánica, clics, impresiones | Windsor.ai | Alta | Diaria | 2026-06-27 | 🟢 (sleve.cl, slevemobile.cl) |
| 6 | **Amazon Seller Central** | Ventas marketplace Amazon | Windsor.ai | Alta | Diaria | — | ⚪ (conector disponible, no configurado) |
| 7 | **Klaviyo** | Revenue por email/flow, listas, engagement | MCP Klaviyo | Alta | ~Tiempo real | 2026-06-27 | 🟢 (cuenta Chile, id LKZuCC) |
| 7b | **Metricool** | Redes sociales orgánicas (IG/FB/TikTok/YouTube): alcance, engagement, crecimiento | Windsor.ai | Alta | Diaria | — | 🔴 (conector disponible, link enviado) |
| 7c | **Gorgias** | Customer service centralizado: tickets, SLA, canales, reputación | Windsor.ai | Alta | ~Tiempo real | — | 🔴 (conector disponible, link enviado) |
| 8 | **Multivende** | Pedidos consolidados, stock multicanal, boletas | ⚠️ POR DEFINIR (API/CSV) | Alta (si oficial) | ? | — | 🔴 |
| 9 | **Marketplaces CL** (Falabella, Walmart, Ripley, París, MercadoLibre — todos 3P) | Ventas, ranking, comisiones, reputación, quiebres | **Multivende API** | Alta | Tiempo real (webhooks) | — | 🔴 (falta app) |
| 10 | **Competencia** (precios públicos) | Precios y disponibilidad de competidores | WebSearch / scraping | Baja-Media | On-demand | — | ⚪ |
| 11 | **Stripe / PayPal** (si aplica) | Pagos, payouts, fees | Windsor.ai | Alta | Diaria | — | ⚪ |

## Reglas de uso de datos
- Si una fuente está 🔴 o ⚪ sin verificar, lo declaro al usar el dato y no construyo decisiones críticas sobre ella.
- Para una misma métrica disponible en dos fuentes (ej: Meta Ads directo vs. Windsor), prefiero la **primaria** y uso la otra para contraste.
- Conciliación clave: las ventas de marketplaces deben cuadrar entre el marketplace, Multivende y la boleta. Discrepancias = bandera roja.
- **Última verificación:** se actualiza cada vez que confirmo que la fuente responde (queda reflejado en HEARTBEAT.md).

> 📌 Esta tabla es un borrador basado en las herramientas disponibles. Hay que **confirmar con el usuario** qué fuentes están realmente activas, qué cuentas, y cómo se accede a Multivende y a cada marketplace.
