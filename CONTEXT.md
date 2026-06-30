# CONTEXT.md — Contexto del negocio SLEVE

> El cerebro de conocimiento del agente. Contiene todo lo necesario para decidir bien sin que el usuario lo explique cada vez.
> 🚧 **ARCHIVO EN CONSTRUCCIÓN.** Las secciones marcadas con ❓ esperan datos del usuario. Completar es prioridad #1 (ver TASKS.md).

---

## 1. La empresa
- **Marca:** SLEVE Mobile (SleveMobile®)
- **Rubro:** Ecommerce — **Electronics** (productos móviles / electrónica de consumo). ❓ Confirmar mix exacto de categorías (accesorios celular, audio, etc.).
- **Sociedad relacionada:** Inversiones Matulic. Business central en Meta: "SLEVE Comercial Central".
- **Dirección:** Lord Cochrane 1134, Santiago, Chile (según Klaviyo).
- **Dominios:** `sleve.cl` (tienda Shopify) y `slevemobile.cl` (ambos en Search Console; Klaviyo usa slevemobile.cl). ❓ Confirmar cuál es el principal y relación entre ambos.
- **Plataforma sitio:** Shopify **Plus** — **multi-tienda**: Chile, Perú, Colombia, México (B2C) **+ Chile B2B en tienda separada**.
- **Marketplaces:** todos los de Chile centralizados vía **Multivende** (API OAuth2 confirmada). CO/MX/PE por mapear.
- **Modelo:** B2C + B2B (B2B en su propia tienda) — ❓ confirmar peso de cada uno.
- **País base:** Chile.
- **Países donde opera / vende (confirmados):** 🇨🇱 Chile · 🇨🇴 Colombia · 🇲🇽 México · 🇵🇪 Perú _(según cuentas de Meta Ads, Google Ads y GA4)_. ❓ ¿Algún otro país?

## 2. Objetivos actuales
> ❓ A definir con el usuario. Borrador:
- Centralizar el análisis de todos los canales (marketplaces + sitio propio) en un solo lugar.
- Detectar problemas y urgencias antes de que cuesten dinero.
- Mejorar eficiencia de venta, ads, pricing y customer service.
- Construir un dashboard de control con métricas y urgencias.

## 3. Canales de venta
> Detalle completo en [CHANNELS.md](CHANNELS.md) y [MARKETPLACES.md](MARKETPLACES.md).
- **Sitio propio:** Shopify Plus — tienda "Sleve Mobile Chile" (sleve.cl). ❓ ¿Hay tiendas Shopify por país o una sola? ¿B2C y B2B separados?
- **Marketplaces:** "prácticamente todos" por país (CL/CO/MX/PE) ❓ _(listar en MARKETPLACES.md)_
- **Email/CRM:** Klaviyo (cuenta Chile). ❓ ¿Klaviyo por país o solo Chile?
- **Centralizador:** **Multivende** — conecta canales y genera boleta. Ver [MULTIVENDE.md](MULTIVENDE.md).

### Marketing digital activo (verificado 2026-06-27)
- **Meta Ads:** múltiples cuentas por país bajo "SLEVE Comercial Central" (hay desorden: cuentas "NO USAR"/"ELIMINAR"/CLOSED a depurar).
- **Google Ads:** Chile, Colombia, México, Perú (directo, Ads API v23; MCC 137-819-4398).
- **GA4:** Chile, Colombia, México, Perú.
- **Search Console:** sleve.cl, slevemobile.cl.

## 4. Stakeholders / equipo
- **Dueño / decisor:** Nicolás Matulic (nmatulic@inversionesmatulic.cl)
- **Equipo:** ❓ _(quién maneja ads, quién customer service, quién bodega/logística)_

## 5. Productos / catálogo
- **Marca propia de electrónica/audio.** Categorías: audífonos TWS/ANC, powerbanks, parlantes Bluetooth.
- **Best-sellers (Chile, 30d):** Pulse ANC 2Gen (el rey), One 2Gen, Xpods 2Gen, Evo 2Gen, PureX, Power X 10.000 mAh, parlantes BasslineX/Boom.
- **N° de SKUs:** ❓ (confirmar catálogo completo)
- **Estacionalidad:** ❓ — se ve tráfico de cyber.cl (eventos Cyber). Confirmar peaks (CyberDay, Black Friday, Navidad).

## 6. Restricciones conocidas
- **Tecnología:** Shopify, Multivende, MCPs de Claude (ver TOOLS.md). Multivende sin integración aún.
- **Presupuesto de ads:** ❓
- **Márgenes / objetivos de margen:** ❓
- **Reglas de negocio innegociables:** ❓ _(ej: nunca vender bajo cierto margen, no competir en precio en cierto canal)_

## 7. Eventos comerciales relevantes
> ❓ Confirmar. En Chile típicamente: CyberDay, CyberMonday, Black Friday, Navidad, Día de la Madre, liquidaciones. Detalle en [CALENDAR.md] (por crear).

## 8. Historial relevante
- 2026-06-27 — Inicio del proyecto: se construye la estructura base del Agente SLEVE a partir de la "Estructura Universal de Agente" (PDF) y de la experiencia del agente anterior del usuario.
- ❓ _(decisiones pasadas que afecten el presente: cambios de plataforma, problemas recurrentes, etc.)_

---

### 📋 Lo que necesito del usuario para completar este archivo
1. Qué vende SLEVE (categoría/rubro) y razón social.
2. Países donde vende y marketplaces por país.
3. Estructura del sitio: ¿Shopify único? ¿B2C y B2B separados?
4. Peso B2C vs B2B.
5. Best-sellers y estacionalidad.
6. Objetivos y márgenes meta.
7. Cómo se accede a Multivende (API, export, login).
