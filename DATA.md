# DATA.md — Estructura y significado de los datos

Cómo están organizados los datos que maneja el agente. SOURCES.md da el origen y la confianza; **DATA.md da la estructura y el significado**. Se consulta para interpretar correctamente lo que se extrae antes de analizarlo.

> 🚧 Borrador. Se completa a medida que se conectan las fuentes reales.

---

## 1. Entidades clave y cómo se relacionan
- **SKU / producto** — identificador que conecta el mismo producto entre Shopify, Multivende y cada marketplace. ⚠️ Confirmar que el SKU es consistente entre canales (suele ser el punto de quiebre).
- **Orden / pedido** — una venta. Vive en el canal de origen y se consolida en Multivende; genera boleta.
- **Cliente** — B2C (persona) o B2B (empresa/RUT). Distinto tratamiento de precio e impuestos.
- **Canal** — sitio propio, o un marketplace específico en un país específico.

```
Producto (SKU) ──┬── Shopify (sitio propio)
                 ├── Marketplace A (país X)
                 ├── Marketplace B (país Y)
                 └── Multivende (consolida stock + pedidos + boleta)
```

## 2. Datasets por fuente

### Shopify
- **Formato:** API GraphQL / ShopifyQL.
- **Campos clave:** `sku`, `title`, `price`, `inventory_quantity`, `order_id`, `total_price`, `created_at`, `customer_id`.
- **Unidades:** montos en CLP ❓ (confirmar moneda por tienda).

### Ads (Meta / Google / TikTok — vía Windsor)
- **Campos clave:** `spend`, `impressions`, `clicks`, `conversions`, `conversion_value`, `campaign`, `date`.
- **Cálculos estándar:**
  - **ROAS** = conversion_value / spend
  - **MER** (Marketing Efficiency Ratio) = revenue total / ad spend total
  - **CAC** = ad spend / nuevos clientes
  - **CPA** = spend / conversiones

### Multivende (master de catálogo + precio + inventario + pedidos)
- **Formato:** API REST JSON (OAuth2).
- **Es la fuente de verdad de:** producto (SKU, características/atributos), **precio maestro**, **inventario**, pedidos y boleta. Se propaga a Shopify + marketplaces 3P.
- **Campos esperados:** producto/SKU, atributos, precio, stock por bodega, canal publicado, pedido, estado, boleta/folio.
- **Conciliación clave:** precio/stock publicado en cada marketplace vs. el maestro de Multivende → descalces = bandera.

### Marketplaces
- **Formato:** ❓ por marketplace.
- **Campos esperados:** venta, comisión, ranking/posición, reputación/reviews, stock publicado, estado de despacho.

## 3. Transformaciones / cálculos estándar
- **Margen de contribución** = (precio venta − costo − comisión canal − costo despacho) / precio venta. ❓ Confirmar fórmula y de dónde sale el costo.
- **Revenue consolidado** = suma de ventas netas de todos los canales (evitar doble conteo entre marketplace y Multivende).
- **Quiebre de stock** = inventory_quantity ≤ umbral (definir umbral por producto/canal).

## 4. Dónde viven los datos
- Exports y dumps → `output/exports/`
- Análisis procesados → `output/analisis/`
- Reportes finales → `output/reportes/`

---

### 📋 Pendiente de definir con el usuario
- Moneda(s) y manejo multi-país.
- Fórmula exacta de margen y origen del costo de cada producto.
- Formato real de export de Multivende y de cada marketplace.
- Consistencia de SKU entre canales.
