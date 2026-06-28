# SLEVE E-commerce Agent — servicio always-on (Railway)

Robot de E-commerce. Es un **servicio hermano** del Trade Marketing, dentro del mismo proyecto Railway **`Sleve_Agents`**. Mismo molde que `Sleve-Trade-Marketing`.

## Piezas (en `agent/`)
- `run_railway.py` — **supervisor**: mantiene el bot vivo, corre el scheduler (brief diario), health HTTP, y el MCP server si `MCP_ENABLED`.
- `bot.py` — bot de Telegram (long-polling, comandos). Solo responde al chat autorizado.
- `orchestrator.py` — la **cabeza**: junta a los especialistas y arma el brief. Hook `ask()` para Fase 2 (Anthropic API).
- `specialists.py` — los 6 especialistas (ads, marketplaces, orgánico, tienda/CRO, social, retención).
- `db.py` — DuckDB sobre el **volumen** (persistencia de snapshots).
- `mcp_server.py` — MCP read-only para que el agente Comercial y el E-commerce se consulten entre sí (gateado por `MCP_ENABLED`).

## Cómo se deploya (nuevo servicio en `Sleve_Agents`)
1. En Railway, abre el proyecto **Sleve_Agents** → **+ New** → **GitHub Repo** → elige `sleve-ecommerce-agent`.
2. Railway detecta el **Dockerfile** (raíz del repo) y construye solo.
3. **Variables** del servicio:
   ```
   TELEGRAM_BOT_TOKEN = (token de BotFather)
   TELEGRAM_CHAT_ID   = 920578167
   TZ                 = America/Santiago
   DATA_DIR           = /data        (si montas un volumen)
   # datos en vivo (loop cada 2h):
   WINDSOR_API_KEY    = (UNA llave abre todas las fuentes Windsor: Google/GA4/TikTok/Metricool/Gorgias/Meta)
   # directas (a futuro): SHOPIFY_TOKEN, KLAVIYO_API_KEY, MULTIVENDE_TOKEN
   # opcionales:
   ANTHROPIC_API_KEY  = (para Fase 2: razonamiento en lenguaje natural)
   MCP_ENABLED        = 1            (para exponer el MCP a otros agentes)

## Loop de datos (cada 2h)
`run_railway.py` ejecuta `refresh.py` al arrancar y **cada 2 horas**: trae la data de las fuentes (Windsor con `WINDSOR_API_KEY`; directas con sus llaves) y escribe `DATA_DIR/overview.json`. El robot lo sirve en **`GET /api/overview`** (con CORS) para que el dashboard lo lea en vivo. Sin llaves, escribe el baseline de Chile como placeholder.
   ```
4. (Opcional) **Volumen** montado en `/data` → persiste la DuckDB y snapshots, igual que el Trade.
5. Deploy → llega "🔵 online" a Telegram. Comandos: `/brief /ads /marketplaces /organico /cro /social /retencion /estado /ping`.

## Local
```bash
cd agent
python3 bot.py     # usa ../secrets/.env
```

## Fase 2 (siguiente)
`orchestrator.ask()` con Anthropic API (`claude-opus-4-8`) → responder preguntas en lenguaje natural delegando en los especialistas. Y cada especialista consultando su fuente real (Shopify, Windsor, Multivende, Klaviyo, Metricool) en vez de los textos demo.
