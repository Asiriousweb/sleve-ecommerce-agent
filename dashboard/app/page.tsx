"use client";

import { useEffect, useState } from "react";

const card = "rounded-2xl bg-ink-850 border border-ink-700/60";

const MONEDA: Record<string, string> = { Chile: "CLP", Colombia: "COP", "México": "MXN", "Perú": "PEN", EEUU: "USD" };
const BANDERA: Record<string, string> = { Chile: "🇨🇱", Colombia: "🇨🇴", "México": "🇲🇽", "Perú": "🇵🇪", EEUU: "🇺🇸" };
const ORDEN = ["Chile", "Colombia", "México", "Perú", "EEUU"];
const nf = (n: number) => new Intl.NumberFormat("es-CL").format(Math.round(n || 0));
const fmtMon = (n: number, ccy: string) =>
  new Intl.NumberFormat("es", { style: "currency", currency: ccy || "USD", maximumFractionDigits: 0 }).format(Math.round(n || 0));
const usd = (n: number) => fmtMon(n, "USD");

const TABS = [
  { id: "resumen", label: "Resumen" },
  { id: "canales", label: "Canales de venta" },
  { id: "ads", label: "Adquisición" },
  { id: "social", label: "Redes sociales" },
  { id: "cs", label: "Customer Service" },
  { id: "seo", label: "SEO / AEO / GEO" },
  { id: "acciones", label: "Acciones" },
] as const;
type TabId = (typeof TABS)[number]["id"];

const PERIODOS = [
  { id: "7d", label: "7 días", on: true },
  { id: "30d", label: "30 días", on: false },
  { id: "mes", label: "Este mes", on: false },
  { id: "yoy", label: "vs año ant.", on: false },
];

export default function Dashboard() {
  const [tab, setTab] = useState<TabId>("resumen");
  const [scope, setScope] = useState("Global");
  const [periodo, setPeriodo] = useState("7d");

  const API = process.env.NEXT_PUBLIC_API_URL
    || "https://sleve-ecommerce-agents-production.up.railway.app/api/overview";
  const [live, setLive] = useState<any>(null);
  useEffect(() => {
    fetch(API).then((r) => (r.ok ? r.json() : null))
      .then((d) => d?.fuente?.includes("vivo") && setLive(d)).catch(() => {});
  }, [API]);

  if (!live) {
    return (
      <main className="min-h-screen bg-ink-950 grid place-items-center text-gray-400">
        <div className="text-center">
          <img src="/sleve-logo.png" alt="SLEVE" className="h-10 mx-auto mb-3 opacity-90" />
          <p className="text-sm">Conectando con el robot…</p>
        </div>
      </main>
    );
  }

  const c = live.consolidado || {};
  const paises: any[] = ORDEN.filter((p) => live.paises?.[p])
    .map((p) => ({ ...live.paises[p], nombre: p, moneda: MONEDA[p] || "USD", bandera: BANDERA[p] || "" }));
  const conData = paises.filter((p) => (p.ventas_usd || 0) > 0 || (p.ad_spend_usd || 0) > 0);
  const cuadraTot = paises.filter((p) => p.cuadratura).length;
  const cuadraOk = paises.filter((p) => p.cuadratura?.ok).length;
  const acciones = buildAcciones(paises);

  const isGlobal = scope === "Global";
  const p = isGlobal ? null : paises.find((x) => x.nombre === scope);
  const scoped = isGlobal ? conData : (p ? [p] : []);

  return (
    <main className="min-h-screen bg-ink-950 px-5 py-5 md:px-8 md:py-6 max-w-[1500px] mx-auto">
      {/* Header */}
      <header className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div className="flex items-center gap-3">
          <img src="/sleve-logo.png" alt="SLEVE" className="h-8" />
          <div>
            <h1 className="font-bold leading-tight">E-commerce Cockpit</h1>
            <p className="text-[11px] text-accent-up">
              🟢 En vivo · {new Date(live.actualizado).toLocaleString("es-CL")} · cuadratura {cuadraOk}/{cuadraTot}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {/* Scope (Global / país) */}
          <select value={scope} onChange={(e) => setScope(e.target.value)}
            className="rounded-xl bg-ink-850 border border-ink-700/60 px-3 py-2 text-sm text-white font-semibold">
            <option value="Global">🌎 Global (consolidado)</option>
            {paises.map((x) => <option key={x.nombre} value={x.nombre}>{x.bandera} {x.nombre}</option>)}
          </select>
          {/* Período */}
          <div className="inline-flex rounded-xl bg-ink-850 border border-ink-700/60 p-1">
            {PERIODOS.map((pe) => (
              <button key={pe.id} disabled={!pe.on} onClick={() => pe.on && setPeriodo(pe.id)}
                title={pe.on ? "" : "Próximamente (requiere histórico)"}
                className={`px-2.5 py-1.5 text-[11px] rounded-lg transition ${periodo === pe.id ? "bg-ink-700 text-white" : pe.on ? "text-gray-400 hover:text-gray-200" : "text-gray-600 cursor-not-allowed"}`}>
                {pe.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <ConexionesStrip />

      {/* Tabs */}
      <nav className="mt-4 flex gap-5 border-b border-ink-700/60 overflow-x-auto">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`pb-3 text-sm whitespace-nowrap transition border-b-2 -mb-px ${tab === t.id ? "text-white border-white" : "text-gray-500 border-transparent hover:text-gray-300"}`}>
            {t.label}{t.id === "acciones" && acciones.length ? ` (${acciones.length})` : ""}
          </button>
        ))}
      </nav>

      <div className="mt-1 text-[11px] text-gray-500">
        Mostrando: <b className="text-gray-300">{isGlobal ? "Global (consolidado USD)" : `${p?.bandera} ${scope}`}</b> · últimos 7 días
      </div>

      {tab === "resumen" && (isGlobal
        ? <ResumenGlobal c={c} paises={paises} conData={conData} cuadraOk={cuadraOk} cuadraTot={cuadraTot} acciones={acciones} setTab={setTab} />
        : <ResumenPais p={p} />)}
      {tab === "canales" && <Canales scoped={scoped} isGlobal={isGlobal} />}
      {tab === "ads" && <Adquisicion c={c} scoped={scoped} isGlobal={isGlobal} />}
      {tab === "social" && <Proximamente titulo="Redes sociales (Meta / Instagram orgánico)" detalle="Tienes los accesos a las páginas de Facebook e Instagram. Aquí verás seguidores, alcance, engagement y rendimiento de publicaciones por país. Falta cablear el pull de Meta orgánico." />}
      {tab === "cs" && <Proximamente titulo="Customer Service (Gorgias)" detalle="Tickets pendientes, tiempos de primera respuesta y resolución, CSAT por país. Pendiente: recuperar acceso a Gorgias + API key." />}
      {tab === "seo" && <Seo scoped={scoped} isGlobal={isGlobal} />}
      {tab === "acciones" && <Acciones acciones={acciones} />}

      <footer className="mt-10 mb-4 flex items-center gap-2 text-[11px] text-gray-600">
        <img src="/sleve-logo.png" alt="SLEVE" className="h-4 opacity-60" />
        <span>· {live.nota} · consolidado en USD (FX del día) · Cockpit v0.4</span>
      </footer>
    </main>
  );
}

/* ---------- RESUMEN ---------- */
function ResumenGlobal({ c, paises, conData, cuadraOk, cuadraTot, acciones, setTab }: any) {
  const kpis = [
    { label: "Venta total (USD)", value: usd(c.ventas_usd), sub: `${nf(c.pedidos)} pedidos` },
    { label: "Gasto Ads (USD)", value: usd(c.ad_spend_usd), sub: "Meta + Google" },
    { label: "MER blended", value: (c.mer_usd ?? 0) + "x", tone: c.mer_usd >= 3 ? "up" : "down", sub: "venta / ads" },
    { label: "Contribución (USD)", value: usd(c.contrib_usd), sub: "venta − ads" },
    { label: "AOV (USD)", value: usd(c.aov_usd) },
    { label: "CPA (USD)", value: usd(c.cpa_usd), sub: "costo por pedido" },
    { label: "Conversión", value: (c.conversion ?? 0) + "%", tone: c.conversion >= 1 ? "up" : "down", sub: `${nf(c.sesiones)} sesiones` },
    { label: "MER (solo Meta)", value: (c.mer_meta_usd ?? 0) + "x" },
  ];
  return (
    <>
      <section className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">{kpis.map((k) => <Kpi key={k.label} {...k} />)}</section>
      <Section title="Venta por país (USD · 7d)">
        <Bars data={conData.map((p: any) => ({ label: `${p.bandera} ${p.nombre}`, value: p.ventas_usd || 0 }))} fmt={usd} />
      </Section>
      <PaisesTabla paises={paises} cuadraOk={cuadraOk} cuadraTot={cuadraTot} />
      {acciones.length > 0 && (
        <Section title={`Acciones rápidas · top ${Math.min(3, acciones.length)}`}>
          <ul className="space-y-2">{acciones.slice(0, 3).map((a: any, i: number) => <AccionRow key={i} a={a} />)}</ul>
          <button onClick={() => setTab("acciones")} className="mt-3 text-[11px] text-accent-up hover:underline">Ver todas ({acciones.length}) →</button>
        </Section>
      )}
    </>
  );
}

function ResumenPais({ p }: any) {
  if (!p) return <p className="mt-6 text-gray-500">Sin datos.</p>;
  const stats = [
    { label: "Venta (local)", value: p.ventas_clp ? fmtMon(p.ventas_clp, p.moneda) : "—" },
    { label: "Venta (USD)", value: p.ventas_usd ? usd(p.ventas_usd) : "—" },
    { label: "Pedidos", value: nf(p.pedidos ?? 0) },
    { label: "AOV", value: p.aov ? fmtMon(p.aov, p.moneda) : "—" },
    { label: "Sesiones", value: nf(p.sesiones ?? 0) },
    { label: "Conversión", value: (p.conversion ?? 0) + "%", tone: p.conversion >= 1 ? "up" : "down" },
    { label: "Ads (USD)", value: p.ad_spend_usd ? usd(p.ad_spend_usd) : "—" },
    { label: "MER", value: p.mer_usd ? p.mer_usd + "x" : "—", tone: p.mer_usd >= 3 ? "up" : "down" },
    { label: "Contribución (USD)", value: p.contrib_usd != null ? usd(p.contrib_usd) : "—" },
    { label: "Email (Klaviyo)", value: p.klaviyo?.email_revenue ? fmtMon(p.klaviyo.email_revenue, p.moneda) : "—" },
    { label: "Gasto Meta", value: p.meta_spend != null ? fmtMon(p.meta_spend, p.meta_moneda || p.moneda) : "—" },
    { label: "Gasto Google", value: p.ad_spend ? fmtMon(p.ad_spend, p.gads_moneda || p.moneda) : "—" },
  ];
  return (
    <>
      <section className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">{stats.map((s) => <Kpi key={s.label} {...s} />)}</section>
      <div className="mt-3 flex items-center gap-3">
        <span className="text-[11px] text-gray-500">Cuadratura:</span>
        {p.cuadratura ? (
          <span className={p.cuadratura.ok ? "text-accent-up text-xs" : "text-accent-down text-xs"}>
            {p.cuadratura.ok ? "✓" : "✗"} GA4 {p.cuadratura.ga4_transacciones} {p.cuadratura.ok ? "≤" : ">"} Shopify {p.cuadratura.shopify_pedidos}
          </span>
        ) : <span className="text-gray-600 text-xs">— sin ventas</span>}
      </div>
      {p.traffic?.length > 0 && (
        <Section title="Fuentes de tráfico (GA4 · 7d)">
          <ul className="divide-y divide-ink-700/50">
            {p.traffic.map((t: any) => (
              <li key={t.fuente} className="flex items-center justify-between py-2.5">
                <span className="text-sm text-gray-200">{t.fuente}</span>
                <span className="flex items-center gap-4 text-sm">
                  <span className="text-gray-400">{nf(t.sesiones)} ses.</span>
                  <span className={`w-14 text-right font-semibold ${t.conv >= 1.5 ? "text-accent-up" : t.conv < 0.7 ? "text-accent-down" : "text-gray-300"}`}>{t.conv.toFixed(2)}%</span>
                </span>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}

function PaisesTabla({ paises, cuadraOk, cuadraTot }: any) {
  return (
    <section className="mt-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Consolidado por país</h2>
        <span className={`text-[11px] font-semibold ${cuadraOk === cuadraTot ? "text-accent-up" : "text-accent-down"}`}>Cuadratura {cuadraOk}/{cuadraTot}</span>
      </div>
      <div className={`${card} overflow-x-auto`}>
        <table className="w-full text-sm min-w-[860px]">
          <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
            <th className="text-left font-semibold px-4 py-3">País</th>
            <th className="text-right font-semibold px-4 py-3">Venta USD</th>
            <th className="text-right font-semibold px-4 py-3">Pedidos</th>
            <th className="text-right font-semibold px-4 py-3">Conv.</th>
            <th className="text-right font-semibold px-4 py-3">Ads USD</th>
            <th className="text-right font-semibold px-4 py-3">MER</th>
            <th className="text-right font-semibold px-4 py-3">Contrib. USD</th>
            <th className="text-right font-semibold px-4 py-3">Cuadr.</th>
          </tr></thead>
          <tbody>
            {paises.map((p: any) => (
              <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre}</td>
                <td className="px-4 py-3 text-right text-gray-100 font-semibold">{p.ventas_usd ? usd(p.ventas_usd) : "—"}</td>
                <td className="px-4 py-3 text-right text-gray-300">{nf(p.pedidos ?? 0)}</td>
                <td className={`px-4 py-3 text-right font-semibold ${p.conversion >= 1.5 ? "text-accent-up" : p.conversion < 0.7 ? "text-accent-down" : "text-gray-300"}`}>{(p.conversion ?? 0).toFixed(2)}%</td>
                <td className="px-4 py-3 text-right text-gray-400">{p.ad_spend_usd ? usd(p.ad_spend_usd) : "—"}</td>
                <td className={`px-4 py-3 text-right font-semibold ${p.mer_usd >= 3 ? "text-accent-up" : p.mer_usd > 0 && p.mer_usd < 2 ? "text-accent-down" : "text-gray-300"}`}>{p.mer_usd ? p.mer_usd + "x" : "—"}</td>
                <td className="px-4 py-3 text-right text-gray-300">{p.contrib_usd != null ? usd(p.contrib_usd) : "—"}</td>
                <td className="px-4 py-3 text-right">{p.cuadratura?.ok ? <span className="text-accent-up text-xs">✓</span> : p.cuadratura ? <span className="text-accent-down text-xs">✗</span> : <span className="text-gray-600 text-xs">—</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/* ---------- CANALES ---------- */
function Canales({ scoped, isGlobal }: any) {
  const ventaUsd = scoped.reduce((s: number, p: any) => s + (p.ventas_usd || 0), 0);
  const pedidos = scoped.reduce((s: number, p: any) => s + (p.pedidos || 0), 0);
  return (
    <>
      <Section title="Sitio propio (Shopify) — conectado 🟢">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <Kpi label="Venta sitio propio (USD)" value={usd(ventaUsd)} />
          <Kpi label="Pedidos" value={nf(pedidos)} />
          <Kpi label="Tiendas" value={isGlobal ? "6" : "1"} sub="vía Shopify directo" />
        </div>
      </Section>
      <Section title="Marketplaces (vía Multivende)">
        <Proximamente inline titulo="Mercado Libre · Falabella · Walmart · Ripley · París"
          detalle="Al conectar Multivende (correo enviado a api@multivende.com) verás venta, stock y precio de cada marketplace por país — y se completará la cuadratura de venta total y el P&L por canal." />
      </Section>
    </>
  );
}

/* ---------- ADQUISICIÓN ---------- */
function Adquisicion({ c, scoped, isGlobal }: any) {
  return (
    <>
      {isGlobal && (
        <section className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          <Kpi label="Gasto Ads (USD)" value={usd(c.ad_spend_usd)} sub="Meta + Google" />
          <Kpi label="Gasto Meta (USD)" value={usd(c.meta_spend_usd)} />
          <Kpi label="MER blended" value={(c.mer_usd ?? 0) + "x"} tone={c.mer_usd >= 3 ? "up" : "down"} />
          <Kpi label="CPA (USD)" value={usd(c.cpa_usd)} />
        </section>
      )}
      <Section title="Ads por país (USD)">
        <div className={`${card} overflow-x-auto`}>
          <table className="w-full text-sm min-w-[600px]">
            <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
              <th className="text-left font-semibold px-4 py-3">País</th>
              <th className="text-right font-semibold px-4 py-3">Meta</th>
              <th className="text-right font-semibold px-4 py-3">Google</th>
              <th className="text-right font-semibold px-4 py-3">Total Ads</th>
              <th className="text-right font-semibold px-4 py-3">Venta</th>
              <th className="text-right font-semibold px-4 py-3">MER</th>
            </tr></thead>
            <tbody>
              {scoped.map((p: any) => (
                <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                  <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{p.meta_spend_usd ? usd(p.meta_spend_usd) : "—"}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{p.gads_spend_usd ? usd(p.gads_spend_usd) : "—"}</td>
                  <td className="px-4 py-3 text-right text-gray-100 font-semibold">{p.ad_spend_usd ? usd(p.ad_spend_usd) : "—"}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{p.ventas_usd ? usd(p.ventas_usd) : "—"}</td>
                  <td className={`px-4 py-3 text-right font-semibold ${p.mer_usd >= 3 ? "text-accent-up" : p.mer_usd > 0 && p.mer_usd < 2 ? "text-accent-down" : "text-gray-300"}`}>{p.mer_usd ? p.mer_usd + "x" : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
      <Section title="Eficiencia y creativos">
        <Proximamente inline titulo="CPM · CTR · creativos saturados (fatiga)"
          detalle="Próximamente: CPM, CTR y detección de creativos/publicaciones saturados (frecuencia alta + CTR cayendo). Requiere el pull de Meta a nivel de anuncio/creativo (hoy traemos gasto a nivel cuenta). TikTok Ads también pendiente." />
      </Section>
    </>
  );
}

/* ---------- SEO / AEO / GEO ---------- */
function Seo({ scoped, isGlobal }: any) {
  const conSC = scoped.filter((p: any) => p.search_console);
  return (
    <>
      <Section title="Search Console (búsqueda orgánica) — conectado 🟢">
        {conSC.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[520px]">
              <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
                <th className="text-left font-semibold px-4 py-3">País</th>
                <th className="text-right font-semibold px-4 py-3">Clics</th>
                <th className="text-right font-semibold px-4 py-3">Impresiones</th>
                <th className="text-right font-semibold px-4 py-3">CTR</th>
                <th className="text-right font-semibold px-4 py-3">Posición</th>
              </tr></thead>
              <tbody>
                {conSC.map((p: any) => (
                  <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                    <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre}</td>
                    <td className="px-4 py-3 text-right text-gray-100 font-semibold">{nf(p.search_console.clicks)}</td>
                    <td className="px-4 py-3 text-right text-gray-300">{nf(p.search_console.impressions)}</td>
                    <td className="px-4 py-3 text-right text-gray-400">{p.search_console.ctr}%</td>
                    <td className="px-4 py-3 text-right text-gray-400">{p.search_console.position}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="text-sm text-gray-500">{isGlobal ? "Sin datos de búsqueda en el período." : "Este país aún sin tráfico de búsqueda."}</p>}
      </Section>
      <Section title="AEO / GEO — búsqueda en IA">
        <Proximamente inline titulo="Answer Engine Optimization (AEO) y Generative Engine Optimization (GEO)"
          detalle="Próximamente: visibilidad de SLEVE en buscadores de IA (ChatGPT, Perplexity, Google AI Overviews). Mediremos si la marca aparece en respuestas generativas y en qué consultas — la nueva frontera del descubrimiento." />
      </Section>
    </>
  );
}

/* ---------- ACCIONES ---------- */
function Acciones({ acciones }: any) {
  if (!acciones.length) return <p className="mt-6 text-gray-500">Sin urgencias detectadas. 🟢</p>;
  return (
    <Section title={`Acciones rápidas y urgencias (${acciones.length})`}>
      <ul className="space-y-2">{acciones.map((a: any, i: number) => <AccionRow key={i} a={a} />)}</ul>
    </Section>
  );
}

function buildAcciones(paises: any[]) {
  const A: { level: "down" | "warn" | "info"; text: string }[] = [];
  for (const p of paises) {
    if (p.cuadratura && !p.cuadratura.ok) A.push({ level: "down", text: `Descuadre en ${p.nombre}: GA4 ${p.cuadratura.ga4_transacciones} > Shopify ${p.cuadratura.shopify_pedidos} pedidos — revisar tracking.` });
    if ((p.roas || 0) > 15) A.push({ level: "warn", text: `ROAS Google en ${p.nombre} = ${p.roas}x (sospechoso) — revisar config del valor de conversión.` });
    if ((p.sesiones || 0) > 300 && (p.conversion || 0) < 0.7 && (p.pedidos || 0) > 0) A.push({ level: "warn", text: `Conversión baja en ${p.nombre} (${(p.conversion ?? 0).toFixed(2)}%) con ${nf(p.sesiones)} sesiones — oportunidad CRO.` });
    if ((p.sesiones || 0) > 200 && (p.pedidos || 0) === 0) A.push({ level: "down", text: `${p.nombre}: ${nf(p.sesiones)} sesiones y 0 ventas — definir si activar o pausar inversión.` });
    if ((p.mer_usd || 0) > 0 && (p.mer_usd || 0) < 2) A.push({ level: "warn", text: `MER bajo en ${p.nombre} (${p.mer_usd}x) — ads poco rentables, revisar campañas.` });
    const tk = (p.traffic || []).find((t: any) => /tiktok/i.test(t.fuente));
    if (tk && tk.conv < 0.5 && tk.sesiones > 500) A.push({ level: "warn", text: `TikTok en ${p.nombre} convierte ${tk.conv.toFixed(2)}% con ${nf(tk.sesiones)} sesiones — revisar inversión.` });
  }
  A.push({ level: "info", text: "Multivende: correo enviado → al llegar las credenciales se conectan los marketplaces (hoy sin data)." });
  A.push({ level: "info", text: "Telegram: cargar TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID en Railway para que llegue todo al teléfono." });
  A.push({ level: "info", text: "Google Business Profile: esperando aprobación de acceso API; crear perfiles CO/MX/PE con las bodegas." });
  A.push({ level: "info", text: "Cargar créditos en Anthropic → enciende el loop nocturno + control por Telegram en lenguaje natural." });
  const order = { down: 0, warn: 1, info: 2 };
  return A.sort((a, b) => order[a.level] - order[b.level]);
}

/* ---------- UI bits ---------- */
function Kpi({ label, value, sub, tone }: any) {
  const color = tone === "down" ? "text-accent-down" : tone === "up" ? "text-accent-up" : "text-white";
  return (
    <div className={`${card} p-4`}>
      <div className={`text-2xl md:text-3xl font-black tracking-tight ${color}`}>{value}</div>
      <div className="mt-1 text-[10px] font-semibold tracking-wider text-gray-500 uppercase">{label}</div>
      {sub && <div className="text-[11px] text-gray-500 mt-0.5">{sub}</div>}
    </div>
  );
}
function Section({ title, children }: any) {
  return (
    <section className="mt-6">
      <h2 className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">{title}</h2>
      <div className={`${card} p-4`}>{children}</div>
    </section>
  );
}
function Bars({ data, fmt }: { data: { label: string; value: number }[]; fmt: (n: number) => string }) {
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <div className="space-y-2 py-1">
      {data.map((d) => (
        <div key={d.label} className="flex items-center gap-3">
          <span className="w-28 text-sm text-gray-300 shrink-0">{d.label}</span>
          <div className="flex-1 h-6 bg-ink-800 rounded-lg overflow-hidden"><div className="h-full rounded-lg bg-accent-up/80" style={{ width: `${(d.value / max) * 100}%` }} /></div>
          <span className="w-24 text-right text-xs text-gray-300">{fmt(d.value)}</span>
        </div>
      ))}
    </div>
  );
}
function AccionRow({ a }: { a: { level: string; text: string } }) {
  const dot = a.level === "down" ? "bg-accent-down" : a.level === "warn" ? "bg-amber-400" : "bg-sky-400";
  return (
    <li className="flex items-start gap-3"><span className={`h-2 w-2 rounded-full shrink-0 mt-1.5 ${dot}`} /><span className="text-sm text-gray-300">{a.text}</span></li>
  );
}
function Proximamente({ titulo, detalle, inline }: { titulo: string; detalle: string; inline?: boolean }) {
  return (
    <div className={inline ? "text-center py-4" : `${card} p-8 text-center mt-4`}>
      <div className="text-2xl mb-1">🔌</div>
      <div className="text-gray-200 font-semibold">{titulo}</div>
      <p className="text-sm text-gray-500 mt-1 max-w-xl mx-auto">{detalle}</p>
      <span className="inline-block mt-3 text-[11px] rounded-md bg-ink-800 text-gray-400 px-2 py-1">Próximamente</span>
    </div>
  );
}
function ConexionesStrip() {
  const ok = ["Shopify", "Meta", "Klaviyo", "GA4", "Search Console", "Google Ads"];
  const pend = ["Multivende", "Business Profile", "TikTok", "Gorgias", "Redes orgánico"];
  return (
    <div className="mt-3 flex flex-wrap gap-1.5 text-[10px]">
      {ok.map((s) => <span key={s} className="rounded-md bg-accent-up/15 text-accent-up px-2 py-1">🟢 {s}</span>)}
      {pend.map((s) => <span key={s} className="rounded-md bg-ink-800 text-gray-500 px-2 py-1">○ {s}</span>)}
    </div>
  );
}
