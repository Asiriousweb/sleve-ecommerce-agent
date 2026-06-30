# AGENTS.md — Arquitectura multi-agente SLEVE

SLEVE no es un solo agente que lo sabe todo, sino **orquestadores** (cabezas) que delegan en **especialistas**. Cada especialista cubre los 4 países (🇨🇱🇨🇴🇲🇽🇵🇪) en su dominio, con su propio contexto acotado.

> **Por qué:** un agente con todo el contexto es lento, caro y se dispersa. Especializar = foco, eficiencia de tokens y mejor criterio. El orquestador NO analiza data cruda: pide, consolida, prioriza y decide.

## 0. Topología: dos orquestadores bajo el proyecto Railway `Sleve_Agents`
Todo vive en el proyecto Railway **`Sleve_Agents`** (entorno `production`, always-on). Aloja **dos orquestadores hermanos**:

```
Railway · proyecto Sleve_Agents (production)
├── 🟣 Orquestador COMERCIAL → Trade Marketing
│        servicio: Sleve-Trade-Agents [online, en proceso] + volumen sleve-trade-marketing-volume
│        (tiene sus propios agentes de trade marketing)
└── 🔵 Orquestador E-COMMERCE → este (SLEVE E-commerce Agent)
         + 8 especialistas (ads, marketplaces, orgánico, tienda/CRO,
           inteligencia, social, retención, customer-service)
```

- **Comercial** y **E-commerce** son cabezas **paralelas** (no una bajo la otra). El Trade Marketing NO es un especialista del E-commerce.
- **Este documento describe el orquestador E-commerce** y sus especialistas.
- El cockpit/dashboard (frontend) va a **Vercel**; los orquestadores y agentes (backend always-on) van a **Railway** bajo `Sleve_Agents`.

---

## 🧠 Organigrama

```
                 ┌──────────────────────────────────────┐
                 │   SLEVE E-COMMERCE AGENT (orquestador)│
                 │   consolida · prioriza · decide        │
                 │   → dashboard + Telegram               │
                 └──────────────────────────────────────┘
            ┌───────────┬───────────┬───────────┬───────────┐
            ▼           ▼           ▼           ▼           ▼
     ┌───────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐
     │ PERFORMANCE││MARKETPLACE││ ORGÁNICO ││INTELIGEN.││ SOCIAL   │
     │   ADS     ││   3P     ││  & DESCU.││&TENDENC. ││&CONTENIDO│
     └───────────┘└──────────┘└──────────┘└──────────┘└──────────┘
        cada uno mira los 4 países en su especialidad
```

## Especialistas

| Agente | Dominio | Fuentes / MCPs | Qué entrega al orquestador |
|---|---|---|---|
| **Performance Ads** | Paid: Meta, Google, TikTok | Meta + Google directos (TikTok pendiente) | Spend, ROAS, MER, CAC, anomalías, qué pausar/escalar |
| **Marketplaces (3P)** | Mercado Libre (directo) + Falabella/Walmart/Ripley/París | **ML directo** + **Multivende** (resto) | Ventas, comisiones, buy box, reputación, stock/quiebres, conciliación |
| **Orgánico & Descubribilidad** | SEO, tráfico, contenido del sitio, conversión, AI search | GA4 + Search Console directos + Google Trends | Tráfico, fuentes, embudo, conversión, oportunidades de descubribilidad |
| **Inteligencia & Tendencias** | Precios, competencia, tendencias de mercado/categoría | Google Trends, WebSearch, Multivende (precios), Nubimetrics/manual | Posición de precio, movimientos de competencia, tendencias a capturar |
| **Social & Contenido** | Redes orgánicas, community, social commerce | Meta Graph directo (FB/IG) | Alcance, engagement, contenido top, social→venta |
| **Tienda / CRO** | Sitio Shopify B2C+B2B: conversión, checkout, catálogo | Shopify directo, GA4 | Conversión por tienda, fuga de checkout, anomalías de catálogo |
| **Retención / CRM** | Email/SMS, flows, recompra, lifecycle | Klaviyo directo (4 países) | % revenue CRM, salud de flows, recompra |
| **Customer Service** *(último en activar)* | Triage, SLA, reputación, borradores | **Gorgias** (API directa, pendiente key) | Backlog/SLA, reclamos recurrentes |

> **GA4 = fuente primaria** (la usa Orgánico y la comparte el orquestador). **Multivende = verdad de venta/precio/stock** (Marketplaces + Inteligencia la usan).

## Flujo del orquestador (Observar → Delegar → Sintetizar → Decidir)
1. **Observar:** lee estado (HEARTBEAT, TASKS) y arranca por GA4 (foto general).
2. **Delegar:** pide a cada especialista su lectura del día/semana (en paralelo cuando son independientes).
3. **Sintetizar:** cada especialista devuelve hallazgos estructurados; el orquestador cruza dominios (ej: caída de venta marketplace + alza de CAC ads + quiebre de stock = una sola historia).
4. **Decidir:** prioriza urgencias, alimenta el dashboard, avisa por Telegram, escala lo sensible al usuario.

## Cómo se implementa (Claude Code)
- Cada especialista = un archivo en `.claude/agents/<nombre>.md` (define rol, MCPs permitidos, formato de reporte). El orquestador los invoca con el Agent tool.
- Memoria: cada especialista puede tener su carpeta de contexto (`agents/<nombre>/` con sus PLAYBOOK/SOURCES propios) o reusar los .md raíz compartidos (SOURCES, DATA, MARKETPLACES, ECOSYSTEM).
- Eficiencia: cada agente solo carga SU dominio → menos tokens, más foco.

## ✅ Roster FINAL (decidido 2026-06-28) — 7 especialistas
1. **Performance Ads** — `.claude/agents/performance-ads.md`
2. **Marketplaces 3P** — `.claude/agents/marketplaces.md`
3. **Orgánico & Descubribilidad** — `.claude/agents/organico-descubribilidad.md`
4. **Inteligencia & Tendencias** (precios + competencia + tendencias) — `.claude/agents/inteligencia-tendencias.md`
5. **Social & Contenido** (propio) — `.claude/agents/social-contenido.md`
6. **Retención / CRM** (propio: Klaviyo, recompra, lifecycle) — `.claude/agents/retencion-crm.md`
7. **Tienda / CRO** (propio: foco en la fuga de checkout 77%) — `.claude/agents/tienda-cro.md`

8. **Customer Service** *(mapeado, pendiente de activar)* — `.claude/agents/customer-service.md`

Decisiones del usuario: Social = agente propio · Email/CRM = agente Retención propio · Sitio/CRO = agente propio · Customer Service = mapeado pero se implementa al final.
