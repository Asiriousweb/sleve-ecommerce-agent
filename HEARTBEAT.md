# HEARTBEAT.md — Estado del sistema en tiempo real

> Semáforo del agente. Primer archivo que se revisa al iniciar sesión y en el loop nocturno.
> 🟢 OK · 🟡 DEGRADADO · 🔴 ROTO · ⚪ DESCONOCIDO (no verificado esta sesión)

**Última actualización:** 2026-06-27 (revisión de fuentes + smoke test). Detalle por fuente en [CONNECTIONS.md](CONNECTIONS.md).

## Componentes
| Componente | Estado | Nota |
|---|---|---|
| Estructura de archivos base | 🟢 | Creada 2026-06-27 |
| `.mcp.json` | 🔴 | Bloqueado por seguridad; pendiente de aprobación del usuario |
| `.claude/settings.json` | 🔴 | Bloqueado por seguridad; pendiente de aprobación del usuario |
| **Shopify (sitio propio)** | 🟢 | **DIRECTO (gratis) multi-tienda** vía OAuth en el robot: 6 tiendas conectadas (CL, CL B2B, CO, MX, PE, EEUU). Ventas reales por país cada 2h. Cuadratura GA4↔Shopify operativa (todas ✅). 2026-06-29 |
| **Meta / Facebook Ads** | 🟢 | **DIRECTO (Marketing API, gratis)** — System User token (acceso total) en el robot (`META_TOKEN`). Gasto por país cada 2h (descubre cuentas solo, omite "NO USAR"/"ELIMINAR"). 3 cuentas con gasto (CL/CO/PE). 2026-06-29 |
| **GA4 (Google Analytics)** | 🟢 | **DIRECTO (Data API, gratis)** vía service account (`GOOGLE_SA_JSON` + `GA4_PROP_CL/CO/MX/PE`). `_ga4: ok (4/4 props)`. Reemplazó a Windsor (con fallback). Sesiones/conv/tráfico por país. 2026-06-29 |
| **Search Console** | 🟢 | **DIRECTO (gratis)** vía service account (`pull_search_console`, `SC_SITE_CL/CO/MX/PE = sc-domain:sleve.X`). Clics/impresiones/CTR/posición por país. 2026-06-29: CL 1.336 clics (CTR 4,58%, pos 5,2), CO 288 (3,13%, 6,1); MX/PE sin tráfico de búsqueda aún. Google quedó 100% directo (GA4+SC); Windsor solo Google Ads |
| **Google Business Profile** | 🟡 | API **solicitada** (caso 7-9869000040690, 7-10 días hábiles). Hoy solo **Chile** (perfil verificado, bajo la cuenta de marca "Sleve Mobile"). Al aprobar → `pull_google_business` (vistas/llamadas/clics/cómo llegar + reseñas); auth probable por **OAuth**. **CO/MX/PE = PENDIENTE FUTURO**: crear como Negocio de área de servicio con las bodegas (hay en cada país), verificación por correo ~2 sem c/u |
| **Google Ads** | 🟢 | **DIRECTO 4/4 (Explorer access, SIN formulario Basic)** vía delegación de dominio Workspace + Ads API **v23**. `_google_ads: ok (4/4)` (CL/CO/MX/PE; MX/PE con $0 de gasto). Requirió: habilitar "Google Ads API" en GCP + delegación (scope adwords) + token en Railway + vincular las 4 cuentas al MCC `137-819-4398`. Cuentas en USD (Chile) → FX normaliza. ⚠️ ROAS Colombia 40.71x sospechoso → revisar config valor de conversión |
| **Redes sociales (orgánico)** | 🟢 | **DIRECTO (Meta Graph, gratis)** vía `pull_social` (`owned_pages` del negocio `META_BUSINESS_ID` + mismo System User token, que SÍ tenía scopes sociales). 5 páginas SLEVE: CL FB 8.663 / IG @slevemobile 61k; CO IG @sleve.co 11k; MX 77; PE 2.665. Seguidores + posts por país. Próximamente: alcance/engagement por post. 2026-06-30 |
| **Publicaciones (catálogo Shopify)** | 🟢 | **DIRECTO (Admin GraphQL, gratis)** vía `_shopify_catalog`/`_catalog_cached` (caché 1×día). Completitud de fichas por país (pestaña Publicaciones). 2026-06-29: CL 142 prod (21 sin descripción, **89 no activos = 63%**), CO 73 (**48 no activos = 66%**), MX 17 (4), PE 42 (6), EEUU 26 (0). ⚠️ Revisar % alto de no-activos en CL/CO (¿draft/archived a propósito o se cayeron?). Marketplaces vía Multivende: pendiente |
| **Google Merchant Center** | 🟡 | **TAREA (2026-06-30)**: conectar a la pestaña Publicaciones vía Content API for Shopping (directo/gratis, misma service account de GA4/SC/Ads). Bloqueado: el usuario debe **ordenar sus cuentas MC** (no encuentra todos los países), pasar el/los ID(s) — idealmente cuenta avanzada/MCA — + dar acceso lectura a la SA + habilitar la API en GCP. Mostrará productos aprobados/desaprobados/pendientes + motivos de rechazo por país |
| **MCP remoto (read-only)** | 🟢 | **OPERATIVO en https://mcp-ecommerce.slevemobile.com/mcp** (2026-06-30). POST `/mcp` JSON-RPC a mano en run_railway.py (sin deps). 7 tools de lectura (resumen_global, ventas_por_pais, adquisicion, publicaciones, tendencias, cuadratura, acciones) que leen overview.json por período. Validado end-to-end: SSL Let's Encrypt OK, initialize/tools/list/tools/call OK, auth cerrada (sin token→401, con `MCP_TOKEN` por header bearer o `?token=`→200). Custom domain Railway (puerto 8080) + CNAME. Conectar en Claude: Connectors → URL `/mcp?token=…`. Fase control (acciones con confirmación): futura |
| **Google Trends** | 🟢 | **DIRECTO (feed RSS oficial, gratis)** vía `pull_trends`/`_trends_cached` (caché ~3h). Búsquedas en alza 24h por país (CL/CO/MX/PE), resalta términos afines a electrónica/audio (pestaña Tendencias). Sin Playwright/Chromium (más liviano y estable en Railway). Próximamente: interés-en-el-tiempo de keywords propias |
| **Windsor.ai (multicanal)** | 🟢→⚪ | **YA NO SE USA**: GA4 + Search Console + Google Ads son todos directos ahora. Windsor quedó sin uso → **cancelable**. (Era el único costo pagado de fuentes.) |
| **Loop datos en vivo** | 🟢 | **FUNCIONANDO**: robot trae data real de Windsor cada 2h y la sirve en https://sleve-ecommerce-agents-production.up.railway.app/api/overview (`fuente: windsor en vivo`) |
| **Klaviyo (email)** | 🟢 | **DIRECTO multi-cuenta** (`pull_klaviyo`): una Private API Key por país (`KLAVIYO_API_KEY`/`KLAVIYO_KEY_CL`, `KLAVIYO_KEY_CO/MX/PE`), autodescubre la métrica "Placed Order" de cada cuenta y trae revenue email/SMS 7d. Las 4 conectadas OK (2026-06-29): CL $276.215 (3,2%), CO $227.325 (4,5%), MX/PE 0 (sin ventas). La cuenta "Sleve Mobile" duplicada de Chile se ignora. Banner "cuenta suspendida" en Klaviyo UI no bloquea la API de lectura |
| Multivende | 🟡 | Flujo confirmado: **OAuth2 authorization_code** (patrón Shopify → /multivende/install + /callback). **Correo enviado a api@multivende.com (2026-06-29)** pidiendo cuenta dev + app "SLEVE Agent" (redirect a Railway), permisos **lectura+escritura** (órdenes/inventario/productos/precios). Pendiente: que Multivende entregue Client ID/Secret + capturar endpoints del Postman. Es el corazón (marketplaces hoy demo en dashboard) |
| **Mercado Libre (directo)** | 🟢→🟡 | **CHILE CONECTADO** (2026-06-30): cuenta SLEVEMOBILE (user 290288222). OAuth `meli_oauth.py` (authorization_code + refresh 6h; país vía /users/me; botón desconectar), `pull_meli` (ventas+pedidos+publicaciones por rango del período) → `paises[].meli`; dashboard Canales → "Mercado Libre (directo)". App creada (SLEVE TECH SPA), `MELI_CLIENT_ID/SECRET` en Railway. **Tip:** conectar en incógnito para no arrastrar otra sesión ML (al inicio se conectó por error una cuenta personal). **Pendiente:** conectar CO/MX/PE en /meli (si tiene cuentas). Reemplaza Nubimetrics (~$320/mes); se cuadrará con Multivende |
| Otros marketplaces latam (Falabella/Walmart/Ripley/París) | 🔴 | Vía Multivende (pendiente) |
| Google Drive / Gmail | ⚪ | Por verificar |
| Telegram (reporte) | 🟢 | **OPERATIVO (2026-06-29)** en @Sleve_ecommerce_bot (chat `920578167`). El bug era que Railway E-commerce tenía el token del bot de Trade → se arregló poniendo el token propio (cada servicio su token, o 409 Conflict). Comandos OK (/ping /brief /estado /ads…). **Pendiente Fase 2:** control en lenguaje natural + notificaciones proactivas → cablear `orchestrator.ask` con Claude (necesita créditos Anthropic) |
| Customer Service (Gorgias) | 🔴 | Centralizado en Gorgias. Conector Windsor disponible (link enviado). Último en activar |
| Dashboard (Vercel) | 🟢 | **LIVE + DATOS EN VIVO: https://ecommerce.slevemobile.com**. Lee `/api/overview` del robot (GA4+Google reales por país, cada 2h). Conversión/sesiones/tráfico reales; ventas $/top productos baseline hasta Shopify. Falta: logo |
| Agente always-on (Railway) | 🟢 | **LIVE en Sleve_Agents** (2026-06-28). Servicio respondiendo Telegram (`/ping` → pong ✅). Patrón Trade (Dockerfile + supervisor + orquestador + 6 especialistas + DuckDB + mcp_server). Falta: Fase 2 (Anthropic API + fuentes reales) |
| Loop nocturno | 🟡 | **Agendado 02:30** (`nightly_audit.py`): snapshot del día SIEMPRE. Auditoría INTELIGENTE de los .md (Claude `claude-opus-4-8` clona el repo, optimiza, commit/push solo) lista pero ESPERA 2 credenciales en Railway: `ANTHROPIC_API_KEY` (con saldo) + `GITHUB_TOKEN` |

## Hallazgos de la revisión de fuentes (2026-06-27)
- **Google Ads:** solo Chile y Colombia reportan gasto en últimos 7d; **México y Perú sin datos** (¿pausados/sin gasto?). Revisar.
- **Google Ads Chile — escala sospechosa:** spend 352 con 2.438 clics y conversion_value 1.419 → posible mala configuración de moneda/valor de conversión. Revisar antes de usar para ROAS.
- **GA4 conversión:** Chile 0,62% (25.036 ses/156 trans) vs Colombia 1,76% — Chile convierte bajo pese a ser el grueso del tráfico → oportunidad.
- **México casi inactivo:** 92 sesiones, 0 transacciones en 7d. Definir si está activo.

## Pendientes que afectan operación
- Definir acceso a Multivende y marketplaces (es el corazón de la centralización).
- Completar el resto de CONTEXT.md (catálogo, márgenes, B2B).
- Aprobar `.mcp.json` y `settings.json`.
- Limpiar/identificar las cuentas de Meta Ads válidas vs. basura.
- Conectar Meta Ads y TikTok en Windsor.ai para consolidar todo el spend en un solo lugar.
