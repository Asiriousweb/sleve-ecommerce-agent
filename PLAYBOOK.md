# PLAYBOOK.md — SOPs y procesos paso a paso

Procesos recurrentes del Agente SLEVE. El agente los sigue sin instrucciones adicionales. Cada proceso: nombre, frecuencia, trigger, inputs, pasos, output y manejo de errores.

> 🚧 Versión inicial. Los SOPs se afinan a medida que se conectan las fuentes reales.

---

## SOP 1 — Morning Brief (diario)
- **Frecuencia:** diaria, al inicio del día. También invocable con `/morning-brief`.
- **Trigger:** inicio de sesión matinal o command.
- **Inputs:** HEARTBEAT.md, ventas de ayer (Shopify + marketplaces vía Windsor/Multivende), gasto de ads, stock crítico, tickets de customer service.
- **Pasos:**
  1. OBSERVAR — leer HEARTBEAT, TASKS, MEMORY.
  2. Traer ventas de ayer por canal y compararlas con el día/semana previa.
  3. Traer gasto y ROAS/MER de ads de ayer; marcar anomalías.
  4. Revisar quiebres de stock de productos clave.
  5. Revisar customer service pendiente / SLA en riesgo.
  6. PENSAR — priorizar las 3-5 urgencias del día.
  7. ACTUAR — generar el brief; lo sensible va a BLOQUEADO + aviso.
  8. REGISTRAR — guardar en `output/reportes/YYYY-MM-DD-morning-brief.md` y nota en `memory/`.
- **Output:** resumen ejecutivo: urgencias arriba, métricas clave, recomendaciones priorizadas.
- **Errores:** si una fuente no responde → marcar en HEARTBEAT, reportar el brief con lo disponible y señalar el hueco.

---

## SOP 2 — Reporte semanal (semanal)
- **Frecuencia:** semanal (lunes). Invocable con `/weekly-report`.
- **Pasos:** ventas por canal/país/producto vs. semana anterior; ROAS/MER por plataforma; top y bottom productos; quiebres recurrentes; salud de pricing vs. competencia; resumen de customer service. Cierra con 3 recomendaciones priorizadas.
- **Output:** `output/reportes/YYYY-MM-DD-weekly.md`.

---

## SOP 3 — Diagnóstico de problema (on-demand)
- **Frecuencia:** on-demand. Invocable con `/diagnose [tema]`.
- **Pasos:** acotar el problema → traer los datos relevantes de la(s) fuente(s) correcta(s) → analizar causa raíz → proponer fixes priorizados por impacto/esfuerzo.
- **Output:** `output/analisis/YYYY-MM-DD-diagnostico-[tema].md`.

---

## SOP 4 — Conciliación multicanal (semanal/quincenal)
- **Objetivo:** que las ventas cuadren entre marketplace ↔ Multivende ↔ boleta. Detectar pedidos sin boleta, stock descalzado, comisiones mal cobradas.
- **Pasos:** extraer pedidos de cada canal y de Multivende → cruzar por SKU/orden → listar discrepancias → priorizar las de mayor monto.
- **Output:** `output/analisis/YYYY-MM-DD-conciliacion.md`.
- _(Requiere acceso a Multivende — ver TASKS.md.)_

---

## Manejo de errores y fallos
Regla: **nunca romperse en silencio.**
1. Detectar el error y registrarlo en HEARTBEAT.md (componente ROTO/DEGRADADO).
2. Avisar al usuario con el contexto del fallo.
3. Dejar la tarea afectada en BLOQUEADO en TASKS.md.
4. Avanzar en las demás tareas posibles.
5. Reintentar cuando corresponda o esperar decisión.

---

## Canal de reporte (asíncrono) — Telegram
Canal elegido: **Telegram** (script `scripts/telegram_notify.py`, sin dependencias). La regla de los dos destinos: toda pregunta/bloqueo va **a TASKS.md Y a Telegram**, nunca solo al IDE.

### Setup (una vez)
1. En Telegram, hablar con **@BotFather** → `/newbot` → elegir nombre y usuario → copiar el **token**.
2. `cp secrets/.env.example secrets/.env` y pegar el token en `TELEGRAM_BOT_TOKEN`.
3. Escribirle algo al bot (presionar **Start**).
4. `python3 scripts/telegram_notify.py --get-chat-id` → copiar el `chat_id` a `TELEGRAM_CHAT_ID` en `secrets/.env`.
5. `python3 scripts/telegram_notify.py --test` → debe llegar el mensaje de prueba.

### Uso por el agente
- Enviar aviso: `python3 scripts/telegram_notify.py "texto"` o `from telegram_notify import send_message`.
- Qué se avisa: algo roto, decisión necesaria, urgencia de negocio. Se acumulan: completadas, hallazgos, síntesis nocturna. Nunca molesta: rutina OK, logs, auto-mantenimiento.
- Verificación de envío: si el envío falla, registrar en HEARTBEAT y reintentar; nunca asumir que llegó.
> Control bidireccional completo (mandar comandos al agente por Telegram) llega con el despliegue always-on (Railway). Por ahora: agente → usuario + lectura de respuestas con `--get-chat-id`/getUpdates.

---

## Loop de optimización nocturna (macro-ciclo)
Mecanismo de automejora. 10 sesiones aisladas, una cada 20 min desde la 1:00 AM. Cada una audita un archivo, aplica fixes y registra en `memory/`.

| Sesión | Hora | Archivo | Audita |
|---|---|---|---|
| 1 | 1:00 | SOUL.md | Valores siguen alineados |
| 2 | 1:20 | IDENTITY.md | Rol y mandato correctos |
| 3 | 1:40 | CONTEXT.md | Info desactualizada/faltante |
| 4 | 2:00 | TOOLS + SOURCES + DATA | Herramientas, fuentes, estructura |
| 5 | 2:20 | HEARTBEAT.md | Semáforo con estado real |
| 6 | 2:40 | MEMORY.md + proyecto | Consolidar memoria y archivos propios |
| 7 | 3:00 | PLAYBOOK.md | SOPs rotos/desactualizados |
| 8 | 3:20 | memory/*.md | Extraer aprendizajes clave |
| 9 | 3:40 | skills/ + ORDEN | Skills y reorganización |
| 10 | 4:00 | Síntesis | Reporte ejecutivo de la noche |

**Prompt base por sesión:** Observar (leer archivo + relación con otros) → Pensar (detectar desactualizado/roto/duplicado, lugar y nombre correctos) → Actuar (aplicar fixes, eliminar duplicados, reorganizar, guardar resumen en `memory/YYYY-MM-DD.md`). Reportar: qué encontró, qué cambió y por qué, qué queda pendiente, qué priorizar.

**Sesión 10 (síntesis):** leer todas las notas de la noche y producir reporte ejecutivo (estado del sistema, cambios aplicados, problemas pendientes, top 3 mejoras, próximas acciones) en `memory/YYYY-MM-DD-sintesis.md`.

**Reglas:** cada sesión es aislada, DEBE editar (no solo analizar), elimina duplicados, mantiene el orden, audita base y proyecto, documenta lo que está OK como verificado, y el loop se reprograma para la noche siguiente.
> ⚠️ Pendiente: agendar el loop (requiere agente always-on / cron).
