# SOCIAL.md — Redes sociales

Análisis de redes sociales de SLEVE Mobile como parte del agente e-commerce completo: desempeño orgánico, engagement, crecimiento de comunidad, social commerce y su aporte a la venta. Los ads pagados de Meta/TikTok viven en el eje de Performance (ver METRICS.md); aquí el foco es **orgánico + comunidad + contenido**.

> 🚧 Borrador — confirmar cuentas y prioridades con el usuario.

## Fuentes de redes (2026-07-01) — regla: directo = verdad, Metricool corrobora/rellena
- **IG/FB directo** (Meta Graph, owned_pages, System User token): seguidores + posts por país → **fuente de verdad** de seguidores.
- **YouTube directo** (Data API v3, API Key): suscriptores/vistas/videos top por país → **fuente de verdad** de YouTube.
- **Metricool** (`pull_metricool`, hub social): **engagement/alcance por post** de todas las redes (IG/FB/TikTok/YouTube B2C + LinkedIn corp) → complementa lo que el directo no da fácil, y cubre TikTok/LinkedIn/Threads donde no hay directo. Ver [[regla-fuentes-directo-vs-metricool]] (memoria).

| Red | Cuenta(s) | Estado | Datos |
|---|---|---|---|
| Instagram | @slevemobile (CL), @sleve.co, @sleve.mx, @sleve.pe | 🟢 directo | Seguidores + posts (CL ~61k, CO ~11k, PE ~2,6k, MX ~77) + engagement por post (Metricool) |
| Facebook | Páginas SLEVE por país | 🟢 directo | Seguidores (CL ~8,7k, CO ~2,7k, PE ~1,1k) + engagement por post (Metricool) |
| YouTube | @SleveXOficial (CL/CO/MX/PE) | 🟢 directo | Subs/vistas/videos top (CL 37/53.562, PE 3/1.567, CO/MX 0) |
| TikTok | @slevemobile.cl, etc. | 🟡 Metricool | Engagement por post (directo = trámite; Metricool por ahora) |
| LinkedIn | SLEVE {país} LINKEDIN (corp) | 🟡 Metricool | Posts corporativos B2B |
| Threads / X / Pinterest | slevemobile | 🟡 Metricool | Cobertura vía Metricool |

> **Hallazgo (2026-07-01):** el orgánico está concentrado en **Chile** (18 posts/7d, YouTube 53k vistas). CO/MX casi sin actividad orgánica (0 posts/7d, 0 subs). Palanca clara para crecer esos países.
> Dashboard: pestaña Redes muestra seguidores (Meta), engagement por post (Metricool) y YouTube. Próximamente en YouTube: retención/tiempo de reproducción (YouTube Analytics).

## Qué mide el agente
- **Crecimiento:** seguidores, alcance, impresiones por red y país.
- **Engagement:** likes, comentarios, compartidos, guardados; engagement rate.
- **Contenido:** posts/reels top y peores; formatos que funcionan; mejor horario.
- **Conversión social:** tráfico social → sesiones → venta (cruce con GA4/Shopify); social commerce (TikTok Shop, IG Shopping).
- **Comunidad / reputación:** menciones, sentimiento, consultas por DM (enlaza con CUSTOMER-SERVICE.md).
- **Competencia:** comparación de actividad/engagement vs. competidores (cuando se defina en COMPETITORS).

## Qué puede hacer el agente
- Analizar desempeño y detectar qué contenido convierte.
- Proponer calendario y borradores de contenido (no publica solo — ver CLAUDE.md §5).
- Generar creatividades con las herramientas disponibles (Canva, Adobe, Higgsfield) como borrador.
- Alertar caídas de alcance/engagement o crisis de reputación.

---
### 📋 Necesito del usuario
1. Handles/cuentas por red y país.
2. ¿Quién maneja redes hoy? ¿Hay calendario de contenido?
3. ¿Usan social commerce (TikTok Shop, IG/FB Shopping)?
4. Prioridad: ¿análisis, generación de contenido, o ambos?
