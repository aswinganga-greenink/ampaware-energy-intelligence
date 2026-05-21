import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Receipt, TrendingUp, Sparkles } from "lucide-react";

const bill = Array.from({ length: 12 }, (_, i) => ({
  m: ["J","F","M","A","M","J","J","A","S","O","N","D"][i],
  actual: 800 + Math.round(Math.sin(i / 1.6) * 220 + i * 25),
  predicted: 820 + Math.round(Math.sin(i / 1.6) * 240 + i * 30),
}));

export function BillingSection() {
  return (
    <section id="billing" className="relative overflow-hidden py-24">
      <div className="absolute inset-0 -z-10 bg-secondary" />
      <div className="absolute inset-0 -z-10 grid-pattern opacity-30" />
      <div className="absolute -right-32 top-10 -z-10 h-96 w-96 rounded-full bg-primary/30 blur-3xl" />
      <div className="mx-auto max-w-7xl px-4 text-white">
        <div className="grid items-center gap-12 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-medium text-white/80">
              <Receipt className="h-3.5 w-3.5 text-accent" />
              KSEB Billing engine
            </span>
            <h2 className="mt-4 text-4xl font-semibold tracking-tight md:text-5xl">Know your bill, <span className="text-accent">before KSEB does.</span></h2>
            <p className="mt-5 max-w-lg text-base leading-relaxed text-white/70">Slab calculations, peak-hour multipliers, fixed charges, duties and taxes — modelled to the rupee. Forecast the next cycle, simulate tariff changes and act on optimisation hints in seconds.</p>
            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {[{ i: TrendingUp, t: "Cycle forecast", v: "₹1,842", s: "± 3.4% accuracy" },{ i: Sparkles, t: "Optimisation", v: "₹312/mo", s: "Recommended savings" }].map(({ i: I, t, v, s }) => (
                <div key={t} className="glass-dark rounded-2xl p-4">
                  <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-white/55">
                    <I className="h-3.5 w-3.5 text-accent" />
                    {t}
                  </div>
                  <div className="mt-2 text-2xl font-semibold tabular-nums">{v}</div>
                  <div className="mt-1 text-xs text-white/55">{s}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl glass-dark p-6 shadow-elegant">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-white/55">Billing forecast — 2026</div>
                <div className="mt-1 text-3xl font-semibold tabular-nums">₹14,260</div>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1.5 text-white/70"><span className="h-2 w-2 rounded-full bg-primary" /> Actual</span>
                <span className="flex items-center gap-1.5 text-white/70"><span className="h-2 w-2 rounded-full bg-accent" /> Predicted</span>
              </div>
            </div>
            <div className="mt-6 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={bill} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <XAxis dataKey="m" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: "rgba(10,31,68,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, color: "white", fontSize: 12 }} />
                  <Line type="monotone" dataKey="actual" stroke="#1A6EF5" strokeWidth={2.5} dot={{ r: 3, fill: "#1A6EF5" }} activeDot={{ r: 5 }} />
                  <Line type="monotone" dataKey="predicted" stroke="#FFD600" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}