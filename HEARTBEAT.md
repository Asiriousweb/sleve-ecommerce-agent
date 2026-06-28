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
| **Shopify (sitio propio)** | 🟢 | Conectado: "Sleve Mobile Chile", sleve.cl, Shopify **Plus**, CLP. Verificado 2026-06-27 |
| **Meta / Facebook Ads** | 🟡 | Conectado. Cuentas activas+queryables: 31212947 (CLP), 176373918 (USD), 1332315335238191 CHILE RESELLER (USD), 430901705626782 COLOMBIA (COP). Chile/Perú/México activas pero MCP aún no habilitado (rollout). Varias cuentas basura ("NO USAR"/"ELIMINAR"/CLOSED) → limpiar |
| **Windsor.ai (multicanal)** | 🟢 | Conectado + **WINDSOR_API_KEY en el robot (Railway)** → data viva cada 2h. Conectores: Google Ads, GA4, Search Console (CL/CO/MX/PE). Falta autorizar Meta/TikTok/Metricool/Gorgias en Windsor |
| **Loop datos en vivo** | 🟢 | **FUNCIONANDO**: robot trae data real de Windsor cada 2h y la sirve en https://sleve-ecommerce-agents-production.up.railway.app/api/overview (`fuente: windsor en vivo`) |
| **Klaviyo (email)** | 🟢 | Conectado: cuenta "Sleve Mobile Chile" (id LKZuCC), CLP, Ecommerce/Electronics. Verificado 2026-06-27 |
| Multivende | 🔴 | Sin integración definida — prioridad alta |
| Marketplaces latam | 🔴 | Sin conexión definida (CL/CO/MX/PE) |
| Google Drive / Gmail | ⚪ | Por verificar |
| Telegram (reporte) | 🟢 | Operativo. Bot creado, token+chat_id (920578167) en `secrets/.env`. Mensaje de prueba enviado OK 2026-06-27 |
| Customer Service (Gorgias) | 🔴 | Centralizado en Gorgias. Conector Windsor disponible (link enviado). Último en activar |
| Dashboard (Vercel) | 🟢 | **LIVE + DATOS EN VIVO: https://ecommerce.slevemobile.com**. Lee `/api/overview` del robot (GA4+Google reales por país, cada 2h). Conversión/sesiones/tráfico reales; ventas $/top productos baseline hasta Shopify. Falta: logo |
| Agente always-on (Railway) | 🟢 | **LIVE en Sleve_Agents** (2026-06-28). Servicio respondiendo Telegram (`/ping` → pong ✅). Patrón Trade (Dockerfile + supervisor + orquestador + 6 especialistas + DuckDB + mcp_server). Falta: Fase 2 (Anthropic API + fuentes reales) |
| Loop nocturno | 🔴 | No agendado aún |

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
