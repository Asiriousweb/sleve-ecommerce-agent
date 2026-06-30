# CHANNELS.md — Canales de venta

Visión de todos los canales por donde SLEVE vende, su rol y cómo se miden. Los marketplaces tienen su propio detalle en [MARKETPLACES.md](MARKETPLACES.md).

> 🚧 Borrador — confirmar con el usuario.

## Tiendas Shopify (multi-tienda, misma cuenta) — verificado con usuario 2026-06-27
La cuenta Shopify tiene **varias tiendas** que hay que extraer completas:
| Tienda | País | Cliente | Estado |
|---|---|---|---|
| Sleve Mobile Chile (sleve.cl) | 🇨🇱 Chile | B2C | 🟢 conectada (activa) |
| Sleve Perú | 🇵🇪 Perú | B2C | ⚪ por extraer (usar `switch-shop`) |
| Sleve Colombia | 🇨🇴 Colombia | B2C | ⚪ por extraer |
| Sleve México | 🇲🇽 México | B2C | ⚪ por extraer |
| **Sleve Chile B2B** | 🇨🇱 Chile | **B2B (tienda aparte)** | ⚪ por extraer |

> El B2B **NO vive en la misma tienda** que el B2C: es una tienda Shopify separada. Al consolidar venta hay que sumar todas las tiendas, distinguiendo B2C vs B2B.
> Nota técnica (2026-06-30): la data multi-tienda de Shopify es **automática** vía OAuth directo en el robot (un token por tienda, 6 tiendas). Ya no se usa `switch-shop` ni Windsor.

## Mapa de canales
| Canal | Tipo | Cliente | Plataforma | Datos vía | Estado |
|---|---|---|---|---|---|
| Sitio propio B2C | Directo | Persona | Shopify (CL/PE/CO/MX/EEUU) | Shopify directo | 🟢 |
| Sitio propio B2B | Directo | Empresa/RUT | Shopify (tienda Chile B2B aparte) | Shopify directo | 🟢 |
| **Mercado Libre (3P)** | Intermediado | B2C | ML CL/MX/PE (CO pendiente) | **ML directo** | 🟢 3/4 |
| Otros marketplaces (3P) | Intermediado | B2C | Falabella, Walmart, Ripley, París | **Multivende (API)** | 🔴 (pendiente) |
| Redes sociales | Orgánico + social commerce | B2C | IG, FB (TikTok/YT futuro) | Meta Graph directo | 🟢 (seguidores/posts) |
| Email/CRM | Directo | B2C | Klaviyo | Klaviyo directo (4) | 🟢 |
| Centralizador | Operativo | — | **Multivende** | API OAuth2 | 🟡 (esperando credenciales) |

## Rol de cada canal
- **Sitio propio:** mejor margen (sin comisión de marketplace), control total de marca y data del cliente. Foco de ads propios y email (Klaviyo).
- **Marketplaces:** volumen y alcance, a costa de comisión y menos data del cliente. Pelea de precio/buy box.
- **B2B:** ❓ tickets más grandes, precios y condiciones distintas, posible flujo de cotización.

## Diferencias B2C vs B2B a tener presentes
- Precio (con/sin IVA, lista mayorista), condiciones de pago, mínimos de compra, despacho.
- ❓ Confirmar cómo conviven en Shopify (markets, catálogos B2B, o tienda separada).

---
### 📋 Necesito del usuario
1. ✅ B2B en tienda Shopify aparte (Chile B2B). — confirmado.
2. Peso relativo de cada canal/país en venta y en margen.
3. ¿Hay venta por otros canales (WhatsApp directo, retail físico, social commerce)?
4. Lista de marketplaces por país (los de CL salen vía Multivende).
