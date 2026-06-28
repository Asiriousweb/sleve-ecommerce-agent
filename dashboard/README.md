# SLEVE · E-commerce Cockpit (dashboard)

Dashboard web del agente SLEVE — consolidado multicanal y multi-país, estética dark estilo cockpit. Next.js 14 (App Router) + Tailwind + Recharts.

## Estado
v0.1 — maqueta funcional con el **baseline real de Chile** (sitio propio Shopify + GA4, 30d) y datos demo para marketplaces/ads/social (hasta conectar Multivende y Windsor). Toda la data vive en `lib/data.ts` para reemplazarla por la API en vivo.

## Correr local
```bash
cd dashboard
npm install
npm run dev        # http://localhost:3000
```

## Arquitectura objetivo (Railway + Vercel)
```
┌─────────────── Vercel ───────────────┐      ┌─────────────── Railway ───────────────┐
│  Frontend (este Next.js)              │ ───▶ │  API + Agente (always-on)              │
│  - Dashboard / gráficos               │ HTTP │  - Pull de Shopify / Windsor / Multivende
│  - Llama a la API por NEXT_PUBLIC_API_URL    │  - Cálculos (MER, conciliación)        │
└───────────────────────────────────────┘      │  - Loop nocturno + Telegram            │
                                                └────────────────────────────────────────┘
```
- **Frontend → Vercel:** este proyecto. Deploy con `vercel` o conectando el repo de GitHub.
- **Backend/Agente → Railway:** API que sirve los datos reales (ej. `/chile/overview`, `/chile/trend`) consumiendo las fuentes. Se construye en una fase siguiente (carpeta `api/` o servicio aparte).
- **Conexión:** el frontend lee `NEXT_PUBLIC_API_URL`. Mientras no exista la API, usa los datos de `lib/data.ts`.

## Cómo pasar de demo a datos en vivo
1. Levantar la API en Railway con endpoints por país (Chile primero).
2. Definir `NEXT_PUBLIC_API_URL` en Vercel (variable de entorno).
3. En `lib/data.ts`, reemplazar las constantes por `fetch(`${process.env.NEXT_PUBLIC_API_URL}/...`)`.

## Deploy a Vercel
```bash
cd dashboard
npx vercel            # primera vez: vincula el proyecto
npx vercel --prod     # producción
```
> Credenciales (tokens de Shopify/Windsor/Multivende) NUNCA en el frontend — viven en el backend de Railway como variables de entorno.

## Pendiente
- Reemplazar logo placeholder por el logo oficial de SLEVE (header).
- Selector de país/vista funcional (hoy estático).
- Pestaña YoY.
- Conectar a la API real (Railway).
