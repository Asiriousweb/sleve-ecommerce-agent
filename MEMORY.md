# MEMORY.md — Memoria acumulada de largo plazo

> Memoria del agente: decisiones, hallazgos, errores y aprendizajes. Se consulta para no repetir errores y mantener coherencia entre sesiones. Se consolida desde `memory/YYYY-MM-DD.md` (notas diarias).

---

## Decisiones tomadas
- **2026-06-27** — Se adopta la "Estructura Universal de Agente" (PDF) como base del Agente SLEVE. Razón: marco probado del agente anterior del usuario; da memoria persistente, loop de automejora y operación autónoma.
- **2026-06-27** — Windsor.ai se designa como **centralizador de datos** (325+ conectores) para consolidar ventas + ads + analytics multicanal. Razón: cubre la mayoría de plataformas sin un MCP por cada una.

## Hallazgos
- **2026-06-27** — Gap crítico: no hay MCP directo para Multivende ni para marketplaces latam. La centralización depende de resolver ese acceso (API/CSV/Windsor).

## Errores y soluciones
- **2026-06-27** — `.mcp.json` y `.claude/settings.json` bloqueados por el clasificador de auto-mode (son autoconfiguración del harness). Solución: el usuario los aprueba/crea manualmente. (Esperado, no es un fallo del diseño.)

## Pendientes con contexto
- Completar `CONTEXT.md` (qué vende SLEVE, países, marketplaces, B2C/B2B).
- Definir integración Multivende.
- Verificar MCPs realmente conectados.

## Acuerdos y compromisos
- _(vacío)_

---
> Categorías: Decisiones · Hallazgos · Errores y soluciones · Pendientes · Acuerdos. El loop nocturno consolida aquí lo aprendido en `memory/`.
