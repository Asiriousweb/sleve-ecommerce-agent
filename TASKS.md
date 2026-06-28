# TASKS.md — Cola de tareas (mantiene el loop vivo)

> Regla de oro: una duda nunca detiene el loop. Se anota en BLOQUEADO, se avisa, y se sigue con lo siguiente.
> Estados: BLOQUEADO (necesita decisión del usuario) · EN PROGRESO · PENDIENTE (puedo solo) · COMPLETADO (últimas 24-48h, luego se archiva).

---

## 🔴 BLOQUEADO (necesito decisión / datos del usuario)
- **Formato técnico del dashboard** — reporte del agente (HTML/MD) vs. web en Vercel vs. Looker Studio. (En consulta.)
- **Crear cuenta dev + app en Multivende** — requiere que el usuario la cree/autorice (OAuth2) para obtener token. Es el corazón de la centralización.
- **Aprobar `.mcp.json` y `.claude/settings.json`** — bloqueados por seguridad; el usuario debe crearlos/aprobarlos.
- **Marketplaces CO/MX/PE** — listar y definir acceso (los de CL salen por Multivende).
- **Datos de negocio restantes** — best-sellers, márgenes meta, costos por producto, comisiones por canal, cuentas de redes sociales.

## 🟡 EN PROGRESO
- **Modelar Chile end-to-end** (país modelo, luego replicar a CO/MX/PE). Baseline B2C listo en CHILE.md. Falta: marketplaces (Multivende), B2B, social.

## 🔎 HALLAZGOS CHILE a profundizar (puedo solo, requieren tu ojo en algunos)
- Producto "sin título" con $8M y 0 pedidos en Shopify → investigar anomalía de catálogo.
- TikTok Ads convierte 0,43% (vs Google 1,98%, Meta 0,68%) → ¿aporta o quema? Decisión de inversión.
- Fuga de checkout: 77% de los que llegan a checkout no compran → revisar pagos/envío/fricción.
- UTMs sucios (klaviyo como cpc, fuentes duplicadas) → estandarizar para atribución correcta.
- Google Ads Chile: escala de spend/valor sospechosa → revisar config de conversiones.

## ⚪ PENDIENTE (puedo hacerlo solo cuando haya datos/accesos)
- Depurar cuentas de Meta Ads: identificar las válidas por país y marcar las basura ("NO USAR"/"ELIMINAR"/CLOSED).
- Conectar Meta Ads y TikTok Ads en Windsor.ai para consolidar todo el spend en un solo lugar.
- Completar `MARKETPLACES.md` con los marketplaces reales una vez el usuario los indique.
- Diseñar el primer set de métricas del dashboard (METRICS.md → DASHBOARD.md).
- Definir y documentar el cálculo de margen en DATA.md.
- Crear commands operativos: `/weekly-report`, `/audit`, `/diagnose`.
- Configurar canal de reporte (Telegram u otro) — ver nota abajo.

## ✅ COMPLETADO (últimas 48h)
- **2026-06-27** — Estructura base del agente creada (carpetas + 13 archivos base + TOOLS/SOURCES con MCPs reales).
- **2026-06-27** — Archivos de proyecto: MARKETPLACES, CHANNELS, MULTIVENDE, METRICS, CUSTOMER-SERVICE, **SOCIAL, DASHBOARD**.
- **2026-06-27** — Primer command `/morning-brief`.
- **2026-06-27** — Verificadas integraciones (Shopify 🟢, Klaviyo 🟢, Meta 🟡, Windsor 🟡) y poblados archivos con datos reales (SLEVE Mobile, CL/CO/MX/PE).
- **2026-06-27** — Confirmada API de Multivende (OAuth2). Aclarada estructura multi-tienda Shopify + B2B aparte. Redes sociales al scope. Dashboard estructurado.
- **2026-06-27** — Modelo Chile con baseline real (CHILE.md). Ecosistema documentado (ECOSYSTEM.md): Multivende master de producto/precio/stock; GA4 fuente primaria; Metricool redes.
- **2026-06-27** — ✅ **Telegram operativo** (bot creado, mensaje de prueba OK).

---
> Nota: el PDF propone Telegram como canal de reporte asíncrono. Confirmar con el usuario si quiere Telegram u otro (WhatsApp, email, Slack). Ver PLAYBOOK.md → "Canal de reporte".
