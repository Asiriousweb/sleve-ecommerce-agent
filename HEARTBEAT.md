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
| **Windsor.ai (multicanal)** | 🟢 | **WINDSOR_API_KEY en el robot** → ahora SOLO Google Ads (GA4 + Search Console pasaron a directo). Pendiente: Meta/TikTok/Metricool/Gorgias nunca se autorizaron en Windsor (van directo) |
| **Loop datos en vivo** | 🟢 | **FUNCIONANDO**: robot trae data real de Windsor cada 2h y la sirve en https://sleve-ecommerce-agents-production.up.railway.app/api/overview (`fuente: windsor en vivo`) |
| **Klaviyo (email)** | 🟢 | **DIRECTO multi-cuenta** (`pull_klaviyo`): una Private API Key por país (`KLAVIYO_API_KEY`/`KLAVIYO_KEY_CL`, `KLAVIYO_KEY_CO/MX/PE`), autodescubre la métrica "Placed Order" de cada cuenta y trae revenue email/SMS 7d. Las 4 conectadas OK (2026-06-29): CL $276.215 (3,2%), CO $227.325 (4,5%), MX/PE 0 (sin ventas). La cuenta "Sleve Mobile" duplicada de Chile se ignora. Banner "cuenta suspendida" en Klaviyo UI no bloquea la API de lectura |
| Multivende | 🔴 | Sin integración definida — prioridad alta |
| Marketplaces latam | 🔴 | Sin conexión definida (CL/CO/MX/PE) |
| Google Drive / Gmail | ⚪ | Por verificar |
| Telegram (reporte) | 🟢 | Operativo. Bot creado, token+chat_id (920578167) en `secrets/.env`. Mensaje de prueba enviado OK 2026-06-27 |
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
