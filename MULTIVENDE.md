# MULTIVENDE.md — Centralizador Multivende

Multivende es el **centralizador** de SLEVE: conecta los canales (sitio propio + marketplaces), sincroniza stock y pedidos, y **genera la boleta**. **Todos los marketplaces de Chile están conectados vía Multivende** — es la puerta para entender "dónde estamos parados" en cada canal.

> ✅ **Multivende TIENE API** (confirmado 2026-06-27). Falta crear la cuenta de desarrollador y registrar la app.

## ✅ Integración por API — Multivende Integration Services (MIS)
- **Tipo:** API REST, autenticación **OAuth2**.
- **Documentación:** colección en **Postman** + entorno de desarrollo (el "Playground" para probar antes de producción).
- **Capacidades:** leer y actualizar **pedidos, stock, precios y productos**.
- **Setup requerido:**
  1. Crear cuenta de desarrollador → https://app.multivende.com/developers/signup
  2. Registrar una **aplicación**, configurando: **scopes** (permisos que el comercio otorga), **redirect URL** (OAuth) y **webhooks** (notificaciones: nueva venta, cambio de stock, etc.).
  3. Flujo OAuth2: el comercio (SLEVE) autoriza la app → se obtiene token → token va a `secrets/`.
  4. Implementar cliente en `scripts/` (o un MCP propio) que consuma la API y deje datos en `output/exports/`.
- **Docs útiles:**
  - Guía de integración: https://help.multivende.com/knowledge/proceso-de-integracion-a-multivende
  - Cómo crear una app: https://help.multivende.com/knowledge/como-crear-una-aplicacion
  - API en Postman: https://help.multivende.com/hc/es-419/articles/13751325899917-API-Mutivende-Postman
- **Sensibilidad:** escribir stock/precios/productos es acción de producción → requiere confirmación del usuario (ver CLAUDE.md §5). Empezamos solo con **lectura**.

## Qué hace Multivende (confirmado con usuario 2026-06-27)
Multivende es el **master del catálogo** de SLEVE. Es la fuente de verdad que crea y distribuye a todos los marketplaces:
- **Productos:** creación y **características/atributos** del producto (ficha maestra → se publica en cada canal).
- **Precios:** define el precio maestro y lo mueve a todos los marketplaces.
- **Inventario:** stock centralizado, se dispara a cada canal (evita sobreventa).
- **Pedidos + boleta:** consolida pedidos de todos los canales y emite el documento tributario.

> Implicancia para el agente: el **catálogo, precios e inventario "correctos" viven en Multivende**. Si un marketplace muestra otro precio/stock, es un descalce a detectar (conciliación). El análisis de pricing y de quiebres parte de Multivende.

## Por qué importa para el agente
- Es la **fuente de verdad de pedidos consolidados** y de boletas.
- Permite **conciliar** marketplace ↔ Multivende ↔ boleta (ver PLAYBOOK SOP 4).
- Es el puente para acceder a datos de marketplaces que no tienen MCP propio.

## Opciones de integración
| Opción | Cómo | Pros | Contras |
|---|---|---|---|
| ✅ **API oficial (elegida)** | Cuenta dev + app OAuth2 + script en `scripts/` + token en `secrets/` | Datos en tiempo real, webhooks, automatizable | Requiere setup inicial de app dev |
| **Export CSV/Excel** | Descarga manual → `output/exports/` | Fallback rápido sin desarrollo | Manual, no en tiempo real |
| **MCP propio** | Envolver la API en un MCP | Integración nativa con el agente | Más esfuerzo (fase 2) |

## Datos esperados desde Multivende
- Pedidos: id, canal, fecha, SKU, cantidad, precio, estado, folio boleta.
- Stock: SKU, cantidad por bodega, stock publicado por canal.
- Boletas: folio, monto, fecha, asociación a pedido.

---
### 📋 Necesito del usuario
1. ¿Multivende tiene API? ¿Tienes acceso a credenciales/token?
2. Si no hay API, ¿se puede exportar CSV y con qué frecuencia?
3. ¿Qué campos/reportes entrega hoy Multivende que ya usas?
4. ¿Multivende es la fuente de verdad de stock, o lo es Shopify/otro?
