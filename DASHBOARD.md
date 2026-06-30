# DASHBOARD.md — Panel de control SLEVE

El dashboard responde en 30 segundos: **¿cómo vamos?** · **¿qué está sangrando?** · **¿dónde actúo?**
Filosofía (ver SOUL.md): urgencias primero, lo que mueve dinero arriba. Todo se puede filtrar por **país** (CL/CO/MX/PE) y por **canal** (sitio B2C, B2B, marketplaces, social).

> ✅ **LIVE v0.6 en https://ecommerce.slevemobile.com** (2026-06-30). Abajo: la estructura conceptual (capas) + el estado real de implementación al final.

## 🟢 Estado real (v0.6) — qué está LIVE
- **Filtro global de período**: 7 días · 30 días · Este mes · **vs año anterior** — cambia TODA la data manteniendo la misma estructura; todas las pestañas son navegables en cualquier período. (robot expone `overview.periodos`).
- **Dropdown de país**: Global (consolidado USD) / Chile / Colombia / México / Perú — filtra todo.
- **Pestañas**: Resumen · Canales de venta (sitio propio + **Mercado Libre directo** + productos top) · Publicaciones (completitud de fichas Shopify) · Adquisición (Meta/Google/TikTok con campañas + creativos/fatiga) · Redes sociales · Customer Service (próx.) · SEO/AEO/GEO · Competidores (próx.) · Tendencias (Google Trends) · Acciones (urgencias data-driven).
- **Resumen**: KPIs (venta, gasto ads, MER blended, contribución, AOV, CPA, conversión) + tendencia + venta por país + **venta por canal** (share GA4 × venta real Shopify, cuadra) + tabla por país + cuadratura.
- **Consolidado en USD** (FX del día). Conversión calculada con pedidos Shopify (cuadra con Shopify, no GA4).
- **MCP read-only** para consultar todo desde Claude (mcp-ecommerce.slevemobile.com).
- Pendiente de datos: Customer Service (Gorgias), Competidores (Nubimetrics/manual), TikTok (gasto), P&L con COGS/comisiones.

---

## 🧭 Estructura en capas

### 0 · BARRA DE URGENCIAS (siempre arriba)
Solo lo que requiere acción HOY. Si está vacía, buenas noticias.
- 🔴 Quiebre de stock de best-seller (por país/canal)
- 🔴 Campaña quemando plata (ROAS < umbral, spend alto)
- 🔴 Caída de venta anómala (canal/país vs. patrón)
- 🔴 Cuenta de ads caída/flagged/disabled
- 🟠 Tickets de customer service fuera de SLA
- 🟠 Reputación de marketplace bajando / penalización de despacho
- 🟠 Descalce de conciliación (marketplace ↔ Multivende ↔ boleta)

### 1 · VENTA (consolidado) — *la foto del negocio*
- **Revenue:** hoy · ayer · MTD · vs. período anterior · vs. año anterior
- **Por país:** CL · CO · MX · PE
- **Por canal:** sitio B2C · B2B · cada marketplace · (social commerce)
- **# pedidos · unidades · ticket promedio (AOV)**
- **Margen de contribución** (cuando haya costos + comisiones)
- **Top 10 / Bottom 10 productos**
- Fuentes: Shopify (multi-tienda) + Multivende (marketplaces)

### 2 · PERFORMANCE / ADS — *la métrica reina: MER*
- **Ad spend total** y por plataforma (Meta · Google · TikTok) y por país
- **MER** = revenue total / ad spend total ← número que manda
- **ROAS** por plataforma/país · **CAC** · **CPA**
- **Anomalías:** campañas con spend alto y ROAS bajo
- Fuentes: Meta Ads (MCP) + Google/TikTok (Windsor)

### 3 · SITIO WEB — *salud del embudo*
- Sesiones · fuentes de tráfico · **tasa de conversión** · AOV
- Embudo: visitas → carrito → checkout → compra
- Carritos abandonados (% y monto recuperable)
- Por tienda/país
- Fuentes: GA4 (Windsor) + Shopify + Search Console

### 4 · MARKETPLACES — *vía Multivende*
- Venta por marketplace y país
- **Comisión por canal** (impacto directo en margen)
- Buy box / posición · reputación / rating
- Stock publicado · quiebres por marketplace
- SLA de despacho · penalizaciones
- Fuente: Multivende (API)

### 5 · REDES SOCIALES (orgánico) — *comunidad y contenido*
- Crecimiento de seguidores · alcance · **engagement rate** por red (IG/FB/TikTok/YT)
- Posts/reels top · formato y horario que convierte
- Social → tráfico → venta (atribución)
- Menciones / sentimiento
- Fuente: Windsor (orgánico) + Meta. Ver SOCIAL.md

### 6 · EMAIL / CRM (Klaviyo)
- **% del revenue que viene de email** · revenue por flow
- Crecimiento de lista · engagement
- Flows clave: abandono de carrito, bienvenida, post-compra
- Fuente: Klaviyo (MCP)

### 7 · CUSTOMER SERVICE
- Tickets abiertos · tiempo de respuesta · backlog · por canal/país
- Temas recurrentes (señal de problema de producto/logística)
- Reputación
- Fuente: por definir (correo/marketplace/WhatsApp). Ver CUSTOMER-SERVICE.md

### 8 · STOCK / OPERACIÓN
- Quiebres · **días de inventario** · productos en riesgo
- Conciliación marketplace ↔ Multivende ↔ boleta
- Fuente: Multivende + Shopify

---

## 🚦 Qué se puede construir YA vs. qué espera datos

| Sección | Estado 2026-06-30 | Bloqueado por |
|---|---|---|
| Venta (sitio) | 🟢 Shopify 6 tiendas (4 países) | — |
| Ads | 🟢 Meta + Google (campañas+creativos+fatiga) | TikTok (gasto) → cierra MER real |
| Sitio web | 🟢 GA4 + Search Console + Shopify | — |
| Email | 🟢 Klaviyo (4 países) | — |
| Marketplaces | 🟢 Mercado Libre directo 3/4 · 🟡 resto | ML CO (verificación) · Multivende (resto) |
| Publicaciones | 🟢 catálogo Shopify | Merchant Center + Multivende (marketplaces) |
| Redes sociales | 🟢 seguidores/posts (FB/IG) | engagement/alcance por post |
| Tendencias | 🟢 Google Trends por país | — |
| Customer service | 🔴 | Gorgias API key |
| Competidores | 🔴 | Nubimetrics / carga manual |
| Margen real (P&L) | ⏳ | Costos por producto + comisiones por canal |

**Estado:** el dashboard ya tiene ~85% del valor en vivo. Falta sobre todo: TikTok (gasto), Multivende (resto de marketplaces), Gorgias (CS) y COGS/comisiones para el P&L real.

---

## ⚙️ Formato técnico — web propia (Vercel + Railway) — LIVE
- **Frontend:** Next.js 14 (static export) + Tailwind en `dashboard/app/page.tsx` → **Vercel** (https://ecommerce.slevemobile.com). Hace fetch client-side a `/api/overview`.
- **Robot:** Python en **Railway** (`agent/refresh.py` cada 2h → `overview.json` → `/api/overview`). Supervisor `run_railway.py` (HTTP + bot Telegram + scheduler + endpoint MCP).
- **Datos:** 100% reales en vivo (sin demo). Consolidado USD (FX del día).
- Flujo: robot (llaves propias) → overview.json → /api/overview → dashboard.
