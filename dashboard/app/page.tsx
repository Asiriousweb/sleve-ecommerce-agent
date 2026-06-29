"use client";

import { useEffect, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import {
  META, WEEKS, KPIS, TREND, CHANNELS, ADS, TOP_PRODUCTS, TRAFFIC, ALERTS,
  fmtCLP, fmtCompact, type Kpi,
} from "@/lib/data";

const card = "rounded-2xl bg-ink-850 border border-ink-700/60";

export default function Dashboard() {
  const [tab, setTab] = useState<"tendencia" | "yoy">("tendencia");
  const [granularity, setGranularity] = useState<"semanal" | "mensual">("semanal");

  // Datos en vivo desde el robot (Railway), refrescados cada 2h. Cae al baseline si no responde.
  const API = process.env.NEXT_PUBLIC_API_URL
    || "https://sleve-ecommerce-agents-production.up.railway.app/api/overview";
  const [live, setLive] = useState<any>(null);
  useEffect(() => {
    fetch(API)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d?.fuente?.includes("vivo") && setLive(d))
      .catch(() => {});
  }, [API]);
  const cl = live?.paises?.Chile;
  const nf = (n: number) => new Intl.NumberFormat("es-CL").format(n);
  const kpis: Kpi[] = cl
    ? KPIS.map((k) => {
        if (k.id === "conv")
          return { ...k, value: cl.conversion + "%", sub: nf(cl.sesiones) + " sesiones · 7d en vivo", trend: undefined };
        if (k.id === "ventas" && cl.ventas_clp != null)
          return { ...k, value: fmtCompact(cl.ventas_clp), sub: "Chile · últimos 7 días · en vivo", trend: undefined };
        if (k.id === "pedidos" && cl.pedidos != null)
          return { ...k, value: nf(cl.pedidos), sub: "AOV " + fmtCLP(cl.aov) + " · 7d", trend: undefined };
        return k;
      })
    : KPIS;
  const traffic: any[] = cl?.traffic?.length ? cl.traffic : TRAFFIC;

  // --- Países en vivo (cada uno en SU moneda; nunca se suman) ---
  const MONEDA: Record<string, string> = { Chile: "CLP", Colombia: "COP", "México": "MXN", "Perú": "PEN", EEUU: "USD" };
  const BANDERA: Record<string, string> = { Chile: "🇨🇱", Colombia: "🇨🇴", "México": "🇲🇽", "Perú": "🇵🇪", EEUU: "🇺🇸" };
  const ORDEN = ["Chile", "Colombia", "México", "Perú", "EEUU"];
  const fmtMon = (n: number, ccy: string) =>
    new Intl.NumberFormat("es", { style: "currency", currency: ccy, maximumFractionDigits: 0 }).format(Math.round(n));
  const paisesLive: any[] = live?.paises
    ? ORDEN.filter((p) => live.paises[p]).map((p) => ({ ...live.paises[p], nombre: p, moneda: MONEDA[p] || "USD", bandera: BANDERA[p] || "" }))
    : [];
  const cuadraTot = paisesLive.filter((p) => p.cuadratura).length;
  const cuadraOk = paisesLive.filter((p) => p.cuadratura?.ok).length;

  return (
    <main className="min-h-screen bg-ink-950 px-5 py-5 md:px-8 md:py-6 max-w-[1500px] mx-auto">
      <Header />
      {live ? (
        <p className="text-[11px] text-accent-up mt-2">
          🟢 En vivo · actualizado {new Date(live.actualizado).toLocaleString("es-CL")} · {live.rango} · GA4 + Google · Shopify + Meta directos
        </p>
      ) : (
        <p className="text-[11px] text-gray-600 mt-2">○ Datos demo (baseline) · conectando con el robot…</p>
      )}
      <Tabs tab={tab} setTab={setTab} />
      <WeekSelector />

      {/* Alertas / urgencias */}
      <section className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-3">
        {ALERTS.map((a, i) => (
          <div key={i} className={`${card} px-4 py-3 flex items-center gap-3`}>
            <span
              className={`h-2.5 w-2.5 rounded-full shrink-0 ${
                a.level === "down" ? "bg-accent-down" : "bg-amber-400"
              }`}
            />
            <span className="text-sm text-gray-300">{a.text}</span>
          </div>
        ))}
      </section>

      {/* KPI cards */}
      <section className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((k) => (
          <KpiCard key={k.id} kpi={k} />
        ))}
      </section>

      {/* Países en vivo + cuadratura (siempre visible) */}
      {paisesLive.length > 0 && (
        <section className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-semibold tracking-widest text-gray-500 uppercase">
              Países · en vivo — Shopify + GA4 + Meta · {live.rango}
            </h2>
            <span className={`text-[11px] font-semibold ${cuadraOk === cuadraTot ? "text-accent-up" : "text-accent-down"}`}>
              Cuadratura {cuadraOk}/{cuadraTot} {cuadraOk === cuadraTot ? "✓" : "✗"}
            </span>
          </div>
          <div className={`${card} overflow-x-auto`}>
            <table className="w-full text-sm min-w-[900px]">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
                  <th className="text-left font-semibold px-4 py-3">País</th>
                  <th className="text-right font-semibold px-4 py-3">Ventas 7d</th>
                  <th className="text-right font-semibold px-4 py-3">Pedidos</th>
                  <th className="text-right font-semibold px-4 py-3">AOV</th>
                  <th className="text-right font-semibold px-4 py-3">Sesiones</th>
                  <th className="text-right font-semibold px-4 py-3">Conv.</th>
                  <th className="text-right font-semibold px-4 py-3">Meta gasto</th>
                  <th className="text-right font-semibold px-4 py-3">Email (Klaviyo)</th>
                  <th className="text-right font-semibold px-4 py-3">Cuadratura</th>
                </tr>
              </thead>
              <tbody>
                {paisesLive.map((p) => (
                  <tr key={p.nombre} className="border-b border-ink-700/30 last:border-0">
                    <td className="px-4 py-3 text-gray-200 font-medium whitespace-nowrap">
                      {p.bandera} {p.nombre} <span className="text-gray-600 text-[10px]">{p.moneda}</span>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-100 font-semibold">{p.ventas_clp ? fmtMon(p.ventas_clp, p.moneda) : "—"}</td>
                    <td className="px-4 py-3 text-right text-gray-300">{nf(p.pedidos ?? 0)}</td>
                    <td className="px-4 py-3 text-right text-gray-400">{p.aov ? fmtMon(p.aov, p.moneda) : "—"}</td>
                    <td className="px-4 py-3 text-right text-gray-300">{nf(p.sesiones ?? 0)}</td>
                    <td className={`px-4 py-3 text-right font-semibold ${p.conversion >= 1.5 ? "text-accent-up" : p.conversion < 0.7 ? "text-accent-down" : "text-gray-300"}`}>
                      {(p.conversion ?? 0).toFixed(2)}%
                    </td>
                    <td className="px-4 py-3 text-right text-gray-400">{p.meta_spend != null ? fmtMon(p.meta_spend, p.meta_moneda || p.moneda) : "—"}</td>
                    <td className="px-4 py-3 text-right text-gray-400 whitespace-nowrap">
                      {p.klaviyo?.email_revenue ? (
                        <>{fmtMon(p.klaviyo.email_revenue, p.moneda)}{p.klaviyo.share_pct != null && <span className="text-gray-600"> ({p.klaviyo.share_pct}%)</span>}</>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {p.cuadratura?.ok ? (
                        <span className="text-accent-up text-xs">✓ GA4 {p.cuadratura.ga4_transacciones} ≤ {p.cuadratura.shopify_pedidos}</span>
                      ) : p.cuadratura ? (
                        <span className="text-accent-down text-xs">✗ GA4 {p.cuadratura.ga4_transacciones} &gt; {p.cuadratura.shopify_pedidos}</span>
                      ) : (
                        <span className="text-gray-600 text-xs">— sin ventas</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {live.consolidado?.ventas_usd ? (
            <p className="text-[12px] text-gray-200 mt-3">
              🌎 <b>Venta total consolidada:</b> {fmtMon(live.consolidado.ventas_usd, "USD")} USD
              {live.consolidado.meta_spend_usd ? <> · Gasto Meta {fmtMon(live.consolidado.meta_spend_usd, "USD")} · MER (Meta) {live.consolidado.mer_meta_usd}x</> : null}
              <span className="text-gray-500"> · convertido a USD (FX del día)</span>
            </p>
          ) : null}
          <p className="text-[11px] text-gray-500 mt-2">
            Cada país en su <b>moneda local</b> (no se suman directo). El consolidado se normaliza a USD con el FX del día. Cuadratura = transacciones GA4 ≤ pedidos Shopify · Email = revenue atribuido a Klaviyo (% de la venta del país).
          </p>
        </section>
      )}

      {/* Descubribilidad · Search Console (orgánico) */}
      {paisesLive.some((p) => p.search_console) && (
        <section className="mt-6">
          <h2 className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">
            Descubribilidad · Search Console (búsqueda orgánica) · {live.rango}
          </h2>
          <div className={`${card} overflow-x-auto`}>
            <table className="w-full text-sm min-w-[560px]">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-ink-700/60">
                  <th className="text-left font-semibold px-4 py-3">País</th>
                  <th className="text-right font-semibold px-4 py-3">Clics</th>
                  <th className="text-right font-semibold px-4 py-3">Impresiones</th>
                  <th className="text-right font-semibold px-4 py-3">CTR</th>
                  <th className="text-right font-semibold px-4 py-3">Posición media</th>
                </tr>
              </thead>
              <tbody>
                {paisesLive.filter((p) => p.search_console).map((p) => (
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
          <p className="text-[11px] text-gray-500 mt-2">Búsqueda orgánica en Google (dominios sleve.X). México y Perú aún sin tráfico de búsqueda.</p>
        </section>
      )}

      {/* Tendencia */}
      <section className="mt-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold tracking-widest text-gray-500 uppercase">
            Tendencia · Total Chile (sitio + marketplaces)
          </h2>
          <Toggle
            value={granularity}
            onChange={setGranularity}
            options={[
              { id: "semanal", label: "Semanal" },
              { id: "mensual", label: "Mensual" },
            ]}
          />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ChartCard title="Venta Unidades">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={TREND} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="gU" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6ea8fe" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#6ea8fe" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#22262f" vertical={false} />
                <XAxis dataKey="week" stroke="#6b7280" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#6b7280" fontSize={11} tickLine={false} axisLine={false}
                  tickFormatter={(v) => new Intl.NumberFormat("es-CL").format(v)} />
                <Tooltip content={<DarkTooltip kind="int" />} />
                <Area type="monotone" dataKey="unidades" stroke="#6ea8fe" strokeWidth={2} fill="url(#gU)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Venta $ CLP">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={TREND} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="gV" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#34d399" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#22262f" vertical={false} />
                <XAxis dataKey="week" stroke="#6b7280" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#6b7280" fontSize={11} tickLine={false} axisLine={false}
                  tickFormatter={(v) => fmtCompact(v)} />
                <Tooltip content={<DarkTooltip kind="clp" />} />
                <Area type="monotone" dataKey="ventas" stroke="#34d399" strokeWidth={2} fill="url(#gV)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>

      {/* Canales + Ads */}
      <section className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Venta por canal · S25">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={CHANNELS} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid stroke="#22262f" vertical={false} />
              <XAxis dataKey="canal" stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} interval={0} />
              <YAxis stroke="#6b7280" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => fmtCompact(v)} />
              <Tooltip content={<DarkTooltip kind="clp" />} cursor={{ fill: "#ffffff08" }} />
              <Bar dataKey="ventas" radius={[6, 6, 0, 0]}>
                {CHANNELS.map((c, i) => (
                  <Cell key={i} fill={c.demo ? "#3b4252" : "#6ea8fe"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="text-[11px] text-gray-500 mt-2">
            ◾ Sitio propio (real) · ◼ marketplaces (demo, vía Multivende)
          </p>
        </ChartCard>

        <ChartCard title="Ads por plataforma · ROAS">
          <div className="space-y-3 py-1">
            {ADS.map((a) => (
              <div key={a.plataforma} className="flex items-center gap-3">
                <span className="w-16 text-sm text-gray-300">{a.plataforma}</span>
                <div className="flex-1 h-7 bg-ink-800 rounded-lg overflow-hidden">
                  <div
                    className="h-full rounded-lg flex items-center justify-end pr-2 text-[11px] font-semibold text-ink-950"
                    style={{
                      width: `${Math.min(a.roas / 5, 1) * 100}%`,
                      background: a.roas >= 3 ? "#34d399" : a.roas >= 2 ? "#fbbf24" : "#f87171",
                    }}
                  >
                    {a.roas.toFixed(1)}x
                  </div>
                </div>
                <span className="w-24 text-right text-xs text-gray-400">{fmtCompact(a.spend)} gasto</span>
              </div>
            ))}
            <p className="text-[11px] text-gray-500 pt-1">
              MER consolidado 3.4x · objetivo ROAS ≥ 3.0x. TikTok bajo umbral.
            </p>
          </div>
        </ChartCard>
      </section>

      {/* Top productos + Tráfico */}
      <section className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Top productos · 30 días (Shopify)">
          <ul className="divide-y divide-ink-700/50">
            {TOP_PRODUCTS.map((p, i) => (
              <li key={p.producto} className="flex items-center justify-between py-2.5">
                <span className="flex items-center gap-3 text-sm text-gray-200">
                  <span className="text-gray-500 w-4">{i + 1}</span>
                  {p.producto}
                </span>
                <span className="text-sm text-gray-300">
                  {fmtCLP(p.ventas)} <span className="text-gray-500">· {p.pedidos} ped.</span>
                </span>
              </li>
            ))}
          </ul>
        </ChartCard>

        <ChartCard title={cl ? "Fuentes de tráfico · 7 días (en vivo · GA4)" : "Fuentes de tráfico · 30 días (GA4)"}>
          <ul className="divide-y divide-ink-700/50">
            {traffic.map((t) => (
              <li key={t.fuente} className="flex items-center justify-between py-2.5">
                <span className="text-sm text-gray-200">{t.fuente}</span>
                <span className="flex items-center gap-4 text-sm">
                  <span className="text-gray-400">{new Intl.NumberFormat("es-CL").format(t.sesiones)} ses.</span>
                  <span className={`w-14 text-right font-semibold ${t.conv >= 1.5 ? "text-accent-up" : t.conv < 0.7 ? "text-accent-down" : "text-gray-300"}`}>
                    {t.conv.toFixed(2)}%
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </ChartCard>
      </section>

      <footer className="mt-8 mb-4 text-[11px] text-gray-600">
        Países (ventas/pedidos/conv/Meta) y tráfico: <b>en vivo</b> cada 2h. Tendencia, canales, ads y top productos: baseline hasta conectar Multivende. ·{" "}
        SLEVE E-commerce Global · v0.2
      </footer>
    </main>
  );
}

/* ---------- Subcomponentes ---------- */

function Header() {
  return (
    <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-accent-brand to-accent-up grid place-items-center text-ink-950 font-black text-sm">
          S
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-black tracking-tight">{META.brand}</span>
            <span className="text-gray-500">·</span>
            <h1 className="font-bold">{META.title}</h1>
          </div>
          <p className="text-xs text-gray-500">{META.subtitle}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Pill>🇨🇱 {META.country}</Pill>
        <span className="text-gray-600">/</span>
        <Pill>{META.view}</Pill>
      </div>
    </header>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <button className="flex items-center gap-2 rounded-xl bg-ink-850 border border-ink-700/60 px-3.5 py-2 text-sm text-gray-200 hover:bg-ink-800 transition">
      {children}
      <span className="text-gray-500 text-xs">▾</span>
    </button>
  );
}

function Tabs({ tab, setTab }: { tab: string; setTab: (t: any) => void }) {
  return (
    <nav className="mt-5 flex gap-6 border-b border-ink-700/60">
      {[
        { id: "tendencia", label: "Tendencia" },
        { id: "yoy", label: "YoY" },
      ].map((t) => (
        <button
          key={t.id}
          onClick={() => setTab(t.id)}
          className={`pb-3 text-sm transition border-b-2 -mb-px ${
            tab === t.id
              ? "text-white border-white"
              : "text-gray-500 border-transparent hover:text-gray-300"
          }`}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}

function WeekSelector() {
  return (
    <div className={`${card} mt-5 p-3 flex gap-2 overflow-x-auto`}>
      {WEEKS.map((w) => {
        const highlight = w.current || w.analyzed;
        return (
          <div
            key={w.id}
            className={`min-w-[150px] rounded-xl px-4 py-3 ${
              highlight ? "bg-ink-800 border border-ink-600" : ""
            }`}
          >
            <div className={`font-bold ${highlight ? "text-white" : "text-gray-500"}`}>{w.label}</div>
            <div className="text-[11px] text-gray-500 mt-0.5">{w.tag ?? w.range}</div>
            {w.tag && <div className="text-[11px] text-gray-600">{w.range}</div>}
          </div>
        );
      })}
    </div>
  );
}

function KpiCard({ kpi }: { kpi: Kpi }) {
  const toneColor =
    kpi.tone === "down" ? "text-accent-down" : kpi.tone === "up" ? "text-white" : "text-white";
  return (
    <div className={`${card} p-5`}>
      <div className={`text-4xl font-black tracking-tight ${toneColor}`}>{kpi.value}</div>
      <div className="mt-2 text-[11px] font-semibold tracking-wider text-gray-500 uppercase">
        {kpi.label}
      </div>
      {kpi.sub && <div className="text-[11px] text-gray-500 mt-1">{kpi.sub}</div>}
      {kpi.trend && (
        <div
          className={`mt-2 inline-flex items-center gap-1 text-xs font-semibold ${
            kpi.trend.up ? "text-accent-up" : "text-accent-down"
          }`}
        >
          {kpi.trend.up ? "▲" : "▼"} {kpi.trend.pct}% vs S24
        </div>
      )}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className={`${card} p-4`}>
      <h3 className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">{title}</h3>
      {children}
    </div>
  );
}

function Toggle({
  value, onChange, options,
}: {
  value: string;
  onChange: (v: any) => void;
  options: { id: string; label: string }[];
}) {
  return (
    <div className="inline-flex rounded-xl bg-ink-850 border border-ink-700/60 p-1">
      {options.map((o) => (
        <button
          key={o.id}
          onClick={() => onChange(o.id)}
          className={`px-3 py-1.5 text-xs rounded-lg transition ${
            value === o.id ? "bg-ink-700 text-white" : "text-gray-500 hover:text-gray-300"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function DarkTooltip({ active, payload, label, kind }: any) {
  if (!active || !payload?.length) return null;
  const v = payload[0].value;
  const formatted =
    kind === "clp" ? fmtCLP(v) : new Intl.NumberFormat("es-CL").format(v) + " u.";
  return (
    <div className="rounded-lg bg-ink-800 border border-ink-600 px-3 py-2 text-xs">
      <div className="text-gray-400">{label}</div>
      <div className="text-white font-semibold">{formatted}</div>
    </div>
  );
}
