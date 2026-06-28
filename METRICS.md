# METRICS.md — Métricas y KPIs del agente

Las métricas que el agente monitorea y que alimentan el dashboard de control. Cada una con su definición, fuente y umbral de alerta.

> 🚧 Borrador inicial — afinar umbrales con el usuario.

## A. Venta
| Métrica | Definición | Fuente | Alerta si... |
|---|---|---|---|
| Ventas totales | Revenue neto consolidado (sin doble conteo) | Shopify + Multivende | Caída > X% vs. período comparable ❓ |
| Ventas por canal | Revenue por sitio/marketplace/país | Por canal | Un canal cae > X% ❓ |
| Ticket promedio | Venta / N° pedidos | Por canal | — |
| Margen de contribución | (precio − costo − comisión − despacho)/precio | DATA.md | Margen < umbral ❓ |

## B. Ads / Performance
| Métrica | Definición | Fuente | Alerta si... |
|---|---|---|---|
| Ad spend | Gasto total en ads | Meta/Google/TikTok vía Windsor | Gasto diario > tope ❓ |
| ROAS | conversion_value / spend | Por plataforma | ROAS < umbral ❓ |
| MER | revenue total / ad spend total | Consolidado | MER < umbral ❓ |
| CAC | spend / nuevos clientes | Ads + Shopify | CAC > umbral ❓ |

## C. Sitio web
| Métrica | Definición | Fuente | Alerta si... |
|---|---|---|---|
| Conversión | pedidos / sesiones | GA4 / Shopify | Caída brusca |
| Tráfico | sesiones por fuente | GA4 (Windsor) | Caída de canal clave |
| Carritos abandonados | % abandono | Shopify / Klaviyo | Alza anómala |

## D. Operación / stock
| Métrica | Definición | Fuente | Alerta si... |
|---|---|---|---|
| Quiebres de stock | SKUs bajo umbral | Multivende / Shopify | Best-seller en quiebre |
| Días de inventario | stock / venta diaria | DATA.md | < N días ❓ |

## E. Customer service
| Métrica | Definición | Fuente | Alerta si... |
|---|---|---|---|
| Tickets abiertos | Consultas/reclamos sin resolver | ❓ (definir herramienta) | Backlog > N |
| Tiempo de respuesta | SLA promedio | ❓ | > SLA objetivo |
| Reputación marketplace | Rating/reviews | Marketplaces | Baja de rating |

---
### 📋 Necesito del usuario
1. Umbrales de alerta (cuánto es "caída preocupante", margen mínimo, ROAS/MER objetivo).
2. Qué métricas quieres ver primero en el dashboard.
3. Qué herramienta usan hoy para customer service (Zendesk, correo, los chats de cada marketplace, etc.).
