# MARKETPLACES.md — Marketplaces por país

Catálogo de todos los marketplaces donde vende SLEVE, por país. Cada uno con su acceso a datos, comisión, reglas y estado.

> 🚧 **Plantilla vacía.** El usuario va a indicar los marketplaces reales de cada país. Abajo dejo la estructura y los candidatos típicos de la región para acelerar el llenado.

## Cómo se llena cada marketplace
Por cada uno: nombre · país · categoría/cuenta · % comisión · cómo accedo a sus datos (Multivende / API propia / Windsor / CSV) · reglas clave (buy box, despacho, reputación) · estado de la integración.

---

## 🇨🇱 Chile — confirmado con usuario 2026-06-27
Todos son **3P (marketplace seller)** y **todos se gestionan vía Multivende** (que centraliza inventario y dispara stock a cada uno). Acceso a datos = **Multivende API**.
| Marketplace | Modalidad | Comisión | Acceso a datos | Estado |
|---|---|---|---|---|
| Shopify (sitio propio) | Directo B2C/B2B | — | MCP Shopify / Multivende | 🟢 (B2C) |
| Falabella | 3P | ❓ | Multivende | 🔴 (falta app) |
| Walmart | 3P | ❓ | Multivende | 🔴 |
| Ripley | 3P | ❓ | Multivende | 🔴 |
| París | 3P | ❓ | Multivende | 🔴 |
| MercadoLibre | 3P | ❓ | Multivende | 🔴 |

> ✅ **Países confirmados (2026-06-27):** Chile, Colombia, México, Perú (por cuentas de Ads/GA4). Falta listar los marketplaces de cada uno.

## 🇨🇴 Colombia
| Marketplace | Cuenta/seller | Comisión | Acceso a datos | Estado |
|---|---|---|---|---|
| MercadoLibre CO | ❓ | ❓ | ❓ | 🔴 |
| Falabella CO / éxito / otros | ❓ | ❓ | ❓ | 🔴 |

## 🇲🇽 México
| Marketplace | Cuenta/seller | Comisión | Acceso a datos | Estado |
|---|---|---|---|---|
| MercadoLibre MX | ❓ | ❓ | ❓ | 🔴 |
| Amazon MX / Coppel / otros | ❓ | ❓ | ❓ | 🔴 |

## 🇵🇪 Perú
| Marketplace | Cuenta/seller | Comisión | Acceso a datos | Estado |
|---|---|---|---|---|
| MercadoLibre PE | ❓ | ❓ | ❓ | 🔴 |
| Falabella PE / Ripley PE / otros | ❓ | ❓ | ❓ | 🔴 |

---

## Reglas transversales a vigilar
- **Comisiones** por categoría y país (afectan el margen — ver DATA.md).
- **Buy box / posicionamiento** (precio y reputación).
- **SLA de despacho** por marketplace (penalizaciones).
- **Reputación / reviews** (impacto en visibilidad).
- **Quiebres de stock** publicados (perder publicación = perder ranking).

---

### 📋 Lo que necesito del usuario
1. Lista de marketplaces por país (lo que ibas a demostrar).
2. Por cada uno: ¿se accede vía Multivende, API propia, o export?
3. Comisión por categoría (para el cálculo de margen real).
