# CHILE.md — Modelo maestro 🇨🇱

Chile es el **país modelo**: lo dejamos completo end-to-end y luego se replica en Colombia, México y Perú. Este archivo es el blueprint replicable + el baseline de datos reales.

> **Baseline:** últimos 30 días al 2026-06-27. Moneda: CLP.
> **Cómo replicar:** copiar la estructura de "Cuentas y fuentes" y "Modelo de métricas" cambiando IDs/cuentas por las del país destino.

---

## 1. Cuentas y fuentes de Chile

| Arista | Cuenta / fuente | ID | Estado |
|---|---|---|---|
| Sitio B2C | Shopify "Sleve Mobile Chile" (sleve.cl / sleve-inc.myshopify.com) | — | 🟢 con datos |
| Sitio B2B | Shopify Chile B2B (tienda aparte) | ❓ | 🔴 por re-autorizar |
| Ads Meta | Meta Ads CLP (+ Chile Reseller) | 31212947 · 1332315335238191 | 🟡 MCP (falta en Windsor) |
| Ads Google | Google Ads "Sleve Mobile Chile" | 398-306-6786 | 🟡 datos OK, revisar config |
| Ads TikTok | TikTok Ads | ❓ | 🔴 por conectar en Windsor |
| Analytics | GA4 "Sleve - GA4" | 399804339 | 🟢 con datos |
| SEO | Search Console | sleve.cl, slevemobile.cl | 🟢 |
| Email/CRM | Klaviyo (cuenta Chile) | LKZuCC | 🟢 |
| Marketplaces (3P) | **Falabella · Walmart · Ripley · París · MercadoLibre** — todos vía **Multivende** | — | 🔴 falta app Multivende |
| Redes orgánicas | IG/FB/TikTok/YouTube vía Windsor | — | 🔴 por autorizar |
| Customer service | ❓ (definir herramienta) | — | 🔴 |

---

## 2. Baseline de datos reales (últimos 30 días)

### 2.1 Venta — Sitio B2C (Shopify)
| Métrica | Valor |
|---|---|
| Pedidos | **2.349** |
| Gross sales | $60.721.628 |
| Net sales | $57.662.415 |
| Total sales (con IVA + envío) | $76.626.105 |
| AOV | **$24.851** |

### 2.2 Top productos (por total_sales)
| # | Producto | Ventas | Pedidos |
|---|---|---|---|
| 1 | **Pulse ANC 2Gen** (audífonos ANC) | $27.449.853 | 870 |
| 2 | One 2Gen | $9.437.125 | 625 |
| 3 | Xpods 2Gen | $8.050.464 | 388 |
| 4 | ⚠️ *(sin título)* | $8.007.930 | 0 |
| 5 | Evo 2Gen | $7.700.566 | 279 |
| 6 | PureX | $5.677.437 | 411 |
| 7 | Power X 10.000 Mah Black | $2.474.082 | 159 |
| 8 | Parlante BasslineX Pro | $2.154.899 | 21 |
| 9 | Parlante BasslineX Mini | $1.109.430 | 35 |
| 10 | Parlante Boom + | $828.326 | 31 |

> **Categoría SLEVE Mobile:** audio (TWS/ANC), powerbanks, parlantes Bluetooth — marca propia de electrónica/audio. **Pulse ANC 2Gen es el best-seller absoluto** (~36% del top 10).

### 2.3 Embudo de conversión (Shopify)
| Etapa | Sesiones | % |
|---|---|---|
| Sesiones | 178.000 | 100% |
| Llegó a checkout | 9.744 | 5,5% |
| Completó checkout | 2.221 | **1,25%** (conversión) |

> **Fuga:** de los que llegan a checkout, solo **22,8% completa**. 77% se cae en el checkout → mayor oportunidad de recuperación.

### 2.4 Fuentes de tráfico y conversión (GA4 — top por ventas)
| Fuente / medio | Sesiones | Ventas | Conv. |
|---|---|---|---|
| meta / cpc | 89.858 | 614 | 0,68% |
| google / cpc | 18.329 | 363 | **1,98%** |
| (direct) | 23.736 | 206 | 0,87% |
| klaviyo / cpc* | 1.828 | 74 | 4,05% |
| cyber.cl / referral | 4.691 | 58 | 1,24% |
| t-sml.mtrbio.com / referral (link-in-bio) | 3.786 | 55 | 1,45% |
| google / organic | 5.653 | 44 | 0,78% |
| tiktok / cpc | 8.561 | 37 | **0,43%** |
| facebook / paid | 2.502 | 28 | 1,12% |
| Klaviyo / email | 1.444 | 27 | 1,87% |

\*klaviyo está mal etiquetado como cpc (debería email) — corregir UTMs.

---

## 3. Hallazgos y oportunidades (Chile)
1. **TikTok Ads es el pagado más ineficiente:** 8.561 sesiones → 0,43% conv (el peor). Meta 0,68%, Google **1,98%**. Revisar si TikTok aporta arriba del embudo o solo quema presupuesto.
2. **Google convierte 3x mejor que Meta** pero recibe 5x menos tráfico → posible espacio para reasignar inversión.
3. **Fuga de checkout (77%):** la mayor palanca de venta sin gastar en más tráfico (revisar medios de pago, costos de envío, fricción).
4. **Producto "sin título" con $8M y 0 pedidos:** anomalía de catálogo/datos a investigar (¿producto eliminado, bundle, variante huérfana?).
5. **UTMs sucios:** klaviyo aparece como `cpc`, hay `3Dklaviyo`, `meta` y `facebook` duplicados como fuentes → el reporting de atribución pierde precisión. Estandarizar UTMs.
6. **AI search emergente:** aparece tráfico de chatgpt.com, perplexity, copilot. Tendencia a vigilar.
7. **Pendiente para foto completa:** marketplaces (Multivende) y B2B no están → la venta real de Chile es mayor que los $76M del sitio B2C.

---

## 4. Modelo replicable (qué clonar a CO/MX/PE)
Para cada país replicar:
- [ ] Conectar su tienda Shopify (B2C) — ya hay GA4/Google Ads por país.
- [ ] Mapear sus cuentas Meta/Google/TikTok/GA4/Klaviyo (tabla §1).
- [ ] Sus marketplaces y su acceso (Multivende u otro).
- [ ] Generar su baseline 30d (mismas métricas §2).
- [ ] Levantar sus hallazgos/oportunidades (§3).
- [ ] Conectar al dashboard (DASHBOARD.md) con filtro por país.

> Una vez Chile esté 100% (con Multivende + B2B + social), este archivo es la plantilla exacta a copiar como COLOMBIA.md, MEXICO.md, PERU.md.
