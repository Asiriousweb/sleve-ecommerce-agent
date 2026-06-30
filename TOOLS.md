# TOOLS.md — Herramientas y MCPs disponibles

Catálogo de herramientas del Agente SLEVE. Antes de usar una herramienta, verifico aquí su propósito, cuándo usarla y su estado. **Estado:** 🟢 activo · 🟡 degradado/parcial · 🔴 desconectado · ⚪ por verificar.

> Nota: la mayoría de los MCPs vienen provistos por la plataforma de Claude (prefijo `mcp__claude_ai_*`). Sirven para **análisis ad-hoc en la sesión**. NO confundir con las **conexiones del robot** (sección 0), que son APIs directas con llaves propias y son las que alimentan el dashboard en vivo.

---

## 0. Conexiones DIRECTAS del robot (lo que alimenta el dashboard) ⭐
El robot en Railway (`agent/refresh.py`) trae la data con **sus propias llaves** (env vars), gratis, cada 2h → escribe `overview.json` → lo sirve en `/api/overview` → dashboard Vercel. Estado real en [HEARTBEAT.md](HEARTBEAT.md) y [CONNECTIONS.md](CONNECTIONS.md).

| Fuente directa | Mecanismo | Estado |
|---|---|---|
| Shopify (6 tiendas) | OAuth por tienda (`/shopify`, `shopify_oauth.py`) | 🟢 |
| Meta Ads + Redes orgánico | System User token (Marketing API + Graph owned_pages) | 🟢 |
| Google Ads + GA4 + Search Console | Service account (delegación de dominio) | 🟢 |
| Klaviyo (4 países) | REST, una key por país | 🟢 |
| **Mercado Libre (3/4)** | OAuth una app por país (`/meli`, `meli_oauth.py`) | 🟢 CL/MX/PE · 🟡 CO |
| Google Trends | Feed RSS oficial (sin auth) | 🟢 |
| Telegram | Bot propio (`bot.py`) | 🟢 |
| **MCP remoto read-only** | JSON-RPC en `/mcp` (`mcp_remote.py`) → `mcp-ecommerce.slevemobile.com` | 🟢 |
| Multivende | OAuth2 (pendiente credenciales) | 🟡 |

Períodos: el robot calcula 7d (cada 2h) + 30d + mes (cacheados 1×día) con la MISMA estructura → `overview.periodos`. YoY (vs año anterior) aparte.

---

## A. Núcleo / sistema (siempre disponibles)
| Herramienta | Para qué | Estado |
|---|---|---|
| Bash | Ejecutar scripts, sync de datos, procesar archivos | 🟢 |
| Read / Write / Edit | Leer y editar los archivos del agente | 🟢 |
| WebSearch / WebFetch | Investigar competencia, precios públicos, noticias de marketplaces | ⚪ |
| Agent | Lanzar sub-agentes para búsquedas/tareas multi-paso | 🟢 |
| **Telegram** (`agent/bot.py`) | Canal de reporte asíncrono (avisos, decisiones, urgencias) + comandos | 🟢 operativo (@Sleve_ecommerce_bot). Fase 2 (control natural) espera créditos Anthropic |

---

## B. Sitio web propio — Shopify
**MCP:** `mcp__claude_ai_Shopify__*`
- **Para qué:** gestión de la tienda propia (B2C y, si aplica, B2B). Productos, colecciones, órdenes, clientes, inventario, analytics (ShopifyQL), descuentos, e imágenes. Acceso general vía `graphql_query` / `graphql_mutation` para todo lo demás (metafields, markets, pages, etc.).
- **Cuándo usarla:** analizar ventas/tráfico del sitio, revisar catálogo, detectar quiebres de stock, crear borradores de productos/colecciones/descuentos.
- **Cuándo NO:** publicar cambios de precio/stock en producción sin confirmación (ver CLAUDE.md §5).
- **Quirks:** `run-analytics-query` usa ShopifyQL. Si hay multi-tienda (B2C y B2B separadas), usar `switch-shop`.
- **Estado:** ⚪ por verificar qué tienda(s) están conectadas.

---

## C. Ads / Performance

### Meta / Facebook + Instagram Ads
**MCP:** `mcp__claude_ai_Facebook__ads_*`
- **Para qué:** campañas, ad sets, ads, creatividades, audiencias, catálogos (dynamic ads / advantage+), insights, benchmarks, pixel/datasets, A/B tests.
- **Cuándo usarla:** análisis de ROAS/CPA/gasto, salud del catálogo para dynamic ads, detección de anomalías, preparar campañas (borrador).
- **Cuándo NO:** crear/activar/pausar campañas o cambiar presupuesto sin confirmación.
- **Estado:** ⚪ por verificar cuenta(s) publicitaria(s) conectada(s).

### Google Ads / TikTok Ads / otros (vía Windsor.ai)
Ver bloque D (Windsor.ai). Para **escritura** (pausar/activar/budget) Windsor soporta hoy Meta y Google Ads.

---

## D. Centralizador de datos multicanal — Windsor.ai ⚪ RETIRADO
> **2026-06-30:** Windsor quedó **sin uso** — GA4, Search Console y Google Ads ahora son directos (service account), igual que el resto. Era el único costo pagado de fuentes → **cancelable**. Se mantiene la doc por si se necesita un conector puntual que no tengamos directo.

**MCP:** `mcp__claude_ai_Windsor_ai__*`
- **Para qué:** lectura unificada de **325+ conectores**. Clave para SLEVE porque consolida en un solo lugar: Meta Ads, Google Ads, TikTok Ads, LinkedIn Ads, Amazon Ads, **Amazon Seller Central**, Google Merchant Center, GA4, Shopify, Klaviyo, Stripe, PayPal, Google Sheets, Search Console, y más. También **escribe** en Meta Ads y Google Ads (crear/pausar/activar campañas, ajustar budget).
- **Cuándo usarla:** construir el panorama consolidado de ventas + ads + analytics entre canales/países (el corazón del dashboard). Cuando un dato vive en una plataforma sin MCP propio, probar primero si Windsor tiene el conector.
- **Flujo típico:** `get_connectors` → `get_fields` → `get_data`. Para acciones: `list_actions` → `execute_action`.
- **Cuándo NO:** ejecutar `execute_action` (pausar campañas, cambiar budget) sin confirmación del usuario.
- **Estado:** ⚪ por verificar qué conectores están autorizados en la cuenta Windsor de SLEVE.

---

## E. Marketplaces (multi-país)
- **Mercado Libre = DIRECTO** (API oficial, `agent/meli_oauth.py` + `pull_meli`), una app OAuth por país. 🟢 CL/MX/PE conectados, 🟡 CO (falta verificación de cuenta en ML). Reemplazó a Nubimetrics (~$320/mes). Ver `MARKETPLACES.md`.
- **Falabella / Walmart / Ripley / París = vía Multivende** (pendiente credenciales). Ver `MULTIVENDE.md`.
- **Estado:** 🟢 ML 3/4 · 🟡 resto por Multivende.

---

## F. Email marketing / CRM — Klaviyo
**MCP:** `mcp__claude_ai_Klaviyo__*`
- **Para qué:** campañas, flows, segmentos, perfiles, métricas, plantillas de email, catálogo. Reportes de campaña/flow.
- **Cuándo usarla:** análisis de email (revenue por flow, aperturas), crear borradores de campañas/plantillas, revisar segmentos.
- **Cuándo NO:** enviar campañas o suscribir/desuscribir perfiles sin confirmación.
- **Estado:** ⚪ por verificar cuenta conectada.

---

## G. Productividad / documentos
| Herramienta | MCP | Para qué | Estado |
|---|---|---|---|
| Google Drive | `mcp__claude_ai_Google_Drive__*` | Leer/crear archivos, buscar reportes, planillas de negocio | ⚪ |
| Gmail | `mcp__claude_ai_Gmail__*` | Buscar/triage de correos (proveedores, marketplaces, clientes) — borradores, no enviar solo | ⚪ |
| Google Calendar | `mcp__claude_ai_Google_Calendar__*` | Calendario comercial (eventos, lanzamientos, CyberDay) | ⚪ |
| Microsoft 365 | `mcp__claude_ai_Microsoft_365__*` | SharePoint/Outlook si el negocio usa ecosistema Microsoft | ⚪ |

---

## H. Creatividades / contenido (para ads y fichas de producto)
| Herramienta | MCP | Para qué | Estado |
|---|---|---|---|
| Canva | `mcp__claude_ai_Canva__*` | Diseños, brand templates, exportar piezas | ⚪ |
| Adobe Express / Firefly | `mcp__claude_ai_Adobe_for_creativity__*` | Edición de imagen, fondos, diseños de marketing | ⚪ |
| Higgsfield | `mcp__claude_ai_Higgsfield__*` | Generación de imagen/video para ads y social | ⚪ |

---

## I. Infraestructura / despliegue
| Herramienta | MCP | Para qué | Estado |
|---|---|---|---|
| Vercel | `mcp__claude_ai_Vercel__*` | Desplegar el **dashboard** de control (frontend) | ⚪ |

> Arquitectura objetivo (PDF): agente always-on en **Railway**, dashboard en **Vercel**, repo en **GitHub**. Credenciales como variables de entorno en cada plataforma, nunca en el repo.

---

## J. Multivende — API propia (en implementación)
- **Tipo:** API REST OAuth2 ("Multivende Integration Services"). Sin MCP; se consume con script en `scripts/` (o MCP propio en fase 2).
- **Para qué:** leer pedidos/stock/precios/productos de **todos los marketplaces de Chile** (centralizados aquí) + boletas. Vía de conciliación multicanal.
- **Setup:** cuenta dev → registrar app (scopes + redirect + webhooks) → token en `secrets/`. Detalle en `MULTIVENDE.md`.
- **Cuándo NO:** escribir stock/precios sin confirmación.
- **Estado:** 🟡 API confirmada, falta crear app y token.

## K. Redes sociales — orgánico (vía Windsor.ai + Meta)
- **Conectores Windsor disponibles:** Instagram, Facebook Organic, TikTok Organic, YouTube, LinkedIn Organic (falta autorizarlos en la cuenta).
- **Meta:** páginas/IG vía `mcp__claude_ai_Facebook__ads_get_ig_*` / `ads_get_user_pages`.
- **Estado:** 🔴 por autorizar. Ver `SOCIAL.md`.

## L. Pendiente de conectar
- **Marketplaces CO/MX/PE** — los de Chile salen por Multivende; falta mapear los de otros países.
- **TikTok Ads** en Windsor (para consolidar spend).
- **ERP / facturación / contabilidad** — si existe, documentar aquí.
