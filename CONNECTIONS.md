# CONNECTIONS.md — Mapa de conexión de fuentes

Estado real de cada fuente. **Estado:** 🟢 conectado con datos · 🟡 parcial/pendiente acción · 🔴 falta · ⚪ retirado.

**Última revisión:** 2026-06-30. Cambio mayor vs versiones previas: **todo es DIRECTO ahora** (APIs propias en el robot, gratis), Windsor quedó retirado. El robot (Railway) corre sus propias llaves (env vars), no los MCPs de la sesión Claude. Detalle operativo en [HEARTBEAT.md](HEARTBEAT.md).

## Cómo se conecta cada fuente (patrones)
- **OAuth en el robot** (token por cuenta, guardado en el volumen): Shopify (`/shopify`), Mercado Libre (`/meli`). Una página de instalación por fuente.
- **Service account de Google** (un JSON, delegación de dominio): GA4 + Search Console + Google Ads.
- **Token de System User / API key** (env var): Meta Ads + Redes orgánico (mismo token), Klaviyo (una key por país).
- **Feed público**: Google Trends (RSS, sin auth).
- **OAuth2 authorization_code**: Multivende (pendiente credenciales).

## Estado por fuente
| Fuente | Estado | Cómo | Detalle / datos |
|---|---|---|---|
| **Shopify (sitio propio)** | 🟢 | OAuth directo, 6 tiendas | CL, CL-B2B, CO, MX, PE, EEUU. Ventas/pedidos/AOV por país + catálogo (completitud de fichas). Cada 2h |
| **Meta Ads** | 🟢 | System User token (Marketing API) | Gasto + campañas + creativos (fatiga) por país. Cuentas con gasto: CL/CO/PE |
| **Google Ads** | 🟢 | Service account (delegación) + Ads API v23 | 4/4 (CL/CO/MX/PE). MCC 137-819-4398. MX/PE con $0 |
| **GA4** | 🟢 | Service account (Data API) | Sesiones/transacciones/tráfico por fuente, 4 props |
| **Search Console** | 🟢 | Service account | Clics/impresiones/CTR/posición. CL/CO con datos; MX/PE sin tráfico de búsqueda |
| **Klaviyo** | 🟢 | REST, una key por país | Revenue email/SMS 7d/30d/mes. CL/CO con venta; MX/PE 0 |
| **Redes orgánico (FB/IG)** | 🟢 | Meta Graph (owned_pages) | Seguidores + posts por país (5 páginas SLEVE) |
| **YouTube** | 🟢 | **Directo (Data API v3, API Key)** vía `pull_youtube` (handles `SleveXOficial`) | Subs/vistas/videos top por país. CL 37 subs/53.562 vistas · PE 3/1.567 · CO/MX 0. API Key sin restricción de aplicación. 2026-07-01 |
| **Metricool (hub social)** | 🟢 | **Directo (API v2, `X-Mc-Auth` + userId/blogId)** vía `pull_metricool` | **Engagement/alcance por post por país** (IG/FB/TikTok/YouTube B2C + LinkedIn corp). 1 marca/país (blogId en código, token en env `METRICOOL_USER_TOKEN`). 7d: CL 18 posts/2.679 alcance · PE 2. Endpoints: `/v2/analytics/posts/{red}`, `/admin/simpleProfiles`. Regla: complementa/corrobora al directo. 2026-07-01 |
| **Google Trends** | 🟢 | Feed RSS oficial | Búsquedas en alza 24h por país, marca afines a electrónica/audio |
| **Telegram** | 🟢 | Bot propio | @Sleve_ecommerce_bot (chat 920578167). Comandos OK |
| **MCP remoto (read-only)** | 🟢 | JSON-RPC en `/mcp` | https://mcp-ecommerce.slevemobile.com — 7 tools de lectura, auth por token |
| **Mercado Libre (directo)** | 🟢 3/4 | OAuth, **una app por país** | CL+MX+PE conectados (ventas/pedidos/publicaciones). **CO: falta verificación de cuenta en ML** |
| **Multivende** | 🟡 | OAuth2 authorization_code | Esperando Client ID/Secret de api@multivende.com. Corazón de marketplaces |
| **Otros marketplaces** (Falabella/Walmart/Ripley/París/Hites) | 🔴 | Vía Multivende | Pendiente |
| **Business Profile** | 🟡 | API (OAuth) | API solicitada a Google (caso 7-9869000040690). Hoy solo Chile (perfil) |
| **TikTok Ads** | 🔴 | Marketing API | Falta acceso (advertiser ID + token). Cierra el MER blended real |
| **Gorgias (Customer Service)** | 🔴 | API key | Falta la key |
| **Merchant Center** | 🟡 | Content API (misma SA de Google) | Usuario debe ordenar cuentas + pasar IDs |
| **Threads (Meta)** | 🔴 backlog | Threads API (mismo System User token de Meta) | **Directo barato**: reusa el token de Meta ya conectado. Seguidores + insights por post. Buen candidato de bajo esfuerzo (Metricool también lo cubre) |
| **TikTok orgánico** | 🔴 backlog | Directo (Display/Research API, burocrático) | **Metricool lo cubre** por ahora. Directo = trámite. Engagement/alcance por post |
| **TikTok Ads** | 🔴 backlog | TikTok Marketing API (directo) | Advertiser ID + token. Metricool NO cubre ads → va directo. Cierra el MER blended |
| **Twitter / X** | 🔴 backlog | X API v2 (directo, **de pago**) | Free tier muy limitado → **Metricool lo cubre**. Directo solo si se justifica el costo |
| **LinkedIn Ads** | 🔴 backlog | LinkedIn Marketing API (directo) | Campaign analytics. Requiere aprobación MDP. Metricool NO cubre ads → va directo |
| **Amazon Ads** | 🔴 backlog | Amazon Ads API (directo, OAuth) | Sponsored Products/Brands/Display. Separado de SP-API. México |
| **LinkedIn (orgánico + Ads)** | 🔴 backlog | Marketing API directa (OAuth + MDP) | Company page orgánica + LinkedIn Ads. Relevante para **B2B**. Directo requiere aprobación Marketing Developer Platform (trámite lento) |
| **Amazon MX (Seller/Vendor + Ads)** | 🔴 backlog | SP-API + Amazon Ads API directas (LWA OAuth) | México. Seller Central (3P: órdenes/inventario/precios), Vendor Central (1P) y Amazon Ads. Directo factible; setup burocrático (registro developer + roles) |
| **Walmart 3P (directo)** | 🔴 backlog | Walmart Marketplace API directa (**patrón MeLi, no Multivende**) | Evaluar por país: Walmart **México** tiene Seller API (órdenes/inventario/precios). Donde exista API, evita depender de Multivende para Walmart |
| **Spotify** | 🔴 backlog | API limitada | Ad Studio sin API pública de performance; for Artists muy limitada. **Explorar si aporta** antes de invertir esfuerzo |
| **Windsor.ai** | ⚪ desconectado | — | **Desconectado por el usuario (2026-07-01).** Nada depende de él: GA4 + Search Console + Google Ads son directos. El código lo tenía solo como *fallback* que ya no se gatilla (limpiable) |

## Lo que falta para el 100% — por quién depende
**Acción del usuario (rápida):**
- Mercado Libre Colombia → completar verificación de cuenta en ML → conectar en `/meli`.
- TikTok Ads → conseguir advertiser ID + token.
- Gorgias → API key.
- Merchant Center → ordenar cuentas + IDs.
- Créditos Anthropic + GitHub token → loop nocturno + control natural por Telegram + fase control del MCP.

**Esperando a un tercero:**
- Multivende → credenciales de api@multivende.com (correo enviado).
- Otros marketplaces → vía Multivende.
- Business Profile → aprobación de la API de Google.

## Páginas de conexión del robot
- `/shopify` — instalar/ver tiendas Shopify.
- `/meli` — conectar/ver cuentas de Mercado Libre (una app por país: `MELI_CLIENT_ID_CL/CO/MX/PE` + `_SECRET_*`).
- `/mcp` — endpoint MCP (POST JSON-RPC, token).
- `/refresh` — fuerza un refresco de datos on-demand.
