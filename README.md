# Agente SLEVE de E-commerce

Agente operativo que centraliza y hace más eficiente cada arista del comercio online de SLEVE: venta, ads/performance, sitio propio (B2C/B2B), marketplaces multi-país, el centralizador Multivende y customer service. Detecta problemas y urgencias, y convierte el análisis disperso en acción.

## Estado
🟡 En construcción (v0.1.0 — 2026-06-27). Estructura base lista; pendiente completar datos de negocio y conectar fuentes. Ver `TASKS.md`.

## Cómo arrancar
1. Abrir esta carpeta en Claude Code.
2. El agente lee `CLAUDE.md` automáticamente (system prompt + ciclo Observar→Pensar→Actuar).
3. Revisar `HEARTBEAT.md` (qué está operativo) y `TASKS.md` (qué sigue).

## Slash commands
- `/morning-brief` — resumen ejecutivo de inicio del día (ventas, ads, stock, urgencias).
- _(próximos: `/weekly-report`, `/diagnose`, `/audit`)_

## Requisitos / integraciones
- **MCPs:** Shopify, Meta/Facebook Ads, Windsor.ai (multicanal), Klaviyo, Google Drive/Gmail, Vercel. Ver `TOOLS.md`.
- **Pendiente:** integración con Multivende y marketplaces latam. Variables/credenciales en `secrets/` (nunca a GitHub).

## Estructura
```
.claude/        commands/ y skills/ + settings.json
memory/         notas diarias (+ archive/)
output/         reportes/ analisis/ exports/ drafts/
scripts/        automatizaciones (sync, APIs)
secrets/        credenciales (gitignored)

ARCHIVOS BASE:  README, CLAUDE, SOUL, IDENTITY, CONTEXT, TOOLS,
                SOURCES, DATA, HEARTBEAT, MEMORY, TASKS, PLAYBOOK, CHANGELOG
PROYECTO:       MARKETPLACES, CHANNELS, MULTIVENDE, METRICS, CUSTOMER-SERVICE
```

## Principio
Observar → Pensar → Actuar → Registrar. El agente nunca actúa a ciegas y nunca se rompe en silencio. Lo sensible (dinero, publicar, borrar, precios) siempre se confirma con el usuario.
