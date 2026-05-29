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

const PIE_COLORS = ["var(--color-primary)", "var(--color-success)", "var(--color-accent)", "var(--color-chart-4)"];

function Overview() {
  const [live, setLive] = useState({ v: 0, a: 0, w: 0, pf: 0, kwh: 0, devices: 0 });
  const [stream, setStream] = useState(() => Array.from({ length: 30 }, (_, i) => ({ t: i, w: 0 })));
  const [week, setWeek] = useState<any[]>([]);
  const [day, setDay] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);

  const [projectedBill, setProjectedBill] = useState(0);

  useEffect(() => {
    let id: any;
    const fetchMetrics = async () => {
      try {
        const { api } = await import("@/lib/api");
        const res = await api.get("/dashboard/summary");
        if (res?.metrics) {
          const m = res.metrics;
          if (m.live) {
            setLive({
              v: m.live.v || 0,
              a: m.live.a || 0,
              w: m.live.w || 0,
              pf: m.live.pf || 0,
              kwh: m.live.kwh || 0,
              devices: m.active_devices || 0
            });
            setStream((d) => [...d.slice(1), { t: d[d.length - 1].t + 1, w: m.live.w || 0 }]);
          }
          if (m.week_data) setWeek(m.week_data);
          if (m.day_data) setDay(m.day_data);
          if (m.device_data) setDevices(m.device_data);
          if (m.projected_bill !== undefined) setProjectedBill(m.projected_bill);
        }
      } catch (e) {
        console.error("Failed to fetch dashboard metrics", e);
      }
    };
    
    fetchMetrics(); // Initial fetch
    id = setInterval(fetchMetrics, 3000); // Poll every 3s to not overwhelm the backend

    return () => clearInterval(id);
  }, []);

  // Dynamic metric calculations
  const avgW = day.length ? day.reduce((acc, d) => acc + d.load, 0) / day.length : 0;
  const wDiff = avgW > 0 ? ((live.w - avgW) / avgW) * 100 : 0;
  
  const yestKwh = week.length > 1 ? week[week.length - 2].kwh : 0;
  const kwhDiff = yestKwh > 0 ? ((live.kwh - yestKwh) / yestKwh) * 100 : 0;

  const pfStatus = live.pf >= 0.95 ? { t: "Excellent", c: "text-success" } : live.pf >= 0.85 ? { t: "Good", c: "text-accent-foreground" } : { t: "Poor", c: "text-destructive" };
  const vStatus = live.v >= 220 && live.v <= 240 ? { t: "Nominal", c: "text-muted-foreground" } : { t: "Fluctuating", c: "text-accent-foreground" };

  const metrics = [
    { i: Zap, l: "Live power", v: `${live.w}`, u: "W", t: `${wDiff > 0 ? "▲" : "▼"} ${Math.abs(wDiff).toFixed(1)}% vs avg`, c: wDiff > 0 ? "text-accent-foreground" : "text-success" },
    { i: Bolt, l: "Voltage", v: `${live.v}`, u: "V", t: vStatus.t, c: vStatus.c },
    { i: Plug, l: "Current", v: `${live.a}`, u: "A", t: live.a > 0 ? "Stable" : "Idle", c: "text-muted-foreground" },
    { i: Gauge, l: "Power factor", v: `${live.pf}`, u: "", t: pfStatus.t, c: pfStatus.c },
    { i: Activity, l: "Today", v: `${live.kwh.toFixed(1)}`, u: "kWh", t: `${kwhDiff > 0 ? "▲" : "▼"} ${Math.abs(kwhDiff).toFixed(1)}% vs yest`, c: kwhDiff > 0 ? "text-accent-foreground" : "text-success" },
    { i: Cpu, l: "Active devices", v: `${live.devices}`, u: "", t: live.devices > 0 ? "Online" : "Offline", c: live.devices > 0 ? "text-success" : "text-destructive" },
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

      {/* Bill Estimator Horizontal Strip */}
      <div className="rounded-2xl border border-primary/20 bg-gradient-primary p-5 sm:p-6 text-primary-foreground shadow-elegant flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Bill estimator</h2>
          <p className="mt-1 text-sm opacity-80">Projected KSEB charge for the current cycle.</p>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center gap-6 sm:gap-10">
          <div>
            <div className="text-xs uppercase tracking-wider opacity-80 mb-1">Projected Total</div>
            <div className="text-4xl sm:text-5xl font-semibold tabular-nums tracking-tight">₹{projectedBill.toLocaleString("en-IN")}</div>
            <div className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium bg-primary-foreground/10 px-2 py-1 rounded-md opacity-90">
              <TrendingUp className="h-3.5 w-3.5" /> 6.4% vs last cycle
            </div>
          </div>
          <div className="hidden sm:block w-px h-16 bg-primary-foreground/20"></div>
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm sm:text-base">
            <div className="opacity-80">Consumed</div>
            <div className="tabular-nums font-semibold text-right">{live.kwh.toFixed(1)} kWh</div>
            <div className="opacity-80">Forecast</div>
            <div className="tabular-nums font-semibold text-right">{Math.round(live.kwh * 2.1)} kWh</div>
            <div className="opacity-80">KSEB Slab</div>
            <div className="font-semibold text-right">151–200 units</div>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-border bg-card p-5 shadow-card-soft">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-foreground">Real-time load</h2>
            <p className="text-xs text-muted-foreground">Live wattage from your main feeder.</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-semibold tabular-nums text-foreground">{live.w} W</div>
            <div className={`inline-flex items-center gap-1 text-xs ${wDiff > 0 ? "text-accent-foreground" : "text-success"}`}>
              {wDiff > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />} 
              {Math.abs(wDiff).toFixed(1)}% vs avg
            </div>
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

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card-soft lg:col-span-2">
          <h2 className="text-base font-semibold text-foreground">Weekly consumption</h2>
          <p className="text-xs text-muted-foreground">kWh across the last 7 days.</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={week} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
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
                <Pie data={devices} dataKey="value" innerRadius={50} outerRadius={80} paddingAngle={3}>
                  {devices.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-2 space-y-1.5 text-sm">
            {devices.map((d, i) => (
              <li key={d.name} className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-muted-foreground">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
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
            <AreaChart data={day} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
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