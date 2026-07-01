# CHANGELOG.md — Historial de cambios del agente

## 2026-06-30/07-01 (sesión 19b) — fixes ML + zona horaria + refresh completo
- **`/refresh?full=1`**: invalida cachés diarios (30d/mes/yoy/catálogo/productos) para reflejar fuentes recién conectadas sin esperar al recálculo diario.
- **Mercado Libre robusto**: `_meli_get` con reintentos/backoff ante rate limit (429/5xx) → paginado no se corta en bursts.
- **Zona horaria**: los cortes de período se anclan a **hora de Chile** (`_hoy_local`, America/Santiago, fallback UTC-4). Arreglaba "este mes" que a fin de mes UTC saltaba a julio antes que en Chile.
- Verificado: 7d/30d/mes con ML en los 3 países; "este mes" = junio (968 ped ML Chile), ya no 8.

## 2026-06-30 (sesión 19) — Mercado Libre directo, MCP, períodos unificados + barrido de .md
- **Período = filtro global**: `build_overview(periodo)` parametriza TODAS las fuentes por rango → `overview.periodos` {7d, 30d, mes} con estructura COMPLETA idéntica (cacheo 1×día los pesados). El dashboard ya no "secuestra" la pantalla por período; todas las pestañas navegables en cualquier rango, solo cambian valores. YoY = dataset 30d + badges de crecimiento.
- **Mercado Libre directo (OAuth, gratis, una app por país)**: `meli_oauth.py` (authorization_code + refresh 6h, credenciales `MELI_CLIENT_ID_CL/CO/MX/PE`, verifica país de la cuenta, botón desconectar) + `pull_meli` (ventas+pedidos+publicaciones) → `paises[].meli`; rutas /meli·/install·/callback·/disconnect; dashboard Canales → "Mercado Libre (directo)". **Conectados CL+MX+PE; CO falta verificación de cuenta en ML.** Reemplaza Nubimetrics (~$320/mes).
- **MCP remoto read-only**: `mcp_remote.py` (JSON-RPC en POST /mcp, sin deps) → **https://mcp-ecommerce.slevemobile.com** (SSL Let's Encrypt, auth por `MCP_TOKEN` header o `?token=`). 7 tools de lectura. Validado end-to-end.
- **Nuevas pestañas/datos**: Publicaciones (completitud fichas Shopify), Tendencias (Google Trends RSS), Productos top (line items Shopify), Venta por canal (share GA4 × venta real → cuadra). Acciones data-driven.
- **Cuadratura**: conversión con pedidos Shopify (≈ Shopify, no GA4) + `gap_tracking`.
- **Regla #1** reforzada (CLAUDE.md + memoria): accesos de escritura abiertos, agente read-only por defecto; toda modificación pasa por proponer→confirmar→ejecutar.
- **Barrido de .md**: CONNECTIONS, SOURCES, TOOLS, MARKETPLACES, DASHBOARD, TASKS actualizados al estado real (todo directo, Windsor retirado).

## 2026-06-29 (sesión 18) — Meta Ads DIRECTO (Marketing API)
- Meta conectado **directo (gratis)** vía System User token (Business Manager, acceso total) en `META_TOKEN`. App "SLEVE Agent" creada (sin publicar, modo dev — suficiente para datos propios; NO requiere verificación/review).
- `refresh.py` → `pull_meta()`: descubre las cuentas del token (me/adaccounts), omite "NO USAR"/"ELIMINAR", trae gasto (insights spend) por país. 3 cuentas con gasto (CL/CO/PE).
- ⚠️ Pendiente: **normalizar moneda** (Meta CL en USD, ventas en CLP, etc.) para MER/ROAS consolidado correcto. Hoy el gasto entra en su moneda cruda.

## 2026-06-29 (sesión 17) — Shopify DIRECTO multi-tienda + cuadratura operativa
- Shopify conectado **directo y gratis** (sin Windsor) vía **OAuth multi-tienda**: instalador en el robot (`/shopify` lista las 6 tiendas, `/shopify/install`, `/shopify/callback`), token por tienda en el volumen.
- Nota: el dev dashboard nuevo de Shopify deprecó las "custom apps heredadas" (no se crean desde ene-2026); el "token de automatización" da 401 → la vía correcta es OAuth install (lo automaticé en el robot).
- 6 tiendas conectadas (CL, CL B2B, CO, MX, PE, EEUU). Ventas reales por país: Chile $8,2M/233 ped, Colombia $4,9M/34, Perú/3, MX y EEUU en 0.
- **Cuadratura GA4↔Shopify operativa** (SOP 4): GA4 ≤ Shopify en todos ✅. Endpoint `/refresh` para forzar actualización.
- Criterio de costo aplicado: Shopify directo+gratis; GA4/Google/SearchConsole quedan en Windsor (directo es más enredo).

## 2026-06-28 (sesión 16) — Dashboard con datos en vivo (círculo cerrado)
- `refresh.py` ahora **agrega KPIs por país** (GA4: sesiones/transacciones/conversión/tráfico; Google Ads: gasto/ROAS) + consolidado.
- Dashboard lee `/api/overview` en vivo (fetch cliente, fallback a baseline): conversión, sesiones y fuentes de tráfico reales + badge "🟢 En vivo". Ventas $/top productos siguen baseline hasta conectar Shopify al robot.
- Verificado en vivo por país: Chile 26.832 ses (0,6%), Colombia 2.053 (1,61%), México 99 (0%), Perú 305 (0,98%).

## 2026-06-28 (sesión 15) — ¡DATA VIVA funcionando!
- `WINDSOR_API_KEY` puesta en el robot (Railway) + dominio público generado.
- Corregido el endpoint Windsor (conector en la ruta). Verificado en vivo: `/api/overview` devuelve `fuente: windsor (en vivo)` con GA4 + Google Ads reales de los 4 países, refrescando cada 2h.
- URL del robot: https://sleve-ecommerce-agents-production.up.railway.app
- Siguiente: refresh.py debe **calcular KPIs reales** (por país/canal) en vez de baseline + raw; luego el dashboard lee `/api/overview` en vivo.

## 2026-06-28 (sesión 14) — Loop de datos cada 2h (pipeline)
- Definida la regla: **directo por defecto, Windsor para lo que no se pueda** (Meta hoy por Windsor por el rollout). Cadencia elegida: **cada 2h**.
- Clave: el robot always-on usa SUS PROPIAS llaves (no los MCPs de la sesión Claude). **WINDSOR_API_KEY = una llave para todas las fuentes Windsor.**
- Construido `agent/refresh.py` (trae data → escribe `DATA_DIR/overview.json`; hooks Windsor listos, baseline como placeholder) + `run_railway.py` ahora agenda refresh **cada 2h** y sirve **`GET /api/overview`** (CORS) para el dashboard. Probado: genera overview.json OK.
- Pendiente: el usuario consigue la **Windsor API key** (y luego Shopify/Klaviyo/Multivende) → datos reales en vivo. Luego: dashboard leyendo `/api/overview`.

## 2026-06-28 (sesión 13) — Robot E-commerce LIVE en Railway
- Servicio E-commerce creado en el proyecto Railway `Sleve_Agents` (hermano del Trade) y respondiendo: `/ping` → `pong ✅ (ecommerce)`. Robot always-on confirmado.

## 2026-06-28 (sesión 12) — Dashboard LIVE en Vercel
- Dashboard desplegado y funcionando en Vercel. 🎉
- Fix de deploy: Vercel detectaba el monorepo como Python; solución → Next.js **export estático** (`output: export` + `images.unoptimized`) + **vercel.json en la raíz** (installCommand/buildCommand a `dashboard/`, outputDirectory `dashboard/out`, framework null), con **Root Directory vacío**.
- ✅ Subdominio **https://ecommerce.slevemobile.com** en línea con SSL (CNAME en GoDaddy → Vercel, verificado HTTP 200).
- Pendiente: datos en vivo + logo oficial.

## 2026-06-28 (sesión 11) — Agente E-commerce alineado al patrón Trade
- Estudiado el repo de referencia `Sleve-Trade-Marketing` (Python+Docker+DuckDB+Anthropic API+MCP+Vercel, supervisor `run_railway.py`).
- Decisión (usuario): el agente E-commerce será un **servicio nuevo dentro del proyecto Railway `Sleve_Agents`** (hermano del Trade), desde el repo `sleve-ecommerce-agent`.
- Reestructurado `agent/` al molde Trade: `run_railway.py` (supervisor) · `bot.py` (Telegram) · `orchestrator.py` (cabeza) · `specialists.py` (6 dominios) · `db.py` (DuckDB/volumen) · `mcp_server.py` (read-only, gateado). + `Dockerfile`, `.dockerignore`, `requirements.txt` en raíz.
- Eliminados los archivos de la Fase 1 (Procfile/runtime/railway.json/main.py). Probado: el `/brief` consolida los 6 especialistas.

## 2026-06-28 (sesión 10) — Repo Git inicializado
- `git init` + primer commit (56 archivos) en `main`. Verificado que `secrets/` queda fuera (gitignore OK).
- Monorepo: raíz (cerebro + .md + .claude/agents) · `dashboard/` → Vercel · `agent/` → Railway.
- Pendiente: crear repo en GitHub (privado) y push; luego conectar Vercel y Railway al repo.

## 2026-06-28 (sesión 9) — Servicio always-on para Railway
- Creado `agent/` (servicio Python sin dependencias): listener Telegram long-polling + health HTTP ($PORT) + comandos `/brief /estado /ping /help`. Solo responde al chat autorizado.
- Config Railway: Procfile, railway.json, runtime.txt, requirements.txt, README con deploy paso a paso (CLI o GitHub) y variables de entorno.
- Probado local OK: health responde, recibe y responde comandos de Telegram en vivo.
- Fase 2 pendiente: conectar cerebro (Claude Agent SDK) en `handle_command()` para análisis en vivo y lenguaje natural.

## 2026-06-28 (sesión 8) — Arquitectura multi-agente
- Definida la arquitectura: **SLEVE = orquestador** que delega en especialistas (idea del usuario para acotar contexto por dominio y escalar a 4 países).
- Creado **AGENTS.md** (organigrama) y 8 subagentes en `.claude/agents/`: performance-ads, marketplaces, organico-descubribilidad, tienda-cro, inteligencia-tendencias, social-contenido, retencion-crm, customer-service (este último mapeado, pendiente).
- CLAUDE.md: agregado el rol de orquestador (Observar → Delegar → Sintetizar → Decidir).
- Customer service: confirmado centralizado en **Gorgias** (conector disponible en Windsor, link enviado). Actualizados customer-service.md, CUSTOMER-SERVICE.md, AGENTS.md, SOURCES, HEARTBEAT, ECOSYSTEM.

## 2026-06-27 (sesión 7) — Dashboard web v0.1
- Decisión: dashboard = **web propia** (Next.js → Vercel, API → Railway), estética dark cockpit (referencia: panel Trade Marketing del usuario).
- Construido `dashboard/` (Next.js 14.2.35 + Tailwind + Recharts): header, selector país/semana, tabs, 4 KPI cards, barra de urgencias, tendencia (unidades + $), venta por canal, ROAS por plataforma, top productos, fuentes de tráfico.
- Datos cableados con el baseline real de Chile en `lib/data.ts` (marketplaces/ads/social en demo).
- ✅ `npm run build` compila sin errores. Next fijado a 14.2.35 (parche de seguridad).

## 2026-06-27 (sesión 6) — Canal Telegram
- Creado `scripts/telegram_notify.py` (sin dependencias: envío + descubrir chat_id) y `secrets/.env.example`.
- Documentado setup en PLAYBOOK (BotFather), TOOLS, HEARTBEAT. Validada sintaxis y manejo de errores.
- ✅ **Telegram operativo**: bot creado por el usuario, chat_id 920578167 guardado en `secrets/.env`, mensaje de prueba enviado OK.

## 2026-06-27 (sesión 5) — Modelo completo de plataformas
- Documentada la arquitectura del ecosistema en **ECOSYSTEM.md**: Multivende centraliza inventario y lo dispara a Shopify + 5 marketplaces 3P (Falabella, Walmart, Ripley, París, MercadoLibre); **GA4 = fuente primaria de analytics**; advertising (Klaviyo, Meta, Google, TikTok + SEO/Search Console); social vía **Metricool**.
- MARKETPLACES.md, CHILE.md, CHANNELS.md actualizados con los marketplaces reales (todos vía Multivende).
- SOURCES.md: GA4 marcada como fuente primaria; Metricool agregada (conector Windsor disponible).
- SOCIAL.md: Metricool como fuente de redes.

## 2026-06-27 (sesión 4) — Modelo Chile + baseline real
- Decisión: **Chile = país modelo**, se completa end-to-end y luego se replica (CO/MX/PE).
- Smoke test ampliado con datos reales de Chile: Shopify (ventas 30d, top productos, embudo) + GA4 (fuentes de tráfico).
- Creado **CHILE.md** (modelo maestro replicable + baseline 30d + hallazgos).
- CONTEXT.md: catálogo real (audio/powerbanks/parlantes; best-seller Pulse ANC 2Gen).
- Hallazgos registrados (TikTok ineficiente, fuga de checkout 77%, producto sin título $8M, UTMs sucios).

## 2026-06-27 (sesión 3) — Multivende API, multi-tienda, redes sociales y dashboard
- Confirmado vía WebSearch que **Multivende tiene API REST OAuth2** (MIS). MULTIVENDE.md actualizado con pasos de integración (cuenta dev, app, scopes/webhooks).
- Aclarado con el usuario: **Shopify es multi-tienda** (CL/PE/CO/MX) **+ Chile B2B en tienda aparte**. Todos los marketplaces de Chile van por Multivende. CHANNELS.md y CONTEXT.md actualizados.
- **Redes sociales** sumadas al scope (agente e-commerce completo): creado SOCIAL.md, IDENTITY y TOOLS actualizados (conectores orgánicos de Windsor + Meta).
- Creado **DASHBOARD.md**: estructura en 8 capas + barra de urgencias, MVP construible y opciones de formato técnico.

## 2026-06-27 (tarde) — Verificación de integraciones
- Verificadas 4 integraciones MCP con llamadas de lectura: **Shopify 🟢**, **Klaviyo 🟢**, **Meta Ads 🟡**, **Windsor.ai 🟡** (Google Ads + GA4 + Search Console, CL/CO/MX/PE).
- Descubierto el negocio real: SLEVE Mobile, electrónica, opera en Chile/Colombia/México/Perú, Shopify Plus.
- Actualizados con datos reales: HEARTBEAT, CONTEXT, SOURCES, IDENTITY, MARKETPLACES.
- Hallazgo: desorden de cuentas en Meta Ads (varias "NO USAR"/"ELIMINAR"/CLOSED).

## 2026-06-27 (mañana) — Estructura inicial
- **Versión inicial 0.1.0 del Agente SLEVE de E-commerce.**
- Creada estructura de carpetas base: `.claude/{commands,skills}`, `memory/archive`, `output/{reportes,analisis,exports,drafts}`, `scripts/`, `secrets/tokens`.
- Escritos archivos base: README, CLAUDE, SOUL, IDENTITY, CONTEXT, TOOLS, SOURCES, DATA, HEARTBEAT, MEMORY, TASKS, PLAYBOOK, CHANGELOG.
- TOOLS.md y SOURCES.md poblados con los MCPs reales disponibles (Shopify, Meta Ads, Windsor.ai, Klaviyo, Google, Vercel, Canva/Adobe/Higgsfield).
- Archivos de proyecto creados: MARKETPLACES, CHANNELS, MULTIVENDE, METRICS, CUSTOMER-SERVICE.
- Primer slash command: `/morning-brief`.
- `.gitignore` creado. `.mcp.json` y `.claude/settings.json` quedaron pendientes de aprobación del usuario (bloqueados por el clasificador de seguridad).
- Pendiente: completar CONTEXT.md con datos de negocio, definir acceso a Multivende/marketplaces, configurar canal de reporte y loop nocturno.

## Loop nocturno 2026-07-01
- Actualicé HEARTBEAT.md con la fecha del último snapshot (2026-07-01) y añadí un bloque de estado 7d con las cifras consolidadas en vivo (venta sitio, Mercado Libre, total, ad spend, MER, ROAS, conversión y cuadratura Chile). Actualicé la línea de 'Loop datos en vivo' y la de Mercado Libre para reflejar los números frescos del snapshot. Fui conservador: no toqué el resto de documentos porque están coherentes y al día.
- Archivos optimizados: HEARTBEAT.md

## Loop nocturno 2026-07-01
- Actualicé HEARTBEAT.md con el snapshot en vivo más reciente (overview.json del 2026-07-01T04:49Z): nuevos números 7d de venta sitio ($10.078/264 pedidos), Mercado Libre ($20.000/667/142 pubs), venta total ($30.078/931), ad spend ($3.734, Meta $3.339), MER sitio 2,7 / Meta 3,02 / total 8,06, sesiones 30.096, conversión 0,57%, y Chile (27.280 sesiones, GA4 132 ↔ Shopify 223, gap 91, $8.500 USD / $7.843.785 CLP, AOV $35.174). También ajusté los números por componente (Shopify, Meta, GA4, Mercado Libre) y el timestamp del último snapshot. El resto de los .md están consistentes y no requieren cambios.
- Archivos optimizados: HEARTBEAT.md
