# SOURCES.md — Fuentes de datos: origen, confiabilidad y frescura

Catálogo de orígenes de datos. Antes de usar un dato, verifico aquí de dónde viene, qué tan confiable es y cada cuánto se actualiza. Un agente que no sabe el origen ni la frescura de su info mejora sobre arena.

> ⭐ **GA4 es la fuente primaria de analytics**: el análisis SIEMPRE parte de GA4 (qué pasa en la página / interacción) y de ahí se baja al detalle de cada plataforma. Ver ECOSYSTEM.md.
> 🔵 **Multivende es la fuente de verdad de venta/inventario multicanal** (centraliza y dispara stock a Shopify + marketplaces 3P).

**Confiabilidad:** Alta (fuente primaria/oficial) · Media (agregador/derivado) · Baja (scraping/manual).

> **2026-06-30:** todas las fuentes son **DIRECTAS** en el robot (APIs propias, gratis). Windsor retirado. "Vía" = mecanismo real en producción.

| # | Fuente | Qué entrega | Vía (directa) | Confiab. | Frecuencia | Estado |
|---|---|---|---|---|---|---|
| 1 | **Shopify** (6 tiendas) | Ventas, pedidos, AOV, catálogo/fichas, productos top | OAuth directo | Alta | cada 2h | 🟢 CL/CL-B2B/CO/MX/PE/EEUU |
| 2 | **Meta Ads** | Gasto, ROAS, campañas, creativos (fatiga) | System User token | Alta | cada 2h | 🟢 (gasto CL/CO/PE) |
| 3 | **Google Ads** | Gasto, conversiones, valor, campañas | Service account + Ads API v23 | Alta | cada 2h | 🟢 4/4 (MX/PE $0) |
| 4 | **TikTok Ads** | Gasto, conversiones | Marketing API (directo) | Alta | — | 🔴 falta acceso |
| 5 | **GA4** | Sesiones, transacciones, tráfico por fuente, conversión | Service account (Data API) | Alta | cada 2h | 🟢 4/4 |
| 5b | **Search Console** | Clics, impresiones, CTR, posición | Service account | Alta | cada 2h | 🟢 CL/CO (MX/PE sin tráfico) |
| 6 | **Mercado Libre** | Ventas, pedidos, publicaciones activas | OAuth directo (1 app/país) | Alta | cada 2h | 🟢 CL/MX/PE · 🟡 CO |
| 7 | **Klaviyo** | Revenue email/SMS por canal | REST (key por país) | Alta | cada 2h | 🟢 4 cuentas (venta CL/CO) |
| 7b | **Redes orgánico (FB/IG)** | Seguidores, posts por país | Meta Graph (owned_pages) | Alta | cada 2h | 🟢 5 páginas SLEVE |
| 7c | **YouTube** | Suscriptores, vistas, videos top | Data API v3 (API Key) | Alta | ~cada 6h | 🟢 4 canales (CL/PE con datos) |
| 7d | **Metricool** (hub social) | Engagement/alcance por post (todas las redes) | API v2 (`X-Mc-Auth`) | Media (agregador) | ~cada 3h | 🟢 CL/PE con posts |
| 7e | **Google Trends** | Búsquedas en alza 24h por país | Feed RSS | Media | ~cada 3h | 🟢 4 países |
| 7f | **Gorgias** | Tickets, SLA, CSAT | API key | Alta | — | 🔴 falta key |
| 8 | **Multivende** | Pedidos/stock/precios multicanal, boletas | OAuth2 (pendiente) | Alta | — | 🟡 esperando credenciales |
| 8b | **Walmart (3P)** | Ventas, stock, precios | **Directo (Seller API, patrón MeLi)** | Alta | — | 🔴 backlog (MX) |
| 9 | **Otros marketplaces** (Falabella/Ripley/París/Hites) | Ventas, stock, ranking | Vía Multivende | Alta | — | 🔴 |
| 10 | **Business Profile** | Vistas/llamadas/clics/reseñas | API Google (pendiente) | Alta | — | 🟡 API solicitada |
| 11 | **Merchant Center** | Salud productos Google Shopping | Content API (misma SA) | Alta | — | 🟡 ordenar cuentas |
| 12 | **Competencia** | Precios/disponibilidad | WebSearch / Nubimetrics | Baja-Media | on-demand | ⚪ |

## Reglas de uso de datos
- Si una fuente está 🔴 o ⚪ sin verificar, lo declaro al usar el dato y no construyo decisiones críticas sobre ella.
- **Directo = fuente de verdad; agregador = corroboración.** Para una misma métrica en dos fuentes (ej. seguidores por Meta/YouTube directo vs. Metricool), prefiero la **directa** y uso el agregador para enriquecer/contrastar. Ver [[regla-fuentes-directo-vs-metricool]].
- Conciliación clave: las ventas de marketplaces deben cuadrar entre el marketplace, Multivende y la boleta. Discrepancias = bandera roja.
- **Última verificación:** se actualiza cada vez que confirmo que la fuente responde (queda reflejado en HEARTBEAT.md).

> 📌 Esta tabla es un borrador basado en las herramientas disponibles. Hay que **confirmar con el usuario** qué fuentes están realmente activas, qué cuentas, y cómo se accede a Multivende y a cada marketplace.
