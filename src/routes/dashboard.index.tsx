import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Activity, Bolt, Gauge, Plug, TrendingDown, TrendingUp, Zap, Cpu } from "lucide-react";

export const Route = createFileRoute("/dashboard/")({
  component: Overview,
});

const TOOLTIP_STYLE = {
  background: "var(--color-popover)",
  border: "1px solid var(--color-border)",
  borderRadius: 12,
  fontSize: 12,
  color: "var(--color-foreground)",
};

const WEEK = [
  { d: "Mon", kwh: 18.2 }, { d: "Tue", kwh: 21.4 }, { d: "Wed", kwh: 19.8 },
  { d: "Thu", kwh: 24.6 }, { d: "Fri", kwh: 22.1 }, { d: "Sat", kwh: 17.3 },
  { d: "Sun", kwh: 15.9 },
];

const DEVICES = [
  { name: "HVAC", value: 38 },
  { name: "Lighting", value: 22 },
  { name: "Appliances", value: 24 },
  { name: "Other", value: 16 },
];
const PIE_COLORS = ["var(--color-primary)", "var(--color-success)", "var(--color-accent)", "var(--color-chart-4)"];

const DAY = Array.from({ length: 24 }, (_, h) => ({
  h: `${String(h).padStart(2, "0")}:00`,
  load: Math.round(280 + Math.sin(h / 3.2) * 120 + ((h * 53) % 80)),
}));

function Overview() {
  const [live, setLive] = useState({ v: 230.4, a: 6.2, w: 1428, pf: 0.97, kwh: 142.6, devices: 24 });
  const [stream, setStream] = useState(() =>
    Array.from({ length: 30 }, (_, i) => ({ t: i, w: Math.round(380 + Math.sin(i / 2) * 80 + (i * 19) % 50) }))
  );

  useEffect(() => {
    let id: any;
    const fetchMetrics = async () => {
      try {
        const { api } = await import("@/lib/api");
        const res = await api.get("/dashboard/summary");
        if (res?.metrics?.live) {
          const l = res.metrics.live;
          // Only update if we got valid non-zero data, otherwise use the previous or simulated data
          if (l.v > 0) {
            setLive(l);
            setStream((d) => [...d.slice(1), { t: d[d.length - 1].t + 1, w: l.w }]);
            return;
          }
        }
      } catch (e) {
        console.error("Failed to fetch dashboard metrics", e);
      }
      
      // Fallback to simulation if backend has no data or fails
      setLive((s) => ({
        v: +(229 + Math.random() * 3).toFixed(1),
        a: +(5.6 + Math.random() * 1.4).toFixed(2),
        w: Math.round(1380 + Math.random() * 220),
        pf: +(0.94 + Math.random() * 0.05).toFixed(2),
        kwh: +(s.kwh + 0.04).toFixed(2),
        devices: s.devices,
      }));
      setStream((d) => [...d.slice(1), { t: d[d.length - 1].t + 1, w: Math.round(360 + Math.random() * 180) }]);
    };
    
    fetchMetrics(); // Initial fetch
    id = setInterval(fetchMetrics, 3000); // Poll every 3s to not overwhelm the backend

    return () => clearInterval(id);
  }, []);

  const projectedBill = useMemo(() => Math.round(live.kwh * 32.4 + 220), [live.kwh]);

  const metrics = [
    { i: Zap, l: "Live power", v: `${live.w}`, u: "W", t: "▼ 12% vs avg", c: "text-success" },
    { i: Bolt, l: "Voltage", v: `${live.v}`, u: "V", t: "Nominal", c: "text-muted-foreground" },
    { i: Plug, l: "Current", v: `${live.a}`, u: "A", t: "Stable", c: "text-muted-foreground" },
    { i: Gauge, l: "Power factor", v: `${live.pf}`, u: "", t: "Excellent", c: "text-success" },
    { i: Activity, l: "Today", v: `${live.kwh.toFixed(1)}`, u: "kWh", t: "▲ 4.2%", c: "text-accent-foreground" },
    { i: Cpu, l: "Active devices", v: `${live.devices}`, u: "", t: "All online", c: "text-success" },
  ];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Overview</h1>
          <p className="mt-1 text-sm text-muted-foreground">Real-time energy intelligence across your sites.</p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
          </span>
          Streaming · 1.2s latency
        </div>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {metrics.map((m) => (
          <div key={m.l} className="rounded-2xl border border-border bg-card p-4 shadow-card-soft">
            <div className="flex items-center justify-between">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary">
                <m.i className="h-4 w-4" />
              </span>
              <span className={`text-[11px] font-medium ${m.c}`}>{m.t}</span>
            </div>
            <div className="mt-3 text-xs uppercase tracking-wider text-muted-foreground">{m.l}</div>
            <div className="mt-1 flex items-baseline gap-1 text-2xl font-semibold tabular-nums text-foreground">
              {m.v}<span className="text-xs font-normal text-muted-foreground">{m.u}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card-soft lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-foreground">Real-time load</h2>
              <p className="text-xs text-muted-foreground">Live wattage from your main feeder.</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-semibold tabular-nums text-foreground">{live.w} W</div>
              <div className="inline-flex items-center gap-1 text-xs text-success"><TrendingDown className="h-3 w-3" /> 12% vs avg</div>
            </div>
          </div>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stream} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="loadFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="t" hide />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => [`${Math.round(v)} W`, "Load"]} />
                <Area type="monotone" dataKey="w" stroke="var(--color-primary)" strokeWidth={2} fill="url(#loadFill)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-5 shadow-card-soft">
          <h2 className="text-base font-semibold text-foreground">Bill estimator</h2>
          <p className="text-xs text-muted-foreground">Projected KSEB charge this cycle.</p>
          <div className="mt-5 rounded-2xl bg-gradient-primary p-5 text-primary-foreground shadow-elegant">
            <div className="text-xs uppercase tracking-wider opacity-80">Projected total</div>
            <div className="mt-1 text-4xl font-semibold tabular-nums">₹{projectedBill.toLocaleString("en-IN")}</div>
            <div className="mt-1 inline-flex items-center gap-1 text-xs opacity-90">
              <TrendingUp className="h-3 w-3" /> 6.4% vs last cycle
            </div>
          </div>
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between text-muted-foreground"><dt>Consumed</dt><dd className="tabular-nums text-foreground">{live.kwh.toFixed(1)} kWh</dd></div>
            <div className="flex justify-between text-muted-foreground"><dt>Forecast</dt><dd className="tabular-nums text-foreground">{Math.round(live.kwh * 2.1)} kWh</dd></div>
            <div className="flex justify-between text-muted-foreground"><dt>Slab</dt><dd className="text-foreground">151–200 units</dd></div>
          </dl>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card-soft lg:col-span-2">
          <h2 className="text-base font-semibold text-foreground">Weekly consumption</h2>
          <p className="text-xs text-muted-foreground">kWh across the last 7 days.</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={WEEK} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="d" stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => [`${v} kWh`, "Consumption"]} />
                <Bar dataKey="kwh" radius={[8, 8, 0, 0]} fill="var(--color-primary)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card-soft">
          <h2 className="text-base font-semibold text-foreground">Device breakdown</h2>
          <p className="text-xs text-muted-foreground">Share of today's consumption.</p>
          <div className="mt-2 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number, n: string) => [`${v}%`, n]} />
                <Pie data={DEVICES} dataKey="value" innerRadius={50} outerRadius={80} paddingAngle={3}>
                  {DEVICES.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-2 space-y-1.5 text-sm">
            {DEVICES.map((d, i) => (
              <li key={d.name} className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-muted-foreground">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: PIE_COLORS[i] }} />
                  {d.name}
                </span>
                <span className="tabular-nums text-foreground">{d.value}%</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="rounded-2xl border border-border bg-card p-5 shadow-card-soft">
        <h2 className="text-base font-semibold text-foreground">Hourly load curve</h2>
        <p className="text-xs text-muted-foreground">Average wattage across 24 hours.</p>
        <div className="mt-4 h-56">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={DAY} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="dayFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-success)" stopOpacity={0.45} />
                  <stop offset="100%" stopColor="var(--color-success)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="h" stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => [`${v} W`, "Load"]} />
              <Area type="monotone" dataKey="load" stroke="var(--color-success)" strokeWidth={2} fill="url(#dayFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}