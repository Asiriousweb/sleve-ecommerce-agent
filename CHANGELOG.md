# CHANGELOG.md — Historial de cambios del agente

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
