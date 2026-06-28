# DASHBOARD.md — Panel de control SLEVE

El dashboard responde en 30 segundos: **¿cómo vamos?** · **¿qué está sangrando?** · **¿dónde actúo?**
Filosofía (ver SOUL.md): urgencias primero, lo que mueve dinero arriba. Todo se puede filtrar por **país** (CL/CO/MX/PE) y por **canal** (sitio B2C, B2B, marketplaces, social).

> 🚧 Estructura propuesta v1. Falta: confirmar umbrales, prioridades y **formato técnico** (ver final).

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

| Sección | Hoy | Bloqueado por |
|---|---|---|
| Venta (sitio) | ✅ Shopify (Chile activo; resto con switch-shop/Windsor) | Multi-tienda automatizada |
| Ads | ✅ Meta + Google + GA4 | TikTok en Windsor; orden de cuentas Meta |
| Sitio web | ✅ GA4 + Search Console + Shopify | — |
| Email | ✅ Klaviyo | — |
| Marketplaces | ⏳ | App API de Multivende |
| Redes sociales | ⏳ | Autorizar conectores orgánicos en Windsor |
| Customer service | ⏳ | Definir herramienta/fuente |
| Margen real | ⏳ | Costos por producto + comisiones por canal |

**MVP sugerido (construible ahora):** Venta sitio (CL) + Ads (Meta/Google) + MER + Conversión web (GA4) + Email (Klaviyo). Es un dashboard real con ~70% del valor, mientras se conecta Multivende y social.

---

## ⚙️ Formato técnico — DECIDIDO: web propia (Vercel + Railway)
El usuario eligió **dashboard web propio** estilo cockpit dark (referencia: su panel de Trade Marketing).
- **Frontend:** Next.js 14 + Tailwind + Recharts en `dashboard/` → deploy en **Vercel**. ✅ v0.1 construida y compilando (2026-06-27).
- **Backend/Agente:** API always-on en **Railway** que alimenta los datos reales (fase siguiente).
- **Datos hoy:** baseline real de Chile (Shopify + GA4) en `dashboard/lib/data.ts`; marketplaces/ads/social en demo hasta conectar Multivende/Windsor.
- Detalle técnico y deploy en `dashboard/README.md`.

> v0.1 incluye: header + selector país/vista, tabs, selector de semanas, 4 KPI cards, barra de urgencias, tendencia (unidades + $), venta por canal, ROAS por plataforma, top productos y fuentes de tráfico.
