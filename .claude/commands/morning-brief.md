# morning-brief

## Objetivo
Generar el resumen ejecutivo de inicio del día: ventas de ayer, ads, stock crítico, customer service y las urgencias que requieren atención.

## Inputs
- `HEARTBEAT.md` (qué fuentes están operativas), `TASKS.md`, `MEMORY.md`.
- Ventas de ayer: Shopify (sitio) + marketplaces (Multivende/Windsor).
- Ads de ayer: gasto y ROAS/MER (Meta/Google/TikTok vía Windsor).
- Stock crítico (Multivende/Shopify) y customer service pendiente.

## Pasos
1. **Observar:** leer HEARTBEAT, TASKS, MEMORY. Si una fuente está ROTA, seguir con lo disponible.
2. Traer ventas de ayer por canal y comparar con día y semana previa.
3. Traer gasto + ROAS/MER de ads; marcar anomalías (gasto alto, ROAS bajo).
4. Revisar quiebres de stock de productos clave.
5. Revisar customer service pendiente y SLA en riesgo.
6. **Pensar:** priorizar las 3-5 urgencias del día (lo que mueve dinero primero).
7. **Actuar:** redactar el brief. Lo sensible (decisión/dinero) → BLOQUEADO en TASKS.md + aviso.
8. **Registrar:** guardar output y nota en `memory/`.

## Output esperado
Archivo `output/reportes/YYYY-MM-DD-morning-brief.md` y resumen en pantalla:
- 🔴 **Urgencias / decisiones** (arriba)
- 📊 **Métricas clave** (ventas, ads, conversión) con comparación
- 📦 **Stock crítico**
- 💬 **Customer service**
- ✅ **Recomendaciones priorizadas** (impacto estimado)
