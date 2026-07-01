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
  { id: "catalogo", label: "Publicaciones" },
  { id: "ads", label: "Adquisición" },
  { id: "social", label: "Redes sociales" },
  { id: "cs", label: "Customer Service" },
  { id: "seo", label: "SEO / AEO / GEO" },
  { id: "competidores", label: "Competidores" },
  { id: "tendencias", label: "Tendencias" },
  { id: "acciones", label: "Acciones" },
] as const;
type TabId = (typeof TABS)[number]["id"];

const PERIODOS = [
  { id: "7d", label: "7 días", on: true },
  { id: "30d", label: "30 días", on: true },
  { id: "mes", label: "Este mes", on: true },
  { id: "mes_anterior", label: "Mes anterior", on: true },
  { id: "yoy", label: "vs año ant.", on: true },
];
const pct = (n: number | null) => (n == null ? "—" : (n >= 0 ? "+" : "") + n + "%");

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
          <img src="/sleve-logo.png" alt="SLEVE" className="h-10 mx-auto mb-3 opacity-90 animate-pulse" />
          <p className="text-sm">Cargando datos…</p>
        </div>
      </main>
    );
  }

  // El período es un FILTRO GLOBAL: selecciona el dataset; toda la estructura es idéntica.
  const periodos = live.periodos || {};
  const ds = periodo === "yoy"
    ? (periodos["30d"] || {})                                   // YoY usa el dataset de 30d + deltas
    : (periodos[periodo] || (periodo === "7d"
        ? { paises: live.paises, consolidado: live.consolidado } // fallback retrocompat
        : {}));
  const yoy = periodo === "yoy" ? (live.yoy || null) : null;

  const c = ds.consolidado || {};
  const paises: any[] = ORDEN.filter((p) => ds.paises?.[p])
    .map((p) => ({ ...ds.paises[p], nombre: p, moneda: MONEDA[p] || "USD", bandera: BANDERA[p] || "" }));
  const conData = paises.filter((p) => (p.ventas_usd || 0) > 0 || (p.ad_spend_usd || 0) > 0);
  const cuadraTot = paises.filter((p) => p.cuadratura).length;
  const cuadraOk = paises.filter((p) => p.cuadratura?.ok).length;
  const acciones = buildAcciones(paises, live.catalogo || {});

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
            <h1 className="font-bold leading-tight">E-commerce</h1>
            <p className="text-[11px] text-gray-400">
              En vivo · {new Date(live.actualizado).toLocaleString("es-CL")} · cuadratura {cuadraOk}/{cuadraTot}
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
      <nav className="mt-7 flex gap-6 border-b border-ink-700/60 overflow-x-auto">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`pb-3 text-sm whitespace-nowrap transition border-b-2 -mb-px ${tab === t.id ? "text-white border-white" : "text-gray-500 border-transparent hover:text-gray-300"}`}>
            {t.label}{t.id === "acciones" && acciones.length ? ` (${acciones.length})` : ""}
          </button>
        ))}
      </nav>

      <div className="mt-1 text-[11px] text-gray-500">
        Mostrando: <b className="text-gray-300">{isGlobal ? "Global (consolidado USD)" : `${p?.bandera} ${scope}`}</b> · {periodo === "yoy" ? "comparativo año vs año (30 días)" : periodo === "30d" ? "últimos 30 días" : periodo === "mes" ? "este mes (del día 1 a hoy)" : periodo === "mes_anterior" ? (ds.rango || "mes anterior") : "últimos 7 días"}
      </div>

      {!ds.paises ? (
        <p className="mt-6 text-gray-500">El consolidado de {periodo === "mes" ? "este mes" : periodo === "yoy" ? "año vs año" : "30 días"} se calcula una vez al día — aún no disponible. Vuelve en un rato.</p>
      ) : <>
      {tab === "resumen" && (isGlobal
        ? <ResumenGlobal c={c} paises={paises} conData={conData} cuadraOk={cuadraOk} cuadraTot={cuadraTot} acciones={acciones} setTab={setTab} historia={live.historia || []} periodoLabel={ds.rango || ""} yoy={yoy} />
        : <ResumenPais p={p} periodoLabel={ds.rango || ""} yoy={yoy} />)}
      {tab === "canales" && <Canales scoped={scoped} isGlobal={isGlobal} productos={live.productos || {}} scope={scope} />}
      {tab === "catalogo" && <Publicaciones catalogo={live.catalogo || {}} scope={scope} />}
      {tab === "ads" && <Adquisicion c={c} scoped={scoped} isGlobal={isGlobal} />}
      {tab === "social" && <Redes scoped={scoped} youtube={live.youtube || {}} scope={scope} />}
      {tab === "cs" && <Proximamente titulo="Customer Service (Gorgias)" detalle="Tickets pendientes, tiempos de primera respuesta y resolución, CSAT por país. Pendiente: recuperar acceso a Gorgias + API key." />}
      {tab === "seo" && <Seo scoped={scoped} isGlobal={isGlobal} />}
      {tab === "competidores" && <Proximamente titulo="Inteligencia de competidores y mercado" detalle="Aquí verás cómo te comparas con la competencia y el mercado: precios, share, productos top y demanda. Dos vías: (1) conectar Nubimetrics (market intelligence de Mercado Libre — ventas y tendencias del mercado), y (2) carga manual de data de competidores que tú quieras seguir. Ideal para el especialista de inteligencia/tendencias." />}
      {tab === "tendencias" && <Tendencias tendencias={live.tendencias || {}} scope={scope} />}
      {tab === "acciones" && <Acciones acciones={acciones} />}
      </>}

      <footer className="mt-10 mb-4 flex items-center gap-2 text-[11px] text-gray-600">
        <img src="/sleve-logo.png" alt="SLEVE" className="h-4 opacity-60" />
        <span>· {live.nota} · consolidado en USD (FX del día) · SLEVE E-commerce v0.4</span>
      </footer>
    </main>
  );
}

/* ---------- RESUMEN (simple, por canal) ---------- */
function CanalCard({ icon, nombre, venta, sub, extra, tone }: any) {
  return (
    <div className={`${card} p-4`}>
      <div className="flex items-center gap-2 text-sm text-gray-300 font-medium">{icon} {nombre}</div>
      <div className={`mt-2 text-2xl md:text-3xl font-black tracking-tight ${tone === "off" ? "text-gray-500" : "text-white"}`}>{venta}</div>
      {sub && <div className="text-[11px] text-gray-500 mt-0.5">{sub}</div>}
      {extra && <div className="text-[11px] text-gray-400 mt-1">{extra}</div>}
    </div>
  );
}
function ResumenGlobal({ c, paises, conData, cuadraOk, cuadraTot, acciones, setTab, historia, periodoLabel, yoy }: any) {
  const L = periodoLabel || "período";
  const cc = yoy?.consolidado;
  const vSitio = c.ventas_sitio_usd ?? c.ventas_usd ?? 0;
  const vMeli = c.ventas_meli_usd ?? 0;
  const vTotal = c.ventas_total_usd ?? (vSitio + vMeli);
  const pedTotal = c.pedidos_total ?? c.pedidos ?? 0;
  const adUsd = c.ad_spend_usd ?? 0;
  const metaUsd = c.meta_spend_usd ?? 0;
  const googleUsd = Math.max(0, adUsd - metaUsd);
  const merTotal = c.mer_total_usd ?? c.mer_usd ?? 0;
  // KPIs headline (pocos, los que mandan)
  const kpis = [
    { label: `Venta total (USD · ${L})`, value: usd(vTotal), sub: `${nf(pedTotal)} pedidos · sitio + marketplaces` },
    { label: "Gasto Ads (USD)", value: usd(adUsd), sub: "Meta + Google" },
    { label: "MER blended", value: merTotal + "x", tone: merTotal >= 3 ? "up" : "down", sub: "venta total / ads" },
    { label: "Contribución (USD)", value: usd(vTotal - adUsd), sub: "venta − ads" },
  ];
  // venta por país = sitio + ML
  const ventaPais = ORDEN.filter((p) => paises.find((x: any) => x.nombre === p))
    .map((p) => { const x = paises.find((y: any) => y.nombre === p); return { label: `${x.bandera} ${x.nombre}`, value: (x.ventas_usd || 0) + (x.meli_ventas_usd || 0) }; })
    .filter((d) => d.value > 0);
  return (
    <>
      {cc && (
        <div className="mt-4 rounded-xl bg-ink-900/50 border border-ink-800 px-4 py-3 flex flex-wrap gap-x-8 gap-y-1 text-sm">
          <span className="text-[11px] uppercase tracking-widest text-gray-500 font-semibold w-full">Crecimiento vs mismo período año anterior</span>
          <span className="text-gray-300">Venta: <b className={cc.rev_growth >= 0 ? "text-accent-up" : "text-accent-down"}>{pct(cc.rev_growth)}</b> <span className="text-gray-500">({usd(cc.rev_now_usd)} vs {usd(cc.rev_prev_usd)})</span></span>
          <span className="text-gray-300">Tráfico: <b className={cc.ses_growth >= 0 ? "text-accent-up" : "text-accent-down"}>{pct(cc.ses_growth)}</b> <span className="text-gray-500">({nf(cc.ses_now)} vs {nf(cc.ses_prev)} sesiones)</span></span>
        </div>
      )}
      <section className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">{kpis.map((k) => <Kpi key={k.label} {...k} />)}</section>

      <Section title={`Cómo va cada canal · ${L}`}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <CanalCard icon="🛒" nombre="Sitio propio (Shopify)" venta={usd(vSitio)}
            sub={`${nf(c.pedidos_sitio ?? c.pedidos ?? 0)} pedidos`} extra={`Conversión ${(c.conversion ?? 0)}% · ${nf(c.sesiones ?? 0)} sesiones`} />
          <CanalCard icon="🟡" nombre="Mercado Libre" venta={usd(vMeli)} tone={vMeli > 0 ? "" : "off"}
            sub={`${nf(c.pedidos_meli ?? 0)} pedidos`} extra={`${nf(c.publicaciones_meli ?? 0)} publicaciones activas`} />
          <CanalCard icon="🏬" nombre="Otros marketplaces" venta="—" tone="off"
            sub="Falabella · Walmart · Ripley · París · Hites" extra="Próximamente vía Multivende" />
        </div>
        <p className="text-[11px] text-gray-500 mt-2">Venta total = sitio propio + Mercado Libre (marketplaces restantes al conectar Multivende). Mercado Libre {vMeli > vSitio ? "ya supera al sitio propio" : "aporta fuerte"} en este período.</p>
      </Section>

      <Section title={`Venta por país · sitio + Mercado Libre (USD · ${L})`}>
        <Bars data={ventaPais} fmt={usd} />
      </Section>

      <Section title={`Gasto publicitario por plataforma (USD · ${L})`}>
        <Bars data={[{ label: "📘 Meta", value: metaUsd }, { label: "🔍 Google", value: googleUsd }]} fmt={usd} />
        <p className="text-[11px] text-gray-500 mt-2">Publicidad de Mercado Libre (Product Ads) y TikTok Ads: próximamente. Detalle de campañas y creativos en la pestaña Adquisición.</p>
      </Section>

      {acciones.length > 0 && (
        <Section title={`Insights principales · top ${Math.min(4, acciones.length)}`}>
          <ul className="space-y-2">{acciones.slice(0, 4).map((a: any, i: number) => <AccionRow key={i} a={a} />)}</ul>
          <button onClick={() => setTab("acciones")} className="mt-3 text-[11px] text-accent-up hover:underline">Ver todas ({acciones.length}) →</button>
        </Section>
      )}
    </>
  );
}

function ResumenPais({ p, periodoLabel, yoy }: any) {
  if (!p) return <p className="mt-6 text-gray-500">Sin datos.</p>;
  const L = periodoLabel || "período";
  const g = yoy?.paises?.[p.nombre];
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
      {g && (
        <div className="mt-4 rounded-xl bg-ink-900/50 border border-ink-800 px-4 py-3 flex flex-wrap gap-x-8 gap-y-1 text-sm">
          <span className="text-[11px] uppercase tracking-widest text-gray-500 font-semibold w-full">Vs mismo período año anterior</span>
          <span className="text-gray-300">Venta: <b className={g.rev_growth >= 0 ? "text-accent-up" : "text-accent-down"}>{pct(g.rev_growth)}</b> <span className="text-gray-500">({usd(g.rev_now_usd)} vs {usd(g.rev_prev_usd)})</span></span>
          <span className="text-gray-300">Tráfico: <b className={g.ses_growth >= 0 ? "text-accent-up" : "text-accent-down"}>{pct(g.ses_growth)}</b> <span className="text-gray-500">({nf(g.ses_now)} vs {nf(g.ses_prev)} sesiones)</span></span>
        </div>
      )}
      <Section title="Cómo va cada canal">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <CanalCard icon="🛒" nombre="Sitio propio (Shopify)" venta={p.ventas_usd ? usd(p.ventas_usd) : "—"}
            sub={`${nf(p.pedidos ?? 0)} pedidos`} extra={`Conversión ${(p.conversion ?? 0)}%`} />
          <CanalCard icon="🟡" nombre="Mercado Libre" venta={p.meli ? usd(p.meli_ventas_usd || 0) : "—"} tone={p.meli?.pedidos ? "" : "off"}
            sub={p.meli ? `${nf(p.meli.pedidos)} pedidos` : "no conectado"} extra={p.meli ? `${nf(p.meli.publicaciones ?? 0)} publicaciones` : ""} />
          <CanalCard icon="🏬" nombre="Otros marketplaces" venta="—" tone="off" sub="Falabella · Ripley · París · Hites…" extra="Próximamente vía Multivende" />
        </div>
      </Section>
      <p className="text-[11px] text-gray-500 mt-4 mb-1 uppercase tracking-widest">Detalle sitio propio</p>
      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">{stats.map((s) => <Kpi key={s.label} {...s} />)}</section>
      <div className="mt-3 flex items-center gap-3">
        <span className="text-[11px] text-gray-500">Cuadratura:</span>
        {p.cuadratura ? (
          <span className={p.cuadratura.ok ? "text-accent-up text-xs" : "text-accent-down text-xs"}>
            {p.cuadratura.ok ? "✓" : "✗"} GA4 {p.cuadratura.ga4_transacciones} {p.cuadratura.ok ? "≤" : ">"} Shopify {p.cuadratura.shopify_pedidos}
          </span>
        ) : <span className="text-gray-600 text-xs">— sin ventas</span>}
      </div>
      <FuentesVenta paises={[p]} titulo={`De dónde viene la venta · por canal (USD · ${L})`} />
      {p.traffic?.length > 0 && (
        <Section title={`Fuentes de tráfico (GA4 · ${L})`}>
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
function Canales({ scoped, isGlobal, productos, scope }: any) {
  const ventaUsd = scoped.reduce((s: number, p: any) => s + (p.ventas_usd || 0), 0);
  const pedidos = scoped.reduce((s: number, p: any) => s + (p.pedidos || 0), 0);
  // Productos top: por país si hay scope; si Global, consolida por nombre en USD
  const paisesProd = ORDEN.filter((p) => productos[p]?.length).filter((p) => isGlobal || p === scope);
  let ranking: any[] = [];
  if (isGlobal) {
    const m: any = {};
    for (const p of paisesProd) for (const it of productos[p]) {
      const d = (m[it.nombre] = m[it.nombre] || { nombre: it.nombre, unidades: 0, ventas_usd: 0 });
      d.unidades += it.unidades; d.ventas_usd += it.ventas_usd;
    }
    ranking = Object.values(m).sort((a: any, b: any) => b.ventas_usd - a.ventas_usd).slice(0, 12);
  } else if (paisesProd.length) {
    ranking = (productos[scope] || []).map((it: any) => ({ ...it }));
  }
  return (
    <>
      <Section title="Sitio propio (Shopify) — conectado 🟢">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <Kpi label="Venta sitio propio (USD)" value={usd(ventaUsd)} />
          <Kpi label="Pedidos" value={nf(pedidos)} />
          <Kpi label="Tiendas" value={isGlobal ? "6" : "1"} sub="vía Shopify directo" />
        </div>
      </Section>
      <Section title="Productos más vendidos · últimos 7 días 🟢">
        {ranking.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[480px]">
              <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
                <th className="text-left font-semibold px-4 py-2.5">#</th>
                <th className="text-left font-semibold px-4 py-2.5">Producto</th>
                <th className="text-right font-semibold px-4 py-2.5">Unidades</th>
                <th className="text-right font-semibold px-4 py-2.5">Venta{isGlobal ? " (USD)" : ""}</th>
              </tr></thead>
              <tbody>
                {ranking.map((it: any, i: number) => (
                  <tr key={i} className="border-b border-ink-700/30 last:border-0">
                    <td className="px-4 py-2.5 text-gray-500">{i + 1}</td>
                    <td className="px-4 py-2.5 text-gray-200">{it.nombre}</td>
                    <td className="px-4 py-2.5 text-right text-gray-300">{nf(it.unidades)}</td>
                    <td className="px-4 py-2.5 text-right text-gray-100 font-semibold">{isGlobal ? usd(it.ventas_usd) : fmtMon(it.ventas, it.moneda)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-[11px] text-gray-500 mt-2">Top por venta (line items de Shopify, 7 días). Cruza con Publicaciones: si un top está “no activo” o sin ficha completa, es plata sobre la mesa.</p>
          </div>
        ) : <p className="text-sm text-gray-500">Sin ventas en los últimos 7 días para este alcance (o calculándose, ~cada 6h).</p>}
      </Section>
      <MercadoLibre scoped={scoped} isGlobal={isGlobal} />
      <Section title="Otros marketplaces (vía Multivende)">
        <Proximamente inline titulo="Falabella · Walmart · Ripley · París"
          detalle="Al conectar Multivende (correo enviado a api@multivende.com) verás venta, stock y precio de cada marketplace por país — y se cuadrará la venta total de Mercado Libre directo vs Multivende." />
      </Section>
    </>
  );
}

function MercadoLibre({ scoped, isGlobal }: any) {
  const con = scoped.filter((p: any) => p.meli);
  const ventaUsd = con.reduce((s: number, p: any) => s + (p.meli_ventas_usd || 0), 0);
  const pedidos = con.reduce((s: number, p: any) => s + (p.meli?.pedidos || 0), 0);
  const pubs = con.reduce((s: number, p: any) => s + (p.meli?.publicaciones || 0), 0);
  if (!con.length) {
    return (
      <Section title="Mercado Libre (directo)">
        <Proximamente inline titulo="Conectar Mercado Libre"
          detalle="Aún sin cuenta ML conectada. Abre /meli en el robot y conecta cada país (OAuth). Reemplaza a Nubimetrics: venta, pedidos y publicaciones activas por país, gratis." />
      </Section>
    );
  }
  return (
    <Section title="Mercado Libre (directo) 🟢">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
        <Kpi label="Venta ML (USD)" value={usd(ventaUsd)} />
        <Kpi label="Pedidos ML" value={nf(pedidos)} />
        <Kpi label="Publicaciones activas" value={nf(pubs)} />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[480px]">
          <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
            <th className="text-left font-semibold px-4 py-2.5">País</th>
            <th className="text-right font-semibold px-4 py-2.5">Venta</th>
            <th className="text-right font-semibold px-4 py-2.5">Pedidos</th>
            <th className="text-right font-semibold px-4 py-2.5">Publicaciones</th>
          </tr></thead>
          <tbody>
            {con.map((p: any) => (
              <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                <td className="px-4 py-2.5 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre}</td>
                <td className="px-4 py-2.5 text-right text-gray-100 font-semibold">{fmtMon(p.meli.ventas, p.meli.moneda)}</td>
                <td className="px-4 py-2.5 text-right text-gray-300">{nf(p.meli.pedidos)}</td>
                <td className="px-4 py-2.5 text-right text-gray-300">{p.meli.publicaciones != null ? nf(p.meli.publicaciones) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-[11px] text-gray-500 mt-2">Mercado Libre directo (API oficial). Se cuadrará con Multivende cuando esté conectado.</p>
      </div>
    </Section>
  );
}

/* ---------- ADQUISICIÓN (sub-nav por plataforma) ---------- */
function Adquisicion({ c, scoped, isGlobal }: any) {
  const [plat, setPlat] = useState("resumen");
  const subs = [
    { id: "resumen", label: "Resumen" },
    { id: "meta", label: "Meta Ads" },
    { id: "google", label: "Google Ads" },
    { id: "tiktok", label: "TikTok Ads" },
  ];
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
      <div className="mt-4 inline-flex rounded-xl bg-ink-850 border border-ink-700/60 p-1">
        {subs.map((s) => (
          <button key={s.id} onClick={() => setPlat(s.id)}
            className={`px-3 py-1.5 text-xs rounded-lg transition ${plat === s.id ? "bg-ink-700 text-white" : "text-gray-400 hover:text-gray-200"}`}>{s.label}</button>
        ))}
      </div>

      {plat === "resumen" && (
        <Section title="Ads por país (USD)">
          <div className="overflow-x-auto">
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
      )}
      {plat === "meta" && <PlataformaAds nombre="Meta Ads" scoped={scoped} campo="meta_spend_usd" campField="meta_campaigns" creaField="meta_creatives" conectado />}
      {plat === "google" && <PlataformaAds nombre="Google Ads" scoped={scoped} campo="gads_spend_usd" campField="gads_campaigns" conectado />}
      {plat === "tiktok" && <Proximamente titulo="TikTok Ads" detalle="Pendiente de conectar (como Meta). Luego verás campañas activas/pausadas, performance, creativos en uso y con desgaste, y acciones recomendadas." />}
    </>
  );
}

function PlataformaAds({ nombre, scoped, campo, campField, creaField, conectado }: any) {
  const data = scoped.filter((p: any) => p[campo]).map((p: any) => ({ label: `${p.bandera} ${p.nombre}`, value: p[campo] || 0 }));
  const camps: any[] = [];
  scoped.forEach((p: any) => (p[campField] || []).forEach((c: any) => camps.push({ ...c, pais: p.bandera, moneda: p.moneda })));
  camps.sort((a, b) => b.spend - a.spend);
  const creas: any[] = [];
  if (creaField) scoped.forEach((p: any) => (p[creaField] || []).forEach((c: any) => creas.push({ ...c, pais: p.bandera, moneda: p.moneda })));
  creas.sort((a, b) => b.spend - a.spend);
  const estadoDot = (e: string) => (/active|enabled/i.test(e || "") ? "bg-accent-up" : "bg-gray-500");
  return (
    <>
      <Section title={`${nombre} · gasto por país (USD) ${conectado ? "🟢" : ""}`}>
        {data.length ? <Bars data={data} fmt={usd} /> : <p className="text-sm text-gray-500">Sin gasto en el período.</p>}
      </Section>
      <Section title={`${nombre} · campañas (top por gasto · 7d)`}>
        {camps.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[560px]">
              <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
                <th className="text-left font-semibold px-3 py-2"></th>
                <th className="text-left font-semibold px-3 py-2">Campaña</th>
                <th className="text-left font-semibold px-3 py-2">Estado</th>
                <th className="text-right font-semibold px-3 py-2">Gasto</th>
                <th className="text-right font-semibold px-3 py-2">ROAS</th>
              </tr></thead>
              <tbody>
                {camps.slice(0, 15).map((c, i) => (
                  <tr key={i} className="border-b border-ink-700/30 last:border-0">
                    <td className="px-3 py-2">{c.pais}</td>
                    <td className="px-3 py-2 text-gray-200 max-w-[280px] truncate" title={c.nombre}>{c.nombre}</td>
                    <td className="px-3 py-2"><span className={`inline-block h-1.5 w-1.5 rounded-full mr-1 ${estadoDot(c.estado)}`} /><span className="text-[11px] text-gray-400">{c.estado}</span></td>
                    <td className="px-3 py-2 text-right text-gray-200">{fmtMon(c.spend, c.moneda)}</td>
                    <td className={`px-3 py-2 text-right font-semibold ${c.roas >= 3 ? "text-accent-up" : c.roas > 0 && c.roas < 1 ? "text-accent-down" : "text-gray-300"}`}>{c.roas ? c.roas + "x" : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-[11px] text-gray-500 mt-2">Montos en la moneda de cada cuenta. ROAS de plataforma (valor de conversión).</p>
          </div>
        ) : <p className="text-sm text-gray-500">Sin campañas con entrega en el período (o conexión pendiente).</p>}
      </Section>
      {creaField && (
        <Section title={`${nombre} · creativos y fatiga (7d)`}>
          {creas.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[600px]">
                <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
                  <th className="text-left font-semibold px-3 py-2"></th>
                  <th className="text-left font-semibold px-3 py-2">Creativo</th>
                  <th className="text-right font-semibold px-3 py-2">Gasto</th>
                  <th className="text-right font-semibold px-3 py-2">CTR</th>
                  <th className="text-right font-semibold px-3 py-2">Frec.</th>
                  <th className="text-right font-semibold px-3 py-2">Estado</th>
                </tr></thead>
                <tbody>
                  {creas.slice(0, 15).map((c, i) => (
                    <tr key={i} className="border-b border-ink-700/30 last:border-0">
                      <td className="px-3 py-2">{c.pais}</td>
                      <td className="px-3 py-2 text-gray-200 max-w-[260px] truncate" title={c.nombre}>{c.nombre}</td>
                      <td className="px-3 py-2 text-right text-gray-200">{fmtMon(c.spend, c.moneda)}</td>
                      <td className={`px-3 py-2 text-right ${c.ctr < 1 ? "text-accent-down" : "text-gray-300"}`}>{c.ctr}%</td>
                      <td className="px-3 py-2 text-right text-gray-400">{c.frecuencia}</td>
                      <td className="px-3 py-2 text-right">{c.fatiga ? <span className="text-[11px] rounded bg-accent-down/20 text-accent-down px-1.5 py-0.5">⚠ fatiga</span> : <span className="text-[11px] text-gray-500">ok</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-[11px] text-gray-500 mt-2">Fatiga = frecuencia alta (≥3) o (≥2 con CTR &lt;1%). Señal para refrescar el creativo.</p>
            </div>
          ) : <p className="text-sm text-gray-500">Sin creativos con gasto en el período.</p>}
        </Section>
      )}
    </>
  );
}

/* ---------- PUBLICACIONES (completitud de fichas) ---------- */
function Publicaciones({ catalogo, scope }: any) {
  const paises = ORDEN.filter((p) => catalogo[p]).filter((p) => scope === "Global" || p === scope)
    .map((p) => ({ ...catalogo[p], nombre: p, bandera: BANDERA[p] || "" }));
  const cell = (n: number, tot: number) => {
    const pctv = tot ? Math.round((n / tot) * 100) : 0;
    return <span className={n > 0 ? "text-accent-down" : "text-gray-400"}>{nf(n)}{tot ? ` (${pctv}%)` : ""}</span>;
  };
  return (
    <>
      <Section title="Sitio propio (Shopify) — completitud de fichas 🟢">
        {paises.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[560px]">
              <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
                <th className="text-left font-semibold px-4 py-3">País</th>
                <th className="text-right font-semibold px-4 py-3">Productos</th>
                <th className="text-right font-semibold px-4 py-3">Sin imagen</th>
                <th className="text-right font-semibold px-4 py-3">Sin descripción</th>
                <th className="text-right font-semibold px-4 py-3">No activos</th>
              </tr></thead>
              <tbody>
                {paises.map((p: any) => (
                  <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                    <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre}</td>
                    <td className="px-4 py-3 text-right text-gray-100 font-semibold">{nf(p.total)}</td>
                    <td className="px-4 py-3 text-right">{cell(p.sin_imagen, p.total)}</td>
                    <td className="px-4 py-3 text-right">{cell(p.sin_descripcion, p.total)}</td>
                    <td className="px-4 py-3 text-right">{cell(p.no_activos, p.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-[11px] text-gray-500 mt-2">Fichas con faltantes en Shopify (muestra hasta 2.000 productos por tienda). Oportunidad directa de mejora: completar imagen y descripción sube conversión.</p>
          </div>
        ) : <p className="text-sm text-gray-500">Aún sin datos de catálogo (se calcula 1×día).</p>}
      </Section>
      <Section title="Marketplaces (vía Multivende)">
        <Proximamente inline titulo="Faltantes y errores por marketplace"
          detalle="Al conectar Multivende: publicaciones con info incompleta o con errores en Mercado Libre, Falabella, Walmart, Ripley y París (atributos, fotos, ficha técnica, GTIN) — además del diagnóstico de catálogo de Meta." />
      </Section>
    </>
  );
}

/* ---------- TENDENCIAS (Google Trends) ---------- */
function Tendencias({ tendencias, scope }: any) {
  const paises = ORDEN.filter((p) => tendencias[p]?.length).filter((p) => scope === "Global" || p === scope);
  return (
    <>
      {paises.length ? paises.map((p: string) => {
        const items = tendencias[p] || [];
        const rel = items.filter((x: any) => x.relevante);
        return (
          <Section key={p} title={`${BANDERA[p] || ""} ${p} — búsquedas en alza (24h) 🟢`}>
            {rel.length > 0 && (
              <div className="mb-3 rounded-lg border border-accent-up/30 bg-accent-up/5 px-3 py-2">
                <p className="text-[11px] uppercase tracking-wider text-accent-up font-semibold mb-1">Afín a SLEVE — oportunidad de contenido/oferta</p>
                <div className="flex flex-wrap gap-2">
                  {rel.map((x: any, i: number) => (
                    <span key={i} className="text-xs bg-accent-up/15 text-accent-up rounded-full px-2.5 py-1 font-medium">{x.termino}{x.trafico ? ` · ${x.trafico}` : ""}</span>
                  ))}
                </div>
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              {items.map((x: any, i: number) => (
                <span key={i} className={`text-xs rounded-full px-2.5 py-1 ${x.relevante ? "bg-accent-up/15 text-accent-up font-medium" : "bg-ink-700/40 text-gray-300"}`}>
                  <span className="text-gray-500 mr-1">{i + 1}.</span>{x.termino}{x.trafico ? <span className="text-gray-500"> · {x.trafico}</span> : null}
                </span>
              ))}
            </div>
          </Section>
        );
      }) : (
        <Section title="Tendencias por país (Google Trends)">
          <p className="text-sm text-gray-500">Cargando búsquedas en alza… (se actualiza ~cada 3h desde el feed de Google Trends).</p>
        </Section>
      )}
      <p className="text-[11px] text-gray-500 px-1">Fuente: Google Trends (búsquedas en alza últimas 24h por país, feed oficial — gratis, sin scraping pesado). Resaltado = términos afines a electrónica/audio. Próximamente: interés en el tiempo de keywords propias (audífonos, parlantes, marcas).</p>
    </>
  );
}

/* ---------- REDES SOCIALES ---------- */
function YouTubeBlock({ yt, scope }: any) {
  const paises = ORDEN.filter((p) => yt?.[p]?.suscriptores != null).filter((p) => scope === "Global" || p === scope);
  if (!paises.length) return null;
  const subs = paises.reduce((s, p) => s + (yt[p].suscriptores || 0), 0);
  const vistas = paises.reduce((s, p) => s + (yt[p].vistas || 0), 0);
  return (
    <Section title="YouTube (orgánico) 🟢">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
        <Kpi label="Suscriptores" value={nf(subs)} sub={scope === "Global" ? "4 canales" : ""} />
        <Kpi label="Vistas totales" value={nf(vistas)} />
        <Kpi label="Canales" value={nf(paises.length)} />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[520px]">
          <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
            <th className="text-left font-semibold px-4 py-2.5">País · canal</th>
            <th className="text-right font-semibold px-4 py-2.5">Suscriptores</th>
            <th className="text-right font-semibold px-4 py-2.5">Vistas</th>
            <th className="text-right font-semibold px-4 py-2.5">Videos</th>
          </tr></thead>
          <tbody>
            {paises.map((p) => (
              <tr key={p} className="border-b border-ink-700/30 last:border-0">
                <td className="px-4 py-2.5 text-gray-200 whitespace-nowrap">{BANDERA[p]} @{yt[p].handle}</td>
                <td className="px-4 py-2.5 text-right text-gray-100 font-semibold">{nf(yt[p].suscriptores)}</td>
                <td className="px-4 py-2.5 text-right text-gray-300">{nf(yt[p].vistas)}</td>
                <td className="px-4 py-2.5 text-right text-gray-300">{nf(yt[p].videos)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-[11px] text-gray-500 mt-2">Datos públicos (YouTube Data API). Próximamente: retención, tiempo de reproducción y tráfico (YouTube Analytics).</p>
      </div>
    </Section>
  );
}
function Redes({ scoped, youtube, scope }: any) {
  const con = scoped.filter((p: any) => p.social);
  const hayYt = ORDEN.some((p) => youtube?.[p]?.suscriptores != null && (scope === "Global" || p === scope));
  if (!con.length) return (<>
    <YouTubeBlock yt={youtube} scope={scope} />
    {!hayYt && <Proximamente titulo="Redes sociales" detalle="Sin datos de redes para esta selección (o falta cargar META_BUSINESS_ID / YOUTUBE_API_KEY)." />}
  </>);
  const fb = con.reduce((s: number, p: any) => s + (p.social.fb_followers || 0), 0);
  const ig = con.reduce((s: number, p: any) => s + (p.social.ig_followers || 0), 0);
  const posts = con.reduce((s: number, p: any) => s + (p.social.ig_posts || 0), 0);
  return (
    <>
      <section className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label="Seguidores Facebook" value={nf(fb)} />
        <Kpi label="Seguidores Instagram" value={nf(ig)} />
        <Kpi label="Audiencia total" value={nf(fb + ig)} sub="FB + IG" />
        <Kpi label="Posts IG" value={nf(posts)} />
      </section>
      <Section title="Redes por país 🟢">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[560px]">
            <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
              <th className="text-left font-semibold px-4 py-3">País</th>
              <th className="text-right font-semibold px-4 py-3">Facebook</th>
              <th className="text-left font-semibold px-4 py-3">Instagram</th>
              <th className="text-right font-semibold px-4 py-3">Seguidores IG</th>
              <th className="text-right font-semibold px-4 py-3">Posts IG</th>
            </tr></thead>
            <tbody>
              {con.map((p: any) => (
                <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                  <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{nf(p.social.fb_followers)}</td>
                  <td className="px-4 py-3 text-gray-400">@{p.social.ig_username}</td>
                  <td className="px-4 py-3 text-right text-gray-100 font-semibold">{nf(p.social.ig_followers)}</td>
                  <td className="px-4 py-3 text-right text-gray-400">{nf(p.social.ig_posts)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-gray-500 mt-2">Seguidores y publicaciones (Meta orgánico). Próximamente: alcance, engagement y rendimiento de cada post (requiere insights por página/IG).</p>
      </Section>
      <YouTubeBlock yt={youtube} scope={scope} />
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

/* ---------- YoY (crecimiento año vs año) ---------- */
function YoYView({ yoy }: any) {
  if (!yoy || !yoy.consolidado) return <p className="mt-6 text-gray-500">El comparativo año vs año se calcula una vez al día — aún no disponible. Vuelve en un rato (o fuerza un refresh del robot).</p>;
  const c = yoy.consolidado;
  const paises = ORDEN.filter((p) => yoy.paises?.[p]).map((p) => ({ ...yoy.paises[p], nombre: p, bandera: BANDERA[p] || "" }));
  const tone = (g: number | null) => (g == null ? undefined : g >= 0 ? "up" : "down");
  return (
    <>
      <section className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label="Venta 30d (USD)" value={usd(c.rev_now_usd)} sub={`año ant. ${usd(c.rev_prev_usd)}`} />
        <Kpi label="Crecimiento venta" value={pct(c.rev_growth)} tone={tone(c.rev_growth)} sub="vs mismos 30d año ant." />
        <Kpi label="Sesiones 30d" value={nf(c.ses_now)} sub={`año ant. ${nf(c.ses_prev)}`} />
        <Kpi label="Crecimiento tráfico" value={pct(c.ses_growth)} tone={tone(c.ses_growth)} />
      </section>
      <Section title={`Crecimiento por país · ${yoy.rango_actual} vs ${yoy.rango_prev}`}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
              <th className="text-left font-semibold px-4 py-3">País</th>
              <th className="text-right font-semibold px-4 py-3">Venta 30d</th>
              <th className="text-right font-semibold px-4 py-3">Año ant.</th>
              <th className="text-right font-semibold px-4 py-3">Δ Venta</th>
              <th className="text-right font-semibold px-4 py-3">Sesiones</th>
              <th className="text-right font-semibold px-4 py-3">Δ Tráfico</th>
            </tr></thead>
            <tbody>
              {paises.map((p: any) => (
                <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                  <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre}</td>
                  <td className="px-4 py-3 text-right text-gray-100 font-semibold">{usd(p.rev_now_usd)}</td>
                  <td className="px-4 py-3 text-right text-gray-400">{usd(p.rev_prev_usd)}</td>
                  <td className={`px-4 py-3 text-right font-semibold ${p.rev_growth == null ? "text-gray-500" : p.rev_growth >= 0 ? "text-accent-up" : "text-accent-down"}`}>{pct(p.rev_growth)}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{nf(p.ses_now)}</td>
                  <td className={`px-4 py-3 text-right font-semibold ${p.ses_growth == null ? "text-gray-500" : p.ses_growth >= 0 ? "text-accent-up" : "text-accent-down"}`}>{pct(p.ses_growth)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-gray-500 mt-2">Venta (Shopify → USD) y sesiones (GA4) de los últimos 30 días vs el mismo período del año anterior. Próximamente: gasto/MER YoY y por marketplace.</p>
      </Section>
    </>
  );
}

/* ---------- PERÍODO AGREGADO (30 días / este mes) ---------- */
function P30View({ p30, scope, label = "últimos 30 días" }: any) {
  if (!p30 || !p30.consolidado) return <p className="mt-6 text-gray-500">El consolidado de {label} se calcula una vez al día — aún no disponible. Vuelve en un rato (o fuerza un refresh del robot).</p>;
  const isGlobal = scope === "Global";
  const paises = ORDEN.filter((p) => p30.paises?.[p]).map((p) => ({ ...p30.paises[p], nombre: p, bandera: BANDERA[p] || "" }));
  const c = p30.consolidado;
  const sel = isGlobal ? null : paises.find((x) => x.nombre === scope);
  const conv = (n: number) => `${(n || 0).toFixed(2)}%`;
  const L = label === "este mes" ? "del mes" : "30d";
  return (
    <>
      <section className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        {isGlobal ? <>
          <Kpi label={`Venta ${L} (USD)`} value={usd(c.ventas_usd)} sub="consolidado 4 países" />
          <Kpi label={`Pedidos ${L}`} value={nf(c.pedidos)} />
          <Kpi label={`Sesiones ${L}`} value={nf(c.sesiones)} />
          <Kpi label={`AOV ${L} (USD)`} value={usd(c.aov_usd)} />
        </> : sel ? <>
          <Kpi label={`Venta ${L} (${sel.moneda})`} value={fmtMon(sel.ventas, sel.moneda)} sub={`${usd(sel.ventas_usd)} USD`} />
          <Kpi label={`Pedidos ${L}`} value={nf(sel.pedidos)} />
          <Kpi label={`Conversión ${L}`} value={conv(sel.conversion)} sub={`${nf(sel.sesiones)} sesiones`} />
          <Kpi label={`AOV ${L} (${sel.moneda})`} value={fmtMon(sel.aov, sel.moneda)} />
        </> : null}
      </section>
      {isGlobal && (
        <Section title={`Venta por país · ${label} (USD)`}>
          <Bars data={paises.map((p: any) => ({ label: `${p.bandera} ${p.nombre}`, value: p.ventas_usd }))} fmt={usd} />
        </Section>
      )}
      <Section title={`Detalle por país · ${p30.rango || label}`}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[680px]">
            <thead><tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
              <th className="text-left font-semibold px-4 py-3">País</th>
              <th className="text-right font-semibold px-4 py-3">Venta (USD)</th>
              <th className="text-right font-semibold px-4 py-3">Pedidos</th>
              <th className="text-right font-semibold px-4 py-3">Sesiones</th>
              <th className="text-right font-semibold px-4 py-3">Conversión</th>
              <th className="text-right font-semibold px-4 py-3">AOV (USD)</th>
            </tr></thead>
            <tbody>
              {(isGlobal ? paises : (sel ? [sel] : [])).map((p: any) => (
                <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                  <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre}</td>
                  <td className="px-4 py-3 text-right text-gray-100 font-semibold">{usd(p.ventas_usd)}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{nf(p.pedidos)}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{nf(p.sesiones)}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{conv(p.conversion)}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{usd(p.aov_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-gray-500 mt-2">Venta y pedidos: Shopify (total del pedido, incluye envío e impuestos → equivale a “Ventas totales” de Shopify). Sesiones y conversión: GA4. Se recalcula 1×día. Ads/MER a 30d: próximamente.</p>
      </Section>
    </>
  );
}

/* ---------- VENTA POR FUENTE/CANAL (share GA4 × venta real Shopify) ---------- */
const CANAL_RULES: [RegExp, string][] = [
  [/instagram|ig\s|ig\//i, "Instagram"],
  [/facebook|fb|meta/i, "Facebook"],
  [/google|adwords/i, "Google"],
  [/tiktok/i, "TikTok"],
  [/bing/i, "Bing"],
  [/klaviyo|email|e-?mail|newsletter/i, "Email"],
  [/youtube/i, "YouTube"],
  [/\(direct\)|^direct|\/\s*\(none\)|sleve/i, "Directo"],
  [/not set|not provided|\(other\)/i, "Otros"],
];
function canalDe(fuente: string) {
  const f = (fuente || "").toLowerCase();
  for (const [re, name] of CANAL_RULES) if (re.test(f)) return name;
  const src = f.split("/")[0].trim();
  return src && src !== "?" ? src.charAt(0).toUpperCase() + src.slice(1) : "Otros";
}
function FuentesVenta({ paises, titulo = "Venta estimada por canal (7d)" }: any) {
  const acc: Record<string, number> = {};
  for (const p of paises || []) {
    const tr = p.traffic || [];
    const totT = tr.reduce((s: number, t: any) => s + (t.transacciones || 0), 0);
    const totS = tr.reduce((s: number, t: any) => s + (t.sesiones || 0), 0);
    const denom = totT > 0 ? totT : totS;
    if (!denom || !p.ventas_usd) continue;
    for (const t of tr) {
      const w = (totT > 0 ? (t.transacciones || 0) : (t.sesiones || 0)) / denom;
      const canal = canalDe(t.fuente);
      acc[canal] = (acc[canal] || 0) + w * p.ventas_usd;
    }
  }
  const data = Object.entries(acc).map(([label, value]) => ({ label, value: Math.round(value) }))
    .filter((d) => d.value > 0).sort((a, b) => b.value - a.value).slice(0, 8);
  if (!data.length) return null;
  return (
    <Section title={titulo}>
      <Bars data={data} fmt={usd} />
      <p className="text-[11px] text-gray-500 mt-2">Venta real de Shopify repartida por el peso de cada canal en GA4 (transacciones; sesiones si no hay). La suma cuadra con la venta total. Atribución last-click de GA4 — referencial para decidir dónde invertir.</p>
    </Section>
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

function buildAcciones(paises: any[], catalogo: any = {}) {
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
  for (const [pais, cat] of Object.entries<any>(catalogo)) {
    if ((cat?.sin_descripcion || 0) > 0) A.push({ level: "warn", text: `${pais}: ${cat.sin_descripcion} fichas sin descripción en Shopify — completarlas sube conversión y SEO.` });
    if ((cat?.sin_imagen || 0) > 0) A.push({ level: "down", text: `${pais}: ${cat.sin_imagen} productos sin imagen — prioridad alta, casi no venden sin foto.` });
    if (cat?.total && (cat.no_activos / cat.total) > 0.5) A.push({ level: "info", text: `${pais}: ${cat.no_activos}/${cat.total} productos no activos (${Math.round((cat.no_activos / cat.total) * 100)}%) — revisar si conviene reactivar catálogo.` });
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
function Trend({ data }: { data: any[] }) {
  if (!data || data.length < 2) {
    return <p className="text-sm text-gray-500">La tendencia se irá llenando con los días (el robot guarda 1 punto por día). {data?.length === 1 ? "Hoy: " + usd(data[0].ventas_usd) + "." : ""}</p>;
  }
  const max = Math.max(1, ...data.map((d) => d.ventas_usd || 0));
  return (
    <div className="flex items-end gap-1 h-32">
      {data.map((d) => (
        <div key={d.fecha} className="flex-1 flex flex-col items-center justify-end group" title={`${d.fecha}: ${usd(d.ventas_usd)} · MER ${d.mer_usd}x`}>
          <div className="w-full rounded-t bg-accent-up/70 group-hover:bg-accent-up transition" style={{ height: `${Math.max(2, (d.ventas_usd / max) * 100)}%` }} />
          <span className="text-[8px] text-gray-600 mt-1">{String(d.fecha).slice(5)}</span>
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
  const ok = ["Shopify", "Meta", "Klaviyo", "GA4", "Search Console", "Google Ads", "Redes (FB/IG)", "Google Trends", "Telegram"];
  const pend = ["Multivende", "Merchant Center", "YouTube", "Business Profile", "TikTok Ads", "Gorgias"];
  return (
    <div className="mt-4 rounded-xl bg-ink-900/50 border border-ink-800 px-3 py-2.5">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[9px] uppercase tracking-widest text-gray-500 font-semibold">Conexiones</span>
        <span className="text-[9px] text-gray-600">{ok.length} activas · {pend.length} pendientes</span>
      </div>
      <div className="flex flex-wrap gap-1.5 text-[10px]">
        {ok.map((s) => (
          <span key={s} className="inline-flex items-center gap-1.5 rounded-md bg-ink-850 border border-ink-700/60 text-gray-300 px-2 py-1">
            <span className="h-1.5 w-1.5 rounded-full bg-accent-up" />{s}
          </span>
        ))}
        {pend.map((s) => (
          <span key={s} className="rounded-md bg-ink-900 border border-ink-800 text-gray-600 px-2 py-1">{s}</span>
        ))}
      </div>
    </div>
  );
}
