// lib/data.ts — Capa de datos del dashboard SLEVE.
//
// HOY: datos del baseline real de Chile (sitio propio Shopify + GA4, extraídos 2026-06-27)
// combinados con proyecciones demo para marketplaces (pendientes de Multivende).
// MAÑANA: reemplazar estas constantes por fetch a la API en Railway
// (ej. `await fetch(process.env.NEXT_PUBLIC_API_URL + '/chile/overview')`).

export type Trend = { up: boolean; pct: number };

export type Kpi = {
  id: string;
  label: string;
  value: string;
  sub?: string;
  trend?: Trend;
  tone?: "default" | "up" | "down";
};

export const META = {
  brand: "SLEVE",
  title: "E-commerce Global",
  subtitle: "Consolidado Chile · sitio propio + marketplaces",
  country: "Chile",
  view: "Consolidado Chile",
  dataMode: "demo" as "demo" | "live",
  note:
    "Sitio propio (Shopify) y tráfico (GA4): datos reales 30d. Marketplaces, ads y social: demo hasta conectar Multivende/Windsor.",
};

// Selector de semanas (estilo referencia)
export const WEEKS = [
  { id: "S26", label: "S26 · 2026", range: "22 Jun – 28 Jun 2026", tag: "Semana actual (hoy)", current: true },
  { id: "S25", label: "S25 · 2026", range: "15 Jun – 21 Jun 2026", tag: "Semana analizada", analyzed: true },
  { id: "S24", label: "S24 · S-1", range: "8 Jun – 14 Jun 2026" },
  { id: "S23", label: "S23 · S-2", range: "1 Jun – 7 Jun 2026" },
  { id: "S22", label: "S22 · S-3", range: "25 May – 31 May 2026" },
  { id: "S21", label: "S21 · S-4", range: "18 May – 24 May 2026" },
];

// KPIs de la semana analizada (S25) — consolidado ecommerce
export const KPIS: Kpi[] = [
  { id: "ventas", label: "VENTAS $ — S25 '26 (CERRADA)", value: "$70.5M", sub: "15 Jun – 21 Jun 2026", trend: { up: true, pct: 23.4 }, tone: "up" },
  { id: "pedidos", label: "PEDIDOS — S25 '26", value: "2.847", sub: "AOV $24.851 · 5.261 unidades" },
  { id: "mer", label: "MER (revenue / ad spend)", value: "3.4x", sub: "Meta · Google · TikTok", trend: { up: true, pct: 6.1 }, tone: "up" },
  { id: "conv", label: "CONVERSIÓN SITIO", value: "1.25%", sub: "178k sesiones · fuga checkout 77%", trend: { up: false, pct: 4.0 }, tone: "down" },
];

// Tendencia semanal (unidades y $ CLP). Peak = Cyber fin de mayo.
export const TREND = [
  { week: "S17", unidades: 4100, ventas: 54_000_000 },
  { week: "S18", unidades: 4800, ventas: 62_000_000 },
  { week: "S19", unidades: 6200, ventas: 82_000_000 },
  { week: "S20", unidades: 7400, ventas: 96_000_000 },
  { week: "S21", unidades: 9100, ventas: 120_000_000 },
  { week: "S22", unidades: 19200, ventas: 214_000_000 }, // Cyber
  { week: "S23", unidades: 16100, ventas: 203_000_000 },
  { week: "S24", unidades: 4263, ventas: 57_000_000 },
  { week: "S25", unidades: 5261, ventas: 70_500_000 },
];

// Venta por canal (S25) — sitio propio real; marketplaces demo (vía Multivende)
export const CHANNELS = [
  { canal: "Sitio propio", ventas: 19_200_000, demo: false },
  { canal: "MercadoLibre", ventas: 16_800_000, demo: true },
  { canal: "Falabella", ventas: 12_400_000, demo: true },
  { canal: "París", ventas: 9_300_000, demo: true },
  { canal: "Ripley", ventas: 7_600_000, demo: true },
  { canal: "Walmart", ventas: 5_200_000, demo: true },
];

// Ads por plataforma (S25) — demo basado en atribución GA4
export const ADS = [
  { plataforma: "Meta", spend: 6_900_000, ventas: 21_300_000, roas: 3.1 },
  { plataforma: "Google", spend: 3_200_000, ventas: 12_600_000, roas: 3.9 },
  { plataforma: "TikTok", spend: 2_800_000, ventas: 4_900_000, roas: 1.8 },
];

// Top productos (real, Shopify 30d)
export const TOP_PRODUCTS = [
  { producto: "Pulse ANC 2Gen", ventas: 27_449_853, pedidos: 870 },
  { producto: "One 2Gen", ventas: 9_437_125, pedidos: 625 },
  { producto: "Xpods 2Gen", ventas: 8_050_464, pedidos: 388 },
  { producto: "Evo 2Gen", ventas: 7_700_566, pedidos: 279 },
  { producto: "PureX", ventas: 5_677_437, pedidos: 411 },
  { producto: "Power X 10.000 mAh", ventas: 2_474_082, pedidos: 159 },
];

// Fuentes de tráfico (real, GA4 30d)
export const TRAFFIC = [
  { fuente: "Meta", sesiones: 89858, ventas: 614, conv: 0.68 },
  { fuente: "Directo", sesiones: 23736, ventas: 206, conv: 0.87 },
  { fuente: "Google Ads", sesiones: 18329, ventas: 363, conv: 1.98 },
  { fuente: "TikTok", sesiones: 8561, ventas: 37, conv: 0.43 },
  { fuente: "Google Orgánico", sesiones: 5653, ventas: 44, conv: 0.78 },
  { fuente: "Klaviyo (email)", sesiones: 3272, ventas: 101, conv: 3.09 },
];

// Alertas / urgencias (capa 0 del DASHBOARD.md)
export const ALERTS = [
  { level: "down" as const, text: "TikTok Ads convierte 0,43% (vs Google 1,98%) — revisar inversión" },
  { level: "down" as const, text: "Fuga de checkout: 77% de quienes llegan a pagar no compran" },
  { level: "warn" as const, text: "Producto sin título con $8M y 0 pedidos — anomalía de catálogo" },
  { level: "warn" as const, text: "México casi sin tráfico (92 sesiones, 0 ventas en 7d)" },
];

export const fmtCLP = (n: number) =>
  "$" + new Intl.NumberFormat("es-CL").format(Math.round(n));

export const fmtCompact = (n: number) => {
  if (n >= 1_000_000) return "$" + (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return "$" + (n / 1_000).toFixed(0) + "K";
  return "$" + n;
};
