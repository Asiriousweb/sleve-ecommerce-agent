# CUSTOMER-SERVICE.md — Atención al cliente

Cómo el agente apoya el customer service de SLEVE: detección, triage, borradores de respuesta y SLA. Aplica a consultas de sitio propio y de cada marketplace.

> 🚧 Borrador — definir herramientas y políticas con el usuario.

## Alcance del agente en CS
- **Detectar** consultas/reclamos pendientes y priorizarlos (monto, antigüedad, riesgo de mala reseña).
- **Triage:** clasificar por tipo (despacho, producto, devolución, garantía, facturación, pre-venta).
- **Borradores de respuesta** según tono SLEVE (ver SOUL.md) — el agente NO envía solo (ver CLAUDE.md §5).
- **Vigilar SLA** y reputación por marketplace.
- **Detectar patrones:** si muchos reclaman lo mismo (un producto, un quiebre, un despacho), levantar bandera.

## Herramienta: Gorgias (centralizado) — confirmado 2026-06-28
SLEVE centraliza todo el customer service en **Gorgias**. Gorgias unifica los canales (email/chat del sitio, marketplaces, redes, WhatsApp) en una sola bandeja con tickets y SLA. El agente se conectará a Gorgias **directo (API key)** — pendiente que el usuario entregue la key.

| Canal | Llega a Gorgias vía | Estado |
|---|---|---|
| Sitio propio | Email / chat / formulario | 🔴 (falta API key de Gorgias) |
| Marketplaces | Integraciones de Gorgias | 🟡 |
| Redes / WhatsApp | Integraciones de Gorgias | 🟡 |

## Tipos de caso y manejo base
- **Estado de pedido / despacho:** consultar Multivende/canal → responder con tracking.
- **Devolución / garantía:** aplicar política → borrador con pasos.
- **Pre-venta (stock, specs):** consultar catálogo → responder y, si hay intención, sugerir cierre.
- **Reclamo / mala experiencia:** priorizar, tono empático, escalar a usuario si implica compensación (= dinero → confirmación).

## SLA objetivo
- ❓ Definir tiempo de respuesta objetivo por canal (los marketplaces penalizan la demora).

---
### 📋 Necesito del usuario
1. ¿Dónde llegan hoy las consultas (correo, Zendesk, paneles de marketplace, WhatsApp)?
2. Políticas de devolución/garantía/cambios (para los borradores).
3. SLA objetivo y quién atiende hoy.
4. ¿Quieres que el agente solo prepare borradores, o también priorice/clasifique el backlog?
