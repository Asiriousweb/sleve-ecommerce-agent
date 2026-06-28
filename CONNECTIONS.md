# CONNECTIONS.md — Mapa de conexión de fuentes

Estado real de cada fuente de datos, qué falta y quién hace la acción. Es la "revisión de fuentes" previa al dashboard. **Estado:** 🟢 conectado y con datos · 🟡 conectado parcial · 🔴 falta conectar · ⚪ por verificar.

**Última revisión:** 2026-06-27 (re-chequeo Windsor: sin conectores nuevos aún)

## Cómo se conecta cada tipo de fuente
- **MCP nativo de Claude** (ya disponible porque la cuenta está conectada en Claude): Shopify, Meta/Facebook Ads, Klaviyo. No requiere acción extra.
- **Windsor.ai — vía link de aplicación web** (un clic, auto-login a la cuenta Windsor de SLEVE): Google Ads ✅, GA4 ✅, Search Console ✅ ya conectados. Faltan: Meta Ads, TikTok Ads, Metricool (redes) y Shopify multi-tienda → **links entregados por chat**.
- **API propia + app OAuth2 (Multivende):** crear cuenta dev → registrar app (scopes + redirect + webhooks) → token a `secrets/` → script en `scripts/`. Desbloquea los 5 marketplaces CL.
- **Marketplaces (Falabella/Walmart/Ripley/París/MercadoLibre):** NO se conectan directo → entran **por Multivende**.

| Fuente | Estado | Smoke test (2026-06-27) | Acción pendiente | Quién |
|---|---|---|---|---|
| **Shopify Chile (B2C)** | 🟢 | Shop info OK (Plus, CLP, sleve.cl) | — | — |
| **Shopify Perú/Colombia/México** | 🔴 | No extraídas | Re-autorizar cada tienda (`switch-shop`) o conectar Shopify en Windsor | Usuario (autoriza) |
| **Shopify Chile B2B** | 🔴 | No extraída (tienda aparte) | Igual que arriba | Usuario |
| **Google Ads (Windsor)** | 🟡 | ✅ Datos OK, pero solo Chile + Colombia con gasto últimos 7d; México y Perú sin datos | Revisar por qué MX/PE no reportan; revisar escala/conversiones de cuenta Chile | Agente revisa / Usuario confirma |
| **GA4 (Windsor)** | 🟢 | ✅ CL 25.036 ses · CO 1.880 · PE 300 · MX 92 | — (MX casi sin tráfico, ver hallazgos) | — |
| **Search Console (Windsor)** | 🟢 | Conectado (sleve.cl, slevemobile.cl) | Smoke test de queries orgánicas | Agente |
| **Meta Ads** | 🟡 | Cuentas listadas (MCP). Desorden de cuentas | (a) Limpiar cuentas; (b) **conectar en Windsor** para consolidar spend → link generado | Usuario (autoriza Windsor) |
| **TikTok Ads (Windsor)** | 🔴 | — | Autorizar en Windsor → link generado | Usuario |
| **Klaviyo** | 🟢 | Account details OK (cuenta Chile, CLP) | ¿Hay cuentas Klaviyo por país? | Usuario confirma |
| **Instagram orgánico (Windsor)** | 🔴 | — | Autorizar → link generado | Usuario |
| **Facebook orgánico (Windsor)** | 🔴 | — | Autorizar → link generado | Usuario |
| **TikTok orgánico (Windsor)** | 🔴 | — | Autorizar → link generado | Usuario |
| **YouTube (Windsor)** | 🔴 | — | Autorizar → link generado | Usuario |
| **Multivende (marketplaces CL)** | 🔴 | — | Crear cuenta dev + app OAuth2 (ver MULTIVENDE.md) | Usuario crea, Agente integra |
| **Marketplaces CO/MX/PE** | 🔴 | — | Listar y definir acceso | Usuario |
| **Customer service (Gorgias)** | 🔴 | — | Autorizar Gorgias en Windsor (link enviado) | Usuario autoriza |

## Links de autorización Windsor (entregados por chat 2026-06-27)
Generados para: Meta Ads, TikTok Ads, Instagram, Facebook orgánico, TikTok orgánico, YouTube. Son links de un solo uso con auto-login a la cuenta Windsor de SLEVE → **no se guardan en archivos** (contienen token). Si expiran, el agente los regenera con `get_connector_authorization_url`.

## Orden sugerido de conexión (mayor impacto primero)
1. **Meta Ads + TikTok Ads en Windsor** → consolida TODO el spend con Google (dashboard de Ads completo).
2. **Multivende** → desbloquea marketplaces de Chile (gran parte de la venta).
3. **Shopify multi-tienda** (PE/CO/MX + B2B) → venta consolidada real.
4. **Redes orgánicas** (IG/FB/TikTok/YouTube) → eje social.
5. **Customer service** → última capa.
