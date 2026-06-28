# ECOSYSTEM.md — Modelo completo de plataformas SLEVE

Cómo se conecta todo el ecosistema. Tres capas: **inventario/venta** (centralizado en Multivende), **advertising** y **social**. Por encima, **GA4 es la fuente primaria de analytics** — el punto de partida para entender qué pasa.

---

## 🗺️ Mapa del ecosistema (Chile, replicable por país)

```
                 ┌───────────────────────────────────────────────┐
                 │   GA4 — FUENTE PRIMARIA DE ANALYTICS            │
                 │   "qué pasa en la página, la interacción"       │
                 │   → el análisis SIEMPRE parte de aquí           │
                 └───────────────────────────────────────────────┘
                        ▲              ▲                ▲
        ────────────────┴──────  ─────┴────────  ──────┴───────────
        VENTA / INVENTARIO        ADVERTISING          SOCIAL
                │                      │                   │
        ┌───────────────┐    ┌──────────────────┐   ┌──────────────┐
        │  MULTIVENDE    │    │ Klaviyo (email)  │   │  METRICOOL   │
        │  centraliza el │    │ Meta Ads         │   │ IG · FB ·    │
        │  inventario y  │    │ Google Ads       │   │ TikTok · YT  │
        │  lo DISPARA a: │    │ TikTok Ads       │   │ (orgánico)   │
        └───────┬────────┘    │ + SEO/Search Cons│   └──────────────┘
                │             └──────────────────┘
                ▼  (stock + pedidos + boleta)
   ┌──────────────────────────────────────┐
   │  Shopify (sitio propio B2C + B2B)     │
   │  Falabella 3P                          │
   │  Walmart 3P                            │
   │  Ripley 3P                             │
   │  París 3P                              │
   │  MercadoLibre 3P                       │
   └──────────────────────────────────────┘
```

> **3P = third-party / marketplace seller:** SLEVE vende como seller en esos marketplaces, no como retail directo (1P).

---

## 1. Capa de venta / inventario — Multivende como master del catálogo
- **Multivende es el master de producto, precio e inventario.** Crea los productos (con sus características), define precios y stock, y los **dispara a todas las plataformas**. También consolida pedidos y emite boleta.
- Plataformas conectadas (Chile): **Shopify, Falabella 3P, Walmart 3P, Ripley 3P, París 3P, MercadoLibre 3P**.
- Para el agente, Multivende es la **fuente de verdad de catálogo, precios, stock y pedidos**. Si un marketplace muestra otro precio/stock = descalce a detectar. Integración por API OAuth2 (ver MULTIVENDE.md).
- Detalle por marketplace en MARKETPLACES.md.

## 2. Capa de analytics — GA4 primero
- **GA4 es la primera fuente de todo:** desde ahí se entiende la interacción del sitio (tráfico, fuentes, embudo, conversión) y se "arrastra" el resto del análisis.
- El agente **parte el análisis en GA4** y luego baja al detalle de cada plataforma (Shopify para venta fina, Ads para spend/ROAS, Multivende para marketplaces).
- Complemento SEO: Search Console (orgánico).
- Acceso: GA4 vía Windsor.ai (4 países conectados).

## 3. Capa de advertising
- **Email/CRM:** Klaviyo.
- **Paid:** Meta Ads, Google Ads, TikTok Ads.
- **SEO:** dentro de Google (Search Console + GA4 orgánico).
- Consolidación de spend/ROAS: Windsor.ai (Google ✅; Meta y TikTok por autorizar).

## 4. Capa social
- **Metricool** es la herramienta de redes (IG, FB, TikTok, YouTube) — desde ahí se extrae el desempeño orgánico.
- ✅ Metricool está disponible como conector en **Windsor.ai** → se consolida con el resto. (Link de autorización entregado por chat.)
- Detalle en SOCIAL.md.

## 5. Capa de servicio — Customer Service (Gorgias)
- **Gorgias** centraliza todo el customer service de SLEVE: email/chat del sitio, marketplaces, redes y WhatsApp en una sola bandeja con tickets y SLA.
- ✅ Disponible como conector en **Windsor.ai** → se consolida con el resto. Último en activar.
- Detalle en CUSTOMER-SERVICE.md.

---

## Cómo lee el agente este modelo (orden de análisis)
1. **GA4** → foto de qué está pasando (tráfico, conversión, fuentes). Punto de partida.
2. **Multivende + Shopify** → venta real e inventario por canal/marketplace.
3. **Ads (Meta/Google/TikTok) + Klaviyo** → de dónde viene la demanda y a qué costo (ROAS/MER).
4. **Metricool** → aporte de lo orgánico/social.
5. **Cruce** → dónde hay fuga, oportunidad o urgencia → al dashboard (DASHBOARD.md).

> Este es el modelo de **Chile** (país piloto). Se replica igual en Colombia, México y Perú cambiando cuentas/marketplaces. Ver CHILE.md.
