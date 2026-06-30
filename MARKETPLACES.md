# MARKETPLACES.md — Marketplaces por país

Catálogo de todos los marketplaces donde vende SLEVE, por país. Cada uno con su acceso a datos, comisión, reglas y estado.

> **Estado 2026-06-30:** Mercado Libre conectado **DIRECTO** (API oficial, gratis) en 3/4 países — reemplaza a Nubimetrics (~$320/mes). El resto de marketplaces entra por Multivende (pendiente credenciales). Acceso a datos por marketplace: **Mercado Libre = directo**; Falabella/Walmart/Ripley/París = **Multivende**.

## Cómo se llena cada marketplace
Por cada uno: nombre · país · cuenta/seller · % comisión · cómo accedo a sus datos (directo / Multivende / CSV) · reglas clave · estado.

---

## 🇨🇱 Chile
| Marketplace | Cuenta/seller | Acceso a datos | Estado | Datos (7d, ref. 2026-06-30) |
|---|---|---|---|---|
| Shopify (sitio propio B2C+B2B) | sleve-inc + reseller | Shopify directo | 🟢 | ~216 pedidos |
| **Mercado Libre** | **SLEVEMOBILE** (user 290288222) | **ML directo** | 🟢 | **~682 pedidos · 57 publicaciones** |
| Falabella | ❓ | Multivende | 🔴 | — |
| Walmart | ❓ | Multivende | 🔴 | — |
| Ripley | ❓ | Multivende | 🔴 | — |
| París | ❓ | Multivende | 🔴 | — |

## 🇨🇴 Colombia
| Marketplace | Cuenta/seller | Acceso a datos | Estado |
|---|---|---|---|
| Shopify (sitio propio) | sleve-mobile-colombia | Shopify directo | 🟢 |
| **Mercado Libre CO** | ❓ | ML directo | 🟡 **falta verificación de cuenta en ML** → reconectar en /meli |
| Otros (Falabella/Éxito) | ❓ | Multivende | 🔴 |

## 🇲🇽 México
| Marketplace | Cuenta/seller | Acceso a datos | Estado | Datos (7d) |
|---|---|---|---|---|
| Shopify (sitio propio) | sleve-mobile-mexico | Shopify directo | 🟢 | ~0 pedidos |
| **Mercado Libre MX** | **SLEVEMEXICO** (user 2415858407) | ML directo | 🟢 | ~1 pedido · **24 publicaciones** |
| Amazon MX / Coppel | ❓ | Multivende | 🔴 | — |

## 🇵🇪 Perú
| Marketplace | Cuenta/seller | Acceso a datos | Estado | Datos (7d) |
|---|---|---|---|---|
| Shopify (sitio propio) | sleve-mobile-peru | Shopify directo | 🟢 | ~3 pedidos |
| **Mercado Libre PE** | **SOSL20240216190454** (user 1687111150) | ML directo | 🟢 | ~1 pedido · **63 publicaciones** |
| Falabella PE / Ripley PE | ❓ | Multivende | 🔴 | — |

> ⚠️ **Hallazgo (2026-06-30):** ML México (24 pubs) y ML Perú (63 pubs) tienen catálogo publicado pero **casi sin ventas** (1 pedido/7d cada uno) vs Chile (682). Revisar precio/posicionamiento/buy box en esos marketplaces.

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
