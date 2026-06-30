# TASKS.md — Cola de tareas (mantiene el loop vivo)

> Regla de oro: una duda nunca detiene el loop. Se anota en BLOQUEADO, se avisa, y se sigue con lo siguiente.
> Estados: BLOQUEADO (necesita decisión/datos del usuario o de un tercero) · EN PROGRESO · PENDIENTE (puedo solo) · COMPLETADO.

**Última actualización:** 2026-06-30.

---

## 🔴 BLOQUEADO (necesito acción del usuario o de un tercero)

**Acción del usuario (rápida):**
- **Mercado Libre Colombia** — completar la **verificación de cuenta** que pide ML Colombia → reconectar en `/meli`. (CL/MX/PE ya 🟢.)
- **TikTok Ads** — conseguir acceso a la Marketing API (advertiser ID + token) → cierro el MER blended real.
- **Gorgias** — entregar API key → tickets/SLA/CSAT.
- **Merchant Center** — ordenar las cuentas y pasar los IDs → salud de productos en Google Shopping.
- **Créditos Anthropic + GITHUB_TOKEN en Railway** — encienden el loop nocturno y el control por Telegram en lenguaje natural + fase control del MCP.

**Esperando a un tercero:**
- **Multivende** — Client ID/Secret de api@multivende.com (correo enviado 2026-06-29). Corazón de marketplaces (Falabella/Walmart/Ripley/París).
- **Business Profile** — aprobación de la API de Google (caso 7-9869000040690).

## 🟡 EN PROGRESO
- Conectar los 4 países de Mercado Libre (3/4 listos; falta CO por verificación de ML).

## ⚪ PENDIENTE (puedo hacerlo solo cuando haya datos/accesos)
- **P&L real por país/canal** — falta cargar COGS por producto + comisiones por marketplace (ver DATA.md). Sin eso, hoy se muestra contribución = venta − ads.
- **Engagement/alcance por post** en redes (hoy solo seguidores/posts).
- **Proteger `/meli`** con token (igual que el MCP) una vez terminadas las conexiones.
- Limpiar código muerto en `refresh.py` (build_p30/build_rango quedaron sin uso tras el refactor de períodos).

## 🔎 HALLAZGOS a profundizar (con tu ojo)
- **México casi muerto**: ~0 ventas en sitio (30d) y ~1 pedido en ML/7d pese a 24 publicaciones → activar o pausar inversión; revisar precio/posicionamiento.
- **Perú ML**: 63 publicaciones, ~1 pedido/7d → mismo análisis.
- **Catálogo Shopify**: CL 89/142 no activos (63%), CO 48/73 (66%) → revisar si conviene reactivar.
- **Chile**: 21 fichas sin descripción en Shopify → completar (sube conversión y SEO).
- **Gap de tracking GA4↔Shopify** (~26% en Chile): GA4 sub-cuenta ventas → revisar setup de medición.
- **Semana post-Cyber** floja vs promedio 30d (esperable, vigilar).

## ✅ COMPLETADO (últimas 48h — 2026-06-29/30)
- Fuentes directas (gratis): Shopify (6), Meta, Klaviyo (4), GA4, Search Console, Google Ads (4/4), Redes orgánico. Windsor retirado.
- Consolidado en USD (FX); cuadratura conversión con pedidos Shopify + gap de tracking.
- Dashboard v0.6: dropdown país, **período = filtro global** (7d/30d/mes/YoY), pestañas por canal, ads por plataforma (campañas+creativos+fatiga), logo.
- **Publicaciones** (completitud fichas Shopify) · **Tendencias** (Google Trends) · **Productos top** · **Venta por canal** (cuadra).
- **Mercado Libre directo** 3/4 países (una app por país).
- **MCP remoto** read-only operativo en mcp-ecommerce.slevemobile.com.
- Telegram operativo (@Sleve_ecommerce_bot).
- Regla #1 de autorización reforzada (CLAUDE.md + memoria).

---
> Canal de reporte: Telegram (@Sleve_ecommerce_bot). Fase 2 (control natural + notificaciones proactivas) espera créditos Anthropic.
