# ─────────────────────────────────────────────────────────────────────────────
# SLEVE E-commerce Agent — imagen del AGENTE (backend) para Railway.
# Es un servicio HERMANO del Trade Marketing, dentro del proyecto Sleve_Agents.
# El frontend (dashboard/) NO se sirve desde aquí → eso va por Vercel.
# Corre: bot de Telegram + scheduler (brief diario) + (opcional) MCP server.
# Mismo patrón que Sleve-Trade-Marketing.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# git: para commits automáticos (regenerar dashboard → push → Vercel) · curl/ca-certs: TLS
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Deps primero (mejor caché)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el repo
COPY . .

# Identidad git para commits automáticos
RUN git config --global user.email "agent@sleve.cl" \
    && git config --global user.name "SLEVE Ecommerce Agent (Railway)" \
    && git config --global --add safe.directory /app

# UN solo servicio corre todo (bot + scheduler + MCP), compartiendo el volumen.
CMD ["python", "-u", "agent/run_railway.py"]
