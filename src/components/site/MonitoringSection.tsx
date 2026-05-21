import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const usage = [
  { d: "Mon", kwh: 12.4 },
  { d: "Tue", kwh: 9.8 },
  { d: "Wed", kwh: 14.2 },
  { d: "Thu", kwh: 11.1 },
  { d: "Fri", kwh: 18.6 },
  { d: "Sat", kwh: 21.3 },
  { d: "Sun", kwh: 16.7 },
];

export function MonitoringSection() {
  const max = Math.max(...usage.map((u) => u.kwh));
  return (
    <section id="monitoring" className="relative py-24">
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-transparent via-muted/40 to-transparent" />
      <div className="mx-auto max-w-7xl px-4">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Smart monitoring</span>
            <h2 className="mt-3 text-4xl font-semibold tracking-tight text-foreground md:text-5xl">See every watt, before it costs you.</h2>
            <p className="mt-5 text-base leading-relaxed text-muted-foreground">Stream live readings from your ESP32 fleet, visualise daily and monthly trends, and surface anomalies the moment they happen — all from one elegant control surface.</p>
            <ul className="mt-6 space-y-3 text-sm text-foreground">
              {["Per-device online / offline indicators","Power factor and harmonic distortion tracking","Anomaly alerts with root-cause hints","Daily summaries delivered to inbox or app"].map((f) => (
                <li key={f} className="flex items-center gap-3">
                  <span className="grid h-5 w-5 place-items-center rounded-full bg-success/15 text-success">✓</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>

          <div className="relative rounded-3xl border border-border bg-card p-6 shadow-card-soft">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Weekly consumption</div>
                <div className="mt-1 text-2xl font-semibold text-foreground tabular-nums">104.1 kWh</div>
              </div>
              <div className="rounded-full bg-accent/20 px-2.5 py-1 text-xs font-medium text-foreground">Peak: Sat</div>
            </div>
            <div className="mt-6 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={usage} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <defs>
                    <linearGradient id="barFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#1A6EF5" />
                      <stop offset="100%" stopColor="#1A6EF5" stopOpacity={0.35} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 6" stroke="rgba(10,31,68,0.08)" vertical={false} />
                  <XAxis dataKey="d" tick={{ fill: "rgba(10,31,68,0.55)", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "rgba(10,31,68,0.5)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: "rgba(26,110,245,0.06)" }} contentStyle={{ background: "white", border: "1px solid rgba(10,31,68,0.08)", borderRadius: 12, fontSize: 12 }} />
                  <Bar dataKey="kwh" radius={[8, 8, 4, 4]}>
                    {usage.map((u, i) => (
                      <Cell key={i} fill={u.kwh === max ? "#FFD600" : "url(#barFill)"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-3">
              {[{ l: "Avg / day", v: "14.9", u: "kWh" },{ l: "Saved", v: "8.2", u: "kWh" },{ l: "Forecast", v: "₹1,420", u: "" }].map((m) => (
                <div key={m.l} className="rounded-xl bg-muted/60 p-3">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{m.l}</div>
                  <div className="mt-1 text-base font-semibold text-foreground tabular-nums">{m.v} <span className="text-xs font-normal text-muted-foreground">{m.u}</span></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}