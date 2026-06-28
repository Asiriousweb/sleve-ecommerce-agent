# SLEVE Agent — servicio always-on (Railway)

Servicio Python que mantiene al agente SLEVE corriendo 24/7 y escuchando Telegram, sin depender de tu computador.

## Qué hace (Fase 1)
- Long-polling de Telegram: escucha tus mensajes y responde comandos.
- Comandos: `/brief`, `/estado`, `/ping`, `/help`.
- Mensaje de "online" al arrancar.
- Health HTTP en `$PORT` (Railway lo necesita).
- Solo responde al chat autorizado (`TELEGRAM_CHAT_ID`).

## Fase 2 (siguiente)
Conectar el cerebro (Claude Agent SDK) en `handle_command()` para que los comandos disparen al orquestador y a los especialistas con análisis en vivo (Shopify, Windsor, Multivende…). Requiere `ANTHROPIC_API_KEY`.

## Correr local
```bash
cd agent
python3 main.py     # usa ../secrets/.env para el token
```

## Deploy en Railway (paso a paso)
Necesitas una cuenta en https://railway.app

**Opción A — Railway CLI (rápida, sin GitHub):**
```bash
npm i -g @railway/cli
railway login
cd agent
railway init        # crea el proyecto
railway up          # sube y deploya esta carpeta
```

**Opción B — GitHub:**
1. Sube el repo a GitHub.
2. En Railway: New Project → Deploy from GitHub repo.
3. En Settings → **Root Directory** = `agent`.

**En ambos casos — variables de entorno (Railway → Variables):**
```
TELEGRAM_BOT_TOKEN = (tu token de BotFather)
TELEGRAM_CHAT_ID   = 920578167
```
> Las credenciales van SOLO en Railway, nunca en el repo. `secrets/` está en `.gitignore`.

4. Railway expone un dominio (health en `/`). El bot empieza a responder en Telegram apenas deploya.

## Verificar
- En Telegram, escribe `/ping` → debe responder `pong ✅`.
- `/brief` → resumen de Chile. `/estado` → estado del sistema.
