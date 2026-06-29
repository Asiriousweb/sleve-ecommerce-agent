"use client";

import { useEffect, useState } from "react";

const card = "rounded-2xl bg-ink-850 border border-ink-700/60";

// --- helpers ---
const MONEDA: Record<string, string> = { Chile: "CLP", Colombia: "COP", "México": "MXN", "Perú": "PEN", EEUU: "USD" };
const BANDERA: Record<string, string> = { Chile: "🇨🇱", Colombia: "🇨🇴", "México": "🇲🇽", "Perú": "🇵🇪", EEUU: "🇺🇸" };
const ORDEN = ["Chile", "Colombia", "México", "Perú", "EEUU"];
const nf = (n: number) => new Intl.NumberFormat("es-CL").format(Math.round(n || 0));
const fmtMon = (n: number, ccy: string) =>
  new Intl.NumberFormat("es", { style: "currency", currency: ccy || "USD", maximumFractionDigits: 0 }).format(Math.round(n || 0));
const usd = (n: number) => fmtMon(n, "USD");

const TABS = [
  { id: "global", label: "Global" },
  { id: "pais", label: "Por país" },
  { id: "ads", label: "Adquisición" },
  { id: "pnl", label: "P&L" },
  { id: "acciones", label: "Acciones" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function Dashboard() {
  const [tab, setTab] = useState<TabId>("global");
  const [paisSel, setPaisSel] = useState("Chile");

  const API = process.env.NEXT_PUBLIC_API_URL
    || "https://sleve-ecommerce-agents-production.up.railway.app/api/overview";
  const [live, setLive] = useState<any>(null);
  useEffect(() => {
    fetch(API).then((r) => (r.ok ? r.json() : null))
      .then((d) => d?.fuente?.includes("vivo") && setLive(d)).catch(() => {});
  }, [API]);

  const c = live?.consolidado || {};
  const paises: any[] = live?.paises
    ? ORDEN.filter((p) => live.paises[p]).map((p) => ({ ...live.paises[p], nombre: p, moneda: MONEDA[p] || "USD", bandera: BANDERA[p] || "" }))
    : [];
  const conData = paises.filter((p) => (p.ventas_usd || 0) > 0 || (p.ad_spend_usd || 0) > 0);
  const cuadraTot = paises.filter((p) => p.cuadratura).length;
  const cuadraOk = paises.filter((p) => p.cuadratura?.ok).length;
  const acciones = buildAcciones(paises);

  if (!live) {
    return (
      <main className="min-h-screen bg-ink-950 grid place-items-center text-gray-400">
        <div className="text-center">
          <div className="text-2xl font-black text-white mb-2">SLEVE · E-commerce</div>
          <p className="text-sm">Conectando con el robot…</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-ink-950 px-5 py-5 md:px-8 md:py-6 max-w-[1500px] mx-auto">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-accent-brand to-accent-up grid place-items-center text-ink-950 font-black text-sm">S</div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-black tracking-tight">SLEVE</span>
              <span className="text-gray-500">·</span>
              <h1 className="font-bold">E-commerce Cockpit</h1>
            </div>
            <p className="text-[11px] text-accent-up">
              🟢 En vivo · {new Date(live.actualizado).toLocaleString("es-CL")} · {live.rango} · cuadratura {cuadraOk}/{cuadraTot}
            </p>
          </div>
        </div>
        <ConexionesStrip />
      </header>

      {/* Tabs */}
      <nav className="mt-5 flex gap-5 border-b border-ink-700/60 overflow-x-auto">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`pb-3 text-sm whitespace-nowrap transition border-b-2 -mb-px ${tab === t.id ? "text-white border-white" : "text-gray-500 border-transparent hover:text-gray-300"}`}>
            {t.label}{t.id === "acciones" && acciones.length ? ` (${acciones.length})` : ""}
          </button>
        ))}
      </nav>

      {tab === "global" && <Global c={c} paises={paises} conData={conData} cuadraOk={cuadraOk} cuadraTot={cuadraTot} live={live} acciones={acciones} setTab={setTab} />}
      {tab === "pais" && <PorPais paises={paises} paisSel={paisSel} setPaisSel={setPaisSel} />}
      {tab === "ads" && <Adquisicion c={c} conData={conData} />}
      {tab === "pnl" && <PnL c={c} conData={conData} />}
      {tab === "acciones" && <Acciones acciones={acciones} />}

      <footer className="mt-8 mb-4 text-[11px] text-gray-600">
        {live.nota} · consolidado en USD (FX del día) · SLEVE E-commerce · v0.3
      </footer>
    </main>
  );
}

/* ---------- Tabs ---------- */

function Global({ c, paises, conData, cuadraOk, cuadraTot, live, acciones, setTab }: any) {
  const kpis = [
    { label: "Venta total (USD)", value: usd(c.ventas_usd), sub: `${nf(c.pedidos)} pedidos · 7d` },
    { label: "Gasto Ads (USD)", value: usd(c.ad_spend_usd), sub: "Meta + Google" },
    { label: "MER blended", value: (c.mer_usd ?? 0) + "x", sub: "venta / ad spend", tone: c.mer_usd >= 3 ? "up" : "down" },
    { label: "Contribución (USD)", value: usd(c.contrib_usd), sub: "venta − ads (falta COGS)" },
    { label: "AOV (USD)", value: usd(c.aov_usd), sub: "ticket promedio" },
    { label: "CPA (USD)", value: usd(c.cpa_usd), sub: "costo por pedido" },
    { label: "Conversión", value: (c.conversion ?? 0) + "%", sub: `${nf(c.sesiones)} sesiones`, tone: c.conversion >= 1 ? "up" : "down" },
    { label: "MER (solo Meta)", value: (c.mer_meta_usd ?? 0) + "x", sub: "venta / Meta spend" },
  ];
  return (
    <>
      <section className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        {kpis.map((k) => <Kpi key={k.label} {...k} />)}
      </section>

      <Section title="Venta por país (USD · 7d)">
        <Bars data={conData.map((p: any) => ({ label: `${p.bandera} ${p.nombre}`, value: p.ventas_usd || 0 }))} fmt={usd} />
      </Section>

      <PaisesTabla paises={paises} cuadraOk={cuadraOk} cuadraTot={cuadraTot} rango={live.rango} />

      {acciones.length > 0 && (
        <Section title={`Acciones rápidas · top ${Math.min(3, acciones.length)}`}>
          <ul className="space-y-2">
            {acciones.slice(0, 3).map((a: any, i: number) => <AccionRow key={i} a={a} />)}
          </ul>
          <button onClick={() => setTab("acciones")} className="mt-3 text-[11px] text-accent-up hover:underline">Ver todas ({acciones.length}) →</button>
        </Section>
      )}
    </>
  );
}

function PaisesTabla({ paises, cuadraOk, cuadraTot, rango }: any) {
  return (
    <section className="mt-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Consolidado por país · {rango}</h2>
        <span className={`text-[11px] font-semibold ${cuadraOk === cuadraTot ? "text-accent-up" : "text-accent-down"}`}>Cuadratura {cuadraOk}/{cuadraTot} {cuadraOk === cuadraTot ? "✓" : "✗"}</span>
      </div>
      <div className={`${card} overflow-x-auto`}>
        <table className="w-full text-sm min-w-[920px]">
          <thead>
            <tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
              <th className="text-left font-semibold px-4 py-3">País</th>
              <th className="text-right font-semibold px-4 py-3">Venta (local)</th>
              <th className="text-right font-semibold px-4 py-3">Venta USD</th>
              <th className="text-right font-semibold px-4 py-3">Pedidos</th>
              <th className="text-right font-semibold px-4 py-3">AOV</th>
              <th className="text-right font-semibold px-4 py-3">Conv.</th>
              <th className="text-right font-semibold px-4 py-3">Ads USD</th>
              <th className="text-right font-semibold px-4 py-3">MER</th>
              <th className="text-right font-semibold px-4 py-3">Email</th>
              <th className="text-right font-semibold px-4 py-3">Cuadr.</th>
            </tr>
          </thead>
          <tbody>
            {paises.map((p: any) => (
              <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre} <span className="text-gray-600 text-[10px]">{p.moneda}</span></td>
                <td className="px-4 py-3 text-right text-gray-300">{p.ventas_clp ? fmtMon(p.ventas_clp, p.moneda) : "—"}</td>
                <td className="px-4 py-3 text-right text-gray-100 font-semibold">{p.ventas_usd ? usd(p.ventas_usd) : "—"}</td>
                <td className="px-4 py-3 text-right text-gray-300">{nf(p.pedidos ?? 0)}</td>
                <td className="px-4 py-3 text-right text-gray-400">{p.aov ? fmtMon(p.aov, p.moneda) : "—"}</td>
                <td className={`px-4 py-3 text-right font-semibold ${p.conversion >= 1.5 ? "text-accent-up" : p.conversion < 0.7 ? "text-accent-down" : "text-gray-300"}`}>{(p.conversion ?? 0).toFixed(2)}%</td>
                <td className="px-4 py-3 text-right text-gray-400">{p.ad_spend_usd ? usd(p.ad_spend_usd) : "—"}</td>
                <td className={`px-4 py-3 text-right font-semibold ${p.mer_usd >= 3 ? "text-accent-up" : p.mer_usd > 0 && p.mer_usd < 2 ? "text-accent-down" : "text-gray-300"}`}>{p.mer_usd ? p.mer_usd + "x" : "—"}</td>
                <td className="px-4 py-3 text-right text-gray-400">{p.klaviyo?.email_revenue ? fmtMon(p.klaviyo.email_revenue, p.moneda) : "—"}</td>
                <td className="px-4 py-3 text-right whitespace-nowrap">
                  {p.cuadratura?.ok ? <span className="text-accent-up text-xs">✓</span> : p.cuadratura ? <span className="text-accent-down text-xs">✗</span> : <span className="text-gray-600 text-xs">—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-gray-500 mt-2">Cada país en su moneda local; el consolidado se normaliza a USD (FX del día). MER = venta / (Meta + Google). Cuadratura = transacciones GA4 ≤ pedidos Shopify.</p>
    </section>
  );
}

function PorPais({ paises, paisSel, setPaisSel }: any) {
  const p = paises.find((x: any) => x.nombre === paisSel) || paises[0];
  if (!p) return <p className="mt-6 text-gray-500">Sin datos.</p>;
  const stats = [
    { label: "Venta (local)", value: p.ventas_clp ? fmtMon(p.ventas_clp, p.moneda) : "—" },
    { label: "Venta (USD)", value: p.ventas_usd ? usd(p.ventas_usd) : "—" },
    { label: "Pedidos", value: nf(p.pedidos ?? 0) },
    { label: "AOV", value: p.aov ? fmtMon(p.aov, p.moneda) : "—" },
    { label: "Sesiones", value: nf(p.sesiones ?? 0) },
    { label: "Conversión", value: (p.conversion ?? 0) + "%", tone: p.conversion >= 1 ? "up" : "down" },
    { label: "Gasto Meta", value: p.meta_spend != null ? fmtMon(p.meta_spend, p.meta_moneda || p.moneda) : "—" },
    { label: "Gasto Google", value: p.ad_spend ? fmtMon(p.ad_spend, p.gads_moneda || p.moneda) : "—" },
    { label: "Ads (USD)", value: p.ad_spend_usd ? usd(p.ad_spend_usd) : "—" },
    { label: "MER", value: p.mer_usd ? p.mer_usd + "x" : "—", tone: p.mer_usd >= 3 ? "up" : "down" },
    { label: "Contribución (USD)", value: p.contrib_usd != null ? usd(p.contrib_usd) : "—" },
    { label: "Email (Klaviyo)", value: p.klaviyo?.email_revenue ? fmtMon(p.klaviyo.email_revenue, p.moneda) : "—" },
  ];
  return (
    <>
      <div className="mt-5 flex items-center gap-3">
        <span className="text-xs text-gray-500 uppercase tracking-widest">País</span>
        <select value={paisSel} onChange={(e) => setPaisSel(e.target.value)}
          className="rounded-xl bg-ink-850 border border-ink-700/60 px-3 py-2 text-sm text-gray-200">
          {paises.map((x: any) => <option key={x.nombre} value={x.nombre}>{x.bandera} {x.nombre}</option>)}
        </select>
      </div>
      <section className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        {stats.map((s) => <Kpi key={s.label} {...s} />)}
      </section>

      {p.search_console && (
        <Section title="Descubribilidad · Search Console (orgánico)">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Kpi label="Clics" value={nf(p.search_console.clicks)} />
            <Kpi label="Impresiones" value={nf(p.search_console.impressions)} />
            <Kpi label="CTR" value={p.search_console.ctr + "%"} />
            <Kpi label="Posición media" value={String(p.search_console.position)} />
          </div>
        </Section>
      )}

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

function Adquisicion({ c, conData }: any) {
  return (
    <>
      <section className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label="Gasto Ads (USD)" value={usd(c.ad_spend_usd)} sub="Meta + Google" />
        <Kpi label="Gasto Meta (USD)" value={usd(c.meta_spend_usd)} />
        <Kpi label="MER blended" value={(c.mer_usd ?? 0) + "x"} tone={c.mer_usd >= 3 ? "up" : "down"} />
        <Kpi label="CPA (USD)" value={usd(c.cpa_usd)} sub="costo por pedido" />
      </section>
      <Section title="Ads por país (USD)">
        <div className={`${card} overflow-x-auto`}>
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
                <th className="text-left font-semibold px-4 py-3">País</th>
                <th className="text-right font-semibold px-4 py-3">Meta (USD)</th>
                <th className="text-right font-semibold px-4 py-3">Google (USD)</th>
                <th className="text-right font-semibold px-4 py-3">Total Ads (USD)</th>
                <th className="text-right font-semibold px-4 py-3">Venta (USD)</th>
                <th className="text-right font-semibold px-4 py-3">MER</th>
              </tr>
            </thead>
            <tbody>
              {conData.map((p: any) => (
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
        <p className="text-[11px] text-gray-500 mt-2">TikTok Ads pendiente de conectar. ROAS por plataforma (valor de conversión) puede diferir del MER (venta real Shopify).</p>
      </Section>
    </>
  );
}

function PnL({ c, conData }: any) {
  return (
    <>
      <section className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label="Venta total (USD)" value={usd(c.ventas_usd)} />
        <Kpi label="Gasto Ads (USD)" value={usd(c.ad_spend_usd)} />
        <Kpi label="Contribución (USD)" value={usd(c.contrib_usd)} tone={c.contrib_usd >= 0 ? "up" : "down"} sub="venta − ads" />
        <Kpi label="% sobre venta" value={c.ventas_usd ? Math.round((c.contrib_usd / c.ventas_usd) * 100) + "%" : "—"} />
      </section>
      <Section title="P&L por país (USD) · contribución después de ads">
        <div className={`${card} overflow-x-auto`}>
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
                <th className="text-left font-semibold px-4 py-3">País</th>
                <th className="text-right font-semibold px-4 py-3">Venta</th>
                <th className="text-right font-semibold px-4 py-3">− Ads</th>
                <th className="text-right font-semibold px-4 py-3">= Contribución</th>
                <th className="text-right font-semibold px-4 py-3">% venta</th>
              </tr>
            </thead>
            <tbody>
              {conData.map((p: any) => (
                <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                  <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">{p.bandera} {p.nombre}</td>
                  <td className="px-4 py-3 text-right text-gray-300">{usd(p.ventas_usd)}</td>
                  <td className="px-4 py-3 text-right text-accent-down">−{usd(p.ad_spend_usd)}</td>
                  <td className={`px-4 py-3 text-right font-semibold ${p.contrib_usd >= 0 ? "text-accent-up" : "text-accent-down"}`}>{usd(p.contrib_usd)}</td>
                  <td className="px-4 py-3 text-right text-gray-400">{p.ventas_usd ? Math.round((p.contrib_usd / p.ventas_usd) * 100) + "%" : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-gray-500 mt-2">
          ⚠️ <b>Contribución después de ads</b> = Venta − Gasto Ads. Para el <b>P&L real</b> falta restar <b>COGS / costo de producto</b> (no conectado aún) y comisiones de marketplace (vendrán con <b>Multivende</b>). Aún no incluye marketplaces (hoy solo sitio propio Shopify).
        </p>
      </Section>
    </>
  );
}

function Acciones({ acciones }: any) {
  if (!acciones.length) return <p className="mt-6 text-gray-500">Sin urgencias detectadas. 🟢</p>;
  return (
    <Section title={`Acciones rápidas y urgencias (${acciones.length})`}>
      <ul className="space-y-2">{acciones.map((a: any, i: number) => <AccionRow key={i} a={a} />)}</ul>
    </Section>
  );
}

/* ---------- generador de acciones (data-driven) ---------- */
function buildAcciones(paises: any[]) {
  const A: { level: "down" | "warn" | "info"; text: string }[] = [];
  for (const p of paises) {
    if (p.cuadratura && !p.cuadratura.ok) A.push({ level: "down", text: `Descuadre en ${p.nombre}: GA4 ${p.cuadratura.ga4_transacciones} > Shopify ${p.cuadratura.shopify_pedidos} pedidos — revisar tracking.` });
    if ((p.roas || 0) > 15) A.push({ level: "warn", text: `ROAS Google en ${p.nombre} = ${p.roas}x (sospechoso) — revisar config del valor de conversión (posible doble conteo).` });
    if ((p.sesiones || 0) > 300 && (p.conversion || 0) < 0.7 && (p.pedidos || 0) > 0) A.push({ level: "warn", text: `Conversión baja en ${p.nombre} (${(p.conversion ?? 0).toFixed(2)}%) con ${nf(p.sesiones)} sesiones — oportunidad CRO.` });
    if ((p.sesiones || 0) > 200 && (p.pedidos || 0) === 0) A.push({ level: "down", text: `${p.nombre}: ${nf(p.sesiones)} sesiones y 0 ventas — definir si activar o pausar inversión.` });
    if ((p.mer_usd || 0) > 0 && (p.mer_usd || 0) < 2) A.push({ level: "warn", text: `MER bajo en ${p.nombre} (${p.mer_usd}x) — ads no rentables, revisar campañas.` });
    const tk = (p.traffic || []).find((t: any) => /tiktok/i.test(t.fuente));
    if (tk && tk.conv < 0.5 && tk.sesiones > 500) A.push({ level: "warn", text: `TikTok en ${p.nombre} convierte ${tk.conv.toFixed(2)}% con ${nf(tk.sesiones)} sesiones — revisar inversión/targeting.` });
  }
  // pendientes de ecosistema (lo conversado)
  A.push({ level: "info", text: "Multivende: correo enviado a api@multivende.com → al llegar el Client ID/Secret, se conectan los marketplaces (hoy sin data)." });
  A.push({ level: "info", text: "Google Business Profile: esperando aprobación de acceso API (Chile listo; CO/MX/PE crear perfiles con bodegas)." });
  A.push({ level: "info", text: "TikTok Ads y Gorgias (customer service): pendientes de conectar." });
  A.push({ level: "info", text: "Cargar créditos en Anthropic → enciende el loop nocturno de auto-optimización (ya construido)." });
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
          <div className="flex-1 h-6 bg-ink-800 rounded-lg overflow-hidden">
            <div className="h-full rounded-lg bg-accent-up/80" style={{ width: `${(d.value / max) * 100}%` }} />
          </div>
          <span className="w-24 text-right text-xs text-gray-300">{fmt(d.value)}</span>
        </div>
      ))}
    </div>
  );
}

function AccionRow({ a }: { a: { level: string; text: string } }) {
  const dot = a.level === "down" ? "bg-accent-down" : a.level === "warn" ? "bg-amber-400" : "bg-sky-400";
  return (
    <li className="flex items-start gap-3">
      <span className={`h-2 w-2 rounded-full shrink-0 mt-1.5 ${dot}`} />
      <span className="text-sm text-gray-300">{a.text}</span>
    </li>
  );
}

function ConexionesStrip() {
  const ok = ["Shopify", "Meta", "Klaviyo", "GA4", "Search Console", "Google Ads"];
  const pend = ["Multivende", "Business Profile", "TikTok", "Gorgias"];
  return (
    <div className="flex flex-wrap gap-1.5 text-[10px]">
      {ok.map((s) => <span key={s} className="rounded-md bg-accent-up/15 text-accent-up px-2 py-1">🟢 {s}</span>)}
      {pend.map((s) => <span key={s} className="rounded-md bg-ink-800 text-gray-500 px-2 py-1">○ {s}</span>)}
    </div>
  );
}
