# HEARTBEAT.md — Estado del sistema en tiempo real

> Semáforo del agente. Primer archivo que se revisa al iniciar sesión y en el loop nocturno.
> 🟢 OK · 🟡 DEGRADADO · 🔴 ROTO · ⚪ DESCONOCIDO (no verificado esta sesión)

**Última actualización:** 2026-07-01 (snapshot en vivo GA4 directo). Detalle por fuente en [CONNECTIONS.md](CONNECTIONS.md).

## Snapshot 7d (2026-07-01, GA4 directo en vivo · USD)
> Consolidado, últimos 7 días. Cadencia cada 2h. Fuente: GA4 directo (en vivo).
- **Venta sitio propio (Shopify):** $10.078 USD · 264 pedidos · AOV $38
- **Mercado Libre (directo):** $20.000 USD · 667 pedidos · 142 publicaciones
- **Venta total:** $30.078 USD · 931 pedidos · AOV total $32
- **Ad spend:** $3.734 USD (Meta $3.339) · CPA $14
- **MER sitio:** 2,7 · **MER Meta:** 3,02 · **MER total (blended):** 8,06
- **Sesiones:** 30.096 · **Conversión:** 0,57%
- **Chile:** 27.280 sesiones · GA4 132 trans ↔ Shopify 223 pedidos (gap tracking 91, cuadratura ✅) · $8.500 USD sitio ($7.843.785 CLP) · AOV $35.174 CLP
- ⚠️ ROAS consolidado (42,02) infla por valor de conversión de Google Ads mal configurado (ver Google Ads abajo) → usar MER como métrica reina.

## Componentes
| Componente | Estado | Nota |
|---|---|---|
| Estructura de archivos base | 🟢 | Creada 2026-06-27 |
| `.mcp.json` | 🔴 | Bloqueado por seguridad; pendiente de aprobación del usuario |
| `.claude/settings.json` | 🔴 | Bloqueado por seguridad; pendiente de aprobación del usuario |
| **Shopify (sitio propio)** | 🟢 | **DIRECTO (gratis) multi-tienda** vía OAuth en el robot: 6 tiendas conectadas (CL, CL B2B, CO, MX, PE, EEUU). Ventas reales por país cada 2h (7d: $10.078 USD / 264 pedidos). Cuadratura GA4↔Shopify operativa (todas ✅). 2026-07-01 |
| **Meta / Facebook Ads** | 🟢 | **DIRECTO (Marketing API, gratis)** — System User token (acceso total) en el robot (`META_TOKEN`). Gasto por país cada 2h (descubre cuentas solo, omite "NO USAR"/"ELIMINAR"). 3 cuentas con gasto (CL/CO/PE). 7d: spend $3.339 USD. 2026-07-01 |
| **GA4 (Google Analytics)** | 🟢 | **DIRECTO (Data API, gratis)** vía service account (`GOOGLE_SA_JSON` + `GA4_PROP_CL/CO/MX/PE`). `_ga4: ok (4/4 props)`. Reemplazó a Windsor (con fallback). Sesiones/conv/tráfico por país. 7d: 30.096 sesiones, conv 0,57%. 2026-07-01 |
| **Search Console** | 🟢 | **DIRECTO (gratis)** vía service account (`pull_search_console`, `SC_SITE_CL/CO/MX/PE = sc-domain:sleve.X`). Clics/impresiones/CTR/posición por país. 2026-06-29: CL 1.336 clics (CTR 4,58%, pos 5,2), CO 288 (3,13%, 6,1); MX/PE sin tráfico de búsqueda aún. Google quedó 100% directo (GA4 + Search Console + Google Ads) |
| **Google Business Profile** | 🟡 | API **solicitada** (caso 7-9869000040690, 7-10 días hábiles). Hoy solo **Chile** (perfil verificado, bajo la cuenta de marca "Sleve Mobile"). Al aprobar → `pull_google_business` (vistas/llamadas/clics/cómo llegar + reseñas); auth probable por **OAuth**. **CO/MX/PE = PENDIENTE FUTURO**: crear como Negocio de área de servicio con las bodegas (hay en cada país), verificación por correo ~2 sem c/u |
| **Google Ads** | 🟢 | **DIRECTO 4/4 (Explorer access, SIN formulario Basic)** vía delegación de dominio Workspace + Ads API **v23**. `_google_ads: ok (4/4)` (CL/CO/MX/PE; MX/PE con $0 de gasto). Requirió: habilitar "Google Ads API" en GCP + delegación (scope adwords) + token en Railway + vincular las 4 cuentas al MCC `137-819-4398`. Cuentas en USD (Chile) → FX normaliza. ⚠️ Valor de conversión mal configurado infla ROAS (Chile Search ROAS 2,71 / PMax 8,71 razonables; consolidado 42x no) → revisar config valor de conversión |
| **Redes sociales (orgánico)** | 🟢 | **DIRECTO (Meta Graph, gratis)** vía `pull_social` (`owned_pages` del negocio `META_BUSINESS_ID` + mismo System User token, que SÍ tenía scopes sociales). 5 páginas SLEVE: CL FB 8.663 / IG @slevemobile 61k; CO IG @sleve.co 11k; MX 77; PE 2.665. Seguidores + posts por país. Próximamente: alcance/engagement por post. 2026-06-30 |
| **Publicaciones (catálogo Shopify)** | 🟢 | **DIRECTO (Admin GraphQL, gratis)** vía `_shopify_catalog`/`_catalog_cached` (caché 1×día). Completitud de fichas por país (pestaña Publicaciones). 2026-06-29: CL 142 prod (21 sin descripción, **89 no activos = 63%**), CO 73 (**48 no activos = 66%**), MX 17 (4), PE 42 (6), EEUU 26 (0). ⚠️ Revisar % alto de no-activos en CL/CO (¿draft/archived a propósito o se cayeron?). Marketplaces vía Multivende: pendiente |
| **Google Merchant Center** | 🟡 | **TAREA (2026-06-30)**: conectar a la pestaña Publicaciones vía Content API for Shopping (directo/gratis, misma service account de GA4/SC/Ads). Bloqueado: el usuario debe **ordenar sus cuentas MC** (no encuentra todos los países), pasar el/los ID(s) — idealmente cuenta avanzada/MCA — + dar acceso lectura a la SA + habilitar la API en GCP. Mostrará productos aprobados/desaprobados/pendientes + motivos de rechazo por país |
| **MCP remoto (read-only)** | 🟢 | **OPERATIVO en https://mcp-ecommerce.slevemobile.com/mcp** (2026-06-30). POST `/mcp` JSON-RPC a mano en run_railway.py (sin deps). 7 tools de lectura (resumen_global, ventas_por_pais, adquisicion, publicaciones, tendencias, cuadratura, acciones) que leen overview.json por período. Validado end-to-end: SSL Let's Encrypt OK, initialize/tools/list/tools/call OK, auth cerrada (sin token→401, con `MCP_TOKEN` por header bearer o `?token=`→200). Custom domain Railway (puerto 8080) + CNAME. Conectar en Claude: Connectors → URL `/mcp?token=…`. Fase control (acciones con confirmación): futura |
| **Google Trends** | 🟢 | **DIRECTO (feed RSS oficial, gratis)** vía `pull_trends`/`_trends_cached` (caché ~3h). Búsquedas en alza 24h por país (CL/CO/MX/PE), resalta términos afines a electrónica/audio (pestaña Tendencias). Sin Playwright/Chromium (más liviano y estable en Railway). Próximamente: interés-en-el-tiempo de keywords propias |
| **Windsor.ai (multicanal)** | 🟢→⚪ | **YA NO SE USA**: GA4 + Search Console + Google Ads son todos directos ahora. Windsor quedó sin uso → **cancelable**. (Era el único costo pagado de fuentes.) |
| **Loop datos en vivo** | 🟢 | **FUNCIONANDO**: robot trae data **directa** cada 2h (7d) + 30d/mes cacheados 1×día y la sirve en https://sleve-ecommerce-agents-production.up.railway.app/api/overview (`fuente: GA4 directo (en vivo)`). Períodos en `overview.periodos`. Último snapshot: 2026-07-01T04:49Z |
| **Klaviyo (email)** | 🟢 | **DIRECTO multi-cuenta** (`pull_klaviyo`): una Private API Key por país (`KLAVIYO_API_KEY`/`KLAVIYO_KEY_CL`, `KLAVIYO_KEY_CO/MX/PE`), autodescubre la métrica "Placed Order" de cada cuenta y trae revenue email/SMS 7d. Las 4 conectadas OK (2026-06-29): CL $276.215 (3,2%), CO $227.325 (4,5%), MX/PE 0 (sin ventas). La cuenta "Sleve Mobile" duplicada de Chile se ignora. Banner "cuenta suspendida" en Klaviyo UI no bloquea la API de lectura |
| Multivende | 🟡 | Flujo confirmado: **OAuth2 authorization_code** (patrón Shopify → /multivende/install + /callback). **Correo enviado a api@multivende.com (2026-06-29)** pidiendo cuenta dev + app "SLEVE Agent" (redirect a Railway), permisos **lectura+escritura** (órdenes/inventario/productos/precios). Pendiente: que Multivende entregue Client ID/Secret + capturar endpoints del Postman. Es el corazón (marketplaces hoy demo en dashboard) |
| **Mercado Libre (directo)** | 🟢 (3/4) | **CL+MX+PE CONECTADOS**: 7d consolidado $20.000 USD · 667 pedidos · 142 publicaciones. CL SLEVEMOBILE (grueso de la venta), MX SLEVEMEXICO (~1 ped, 24 pubs), PE SOSL… (~1 ped, 63 pubs). **CO pendiente: ML le pide verificación de cuenta** (del lado de ML, no del robot) → completar y reconectar en /meli. Arquitectura: **una app por país** (admins distintos) → `MELI_CLIENT_ID_CL/CO/MX/PE` + `_SECRET_*` (fallback global solo Chile). `meli_oauth.py` (OAuth authorization_code + refresh 6h; verifica que la cuenta autorizada sea del país del state; botón desconectar). `pull_meli` → `paises[].meli`. Dashboard Canales → "Mercado Libre (directo)". ⚠️ Tips: App ID es numérico (no invertir con Secret); conectar en incógnito por país. **Hallazgo:** MX/PE casi sin venta en ML pese a 24/63 publicaciones → revisar precio/posicionamiento. Reemplaza Nubimetrics (~$320/mes); se cuadrará con Multivende. 2026-07-01 |
| Otros marketplaces latam (Falabella/Walmart/Ripley/París) | 🔴 | Vía Multivende (pendiente) |
| Google Drive / Gmail | ⚪ | Por verificar |
| Telegram (control headless) | 🟢 | **OPERATIVO** en @Sleve_ecommerce_bot (chat `920578167`). **Comandos en vivo GRATIS** (leen overview.json, sin API): /resumen /ml /ads /acciones /pais <país> /estado /ping. **Lenguaje natural** (`orchestrator.ask` → Claude API) LISTO, gateado a `ANTHROPIC_API_KEY` con saldo + `TG_MODEL` (default claude-opus-4-8; poné claude-haiku-4-5 para minimizar costo). Solo lectura (regla #1). **Pendiente:** cargar saldo Anthropic para el lenguaje natural + notificaciones proactivas |
| **Reporte semanal (email)** | 🟢 | **OPERATIVO** (`weekly_email.py`, validado end-to-end 2026-07-01). Lunes 08:00 Chile: **5 correos** (4 país CL/CO/MX/PE + 1 consolidado) con KPIs + **evolución semana-vs-semana** (periodo `7d_prev` nuevo) + **mes YoY**. Destinatario por país (`REPORT_EMAIL_CL/CO/MX/PE` + `REPORT_CC`; sin cargar → cae a `REPORT_EMAIL`). **Envío por Gmail API** (service account + scope `gmail.send` + Gmail API habilitada en proyecto GCP `70915132646`); SMTP NO sirve en Railway (bloquea 465). Prueba on-demand: `/weekly-email?test=1` (solo a `REPORT_EMAIL`). Pendiente: cargar responsables que falten |
| Customer Service (Gorgias) | 🔴 | Centralizado en Gorgias. Conexión **directa (API key)** — pendiente que el usuario entregue la key. Último en activar |
| Dashboard (Vercel) | 🟢 | **LIVE + DATOS EN VIVO: https://ecommerce.slevemobile.com**. Lee `/api/overview` del robot (GA4+Google reales por país, cada 2h). Conversión/sesiones/tráfico reales; ventas $/top productos baseline hasta Shopify. Falta: logo |
| Agente always-on (Railway) | 🟢 | **LIVE en Sleve_Agents** (2026-06-28). Servicio respondiendo Telegram (`/ping` → pong ✅). Patrón Trade (Dockerfile + supervisor + orquestador + 6 especialistas + DuckDB + mcp_server). Falta: Fase 2 (Anthropic API + fuentes reales) |
| Loop nocturno | 🟡 | **Agendado 02:30** (`nightly_audit.py`): snapshot del día SIEMPRE. Auditoría INTELIGENTE de los .md (Claude `claude-opus-4-8` clona el repo, optimiza, commit/push solo) lista pero ESPERA 2 credenciales en Railway: `ANTHROPIC_API_KEY` (con saldo) + `GITHUB_TOKEN` |

## Hallazgos de la revisión de fuentes
- **Google Ads — valor de conversión sospechoso:** el ROAS consolidado (42x) infla por la config de valor de conversión (Chile Search 2,71x / PMax 8,71x son razonables). Revisar antes de usar para ROAS; usar **MER** como métrica reina.
- **Google Ads MX/PE sin gasto:** siguen en $0. Definir si están activos.
- **México casi inactivo:** ~0 ventas en sitio y ~1 pedido en ML/7d pese a 24 publicaciones. Revisar precio/posicionamiento o pausar inversión.
- **Gap de tracking GA4↔Shopify (Chile):** GA4 132 trans vs Shopify 223 pedidos (gap 91, ~41%). GA4 subcuenta ventas por consentimiento → revisar setup de medición (cuadratura marca ✅).

## Pendientes que afectan operación
- Definir acceso a Multivende y marketplaces (es el corazón de la centralización).
- Completar el resto de CONTEXT.md (catálogo, márgenes, B2B).
- Aprobar `.mcp.json` y `settings.json`.
- Limpiar/identificar las cuentas de Meta Ads válidas vs. basura.
- Conectar **TikTok Ads directo** para cerrar el MER blended (Meta + Google ya son directos).
