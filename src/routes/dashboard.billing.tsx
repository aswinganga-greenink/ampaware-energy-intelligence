import { createFileRoute } from "@tanstack/react-router";
import {
  CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Receipt, Download, TrendingUp } from "lucide-react";

export const Route = createFileRoute("/dashboard/billing")({
  component: BillingPage,
});

const CYCLE = Array.from({ length: 30 }, (_, i) => ({
  d: i + 1,
  actual: Math.round(60 + i * 6.2 + Math.sin(i / 3) * 14),
  forecast: Math.round(60 + i * 6.0 + Math.cos(i / 4) * 10),
}));

const SLABS = [
  { range: "0–50", rate: "₹3.15", units: 50, amount: 157.5 },
  { range: "51–100", rate: "₹3.70", units: 50, amount: 185 },
  { range: "101–150", rate: "₹4.80", units: 50, amount: 240 },
  { range: "151–200", rate: "₹6.40", units: 42, amount: 268.8 },
];

const TOOLTIP_STYLE = {
  background: "var(--color-popover)", border: "1px solid var(--color-border)",
  borderRadius: 12, fontSize: 12, color: "var(--color-foreground)",
};

function BillingPage() {
  const subtotal = SLABS.reduce((s, r) => s + r.amount, 0);
  const duty = subtotal * 0.1;
  const total = Math.round(subtotal + duty + 65);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">KSEB Billing</h1>
          <p className="mt-1 text-sm text-muted-foreground">Slab-accurate forecasts driven by your meter stream.</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-muted">
          <Download className="h-4 w-4" /> Export PDF
        </button>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl bg-gradient-primary p-6 text-primary-foreground shadow-elegant md:col-span-1">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider opacity-80">
            <Receipt className="h-4 w-4" /> Projected this cycle
          </div>
          <div className="mt-2 text-5xl font-semibold tabular-nums">₹{total.toLocaleString("en-IN")}</div>
          <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-xs">
            <TrendingUp className="h-3 w-3" /> 6.4% vs last cycle
          </div>
          <dl className="mt-6 space-y-1.5 text-sm">
            <div className="flex justify-between"><dt className="opacity-80">Units consumed</dt><dd>192 kWh</dd></div>
            <div className="flex justify-between"><dt className="opacity-80">Cycle days</dt><dd>30</dd></div>
            <div className="flex justify-between"><dt className="opacity-80">Avg / day</dt><dd>6.4 kWh</dd></div>
          </dl>
        </div>

        <div className="rounded-2xl border border-border bg-card p-5 shadow-card-soft md:col-span-2">
          <h2 className="text-base font-semibold text-foreground">Actual vs forecast</h2>
          <p className="text-xs text-muted-foreground">Daily cumulative consumption vs the AI forecast.</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={CYCLE} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="d" stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Line type="monotone" dataKey="actual" stroke="var(--color-primary)" strokeWidth={2.5} dot={false} />
                <Line type="monotone" dataKey="forecast" stroke="var(--color-success)" strokeWidth={2} strokeDasharray="5 5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-card-soft">
        <div className="border-b border-border p-5">
          <h2 className="text-base font-semibold text-foreground">Slab breakdown</h2>
          <p className="text-xs text-muted-foreground">How your consumption maps to KSEB tariff slabs.</p>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="px-5 py-3 text-left">Slab (units)</th>
              <th className="px-5 py-3 text-left">Rate / unit</th>
              <th className="px-5 py-3 text-right">Units used</th>
              <th className="px-5 py-3 text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {SLABS.map((s) => (
              <tr key={s.range} className="text-foreground">
                <td className="px-5 py-3 font-medium">{s.range}</td>
                <td className="px-5 py-3 text-muted-foreground">{s.rate}</td>
                <td className="px-5 py-3 text-right tabular-nums">{s.units}</td>
                <td className="px-5 py-3 text-right tabular-nums">₹{s.amount.toFixed(2)}</td>
              </tr>
            ))}
            <tr className="bg-muted/30 font-semibold text-foreground">
              <td className="px-5 py-3" colSpan={3}>Energy charge</td>
              <td className="px-5 py-3 text-right tabular-nums">₹{subtotal.toFixed(2)}</td>
            </tr>
            <tr className="text-muted-foreground">
              <td className="px-5 py-3" colSpan={3}>Electricity duty (10%)</td>
              <td className="px-5 py-3 text-right tabular-nums">₹{duty.toFixed(2)}</td>
            </tr>
            <tr className="text-muted-foreground">
              <td className="px-5 py-3" colSpan={3}>Fixed + meter rent</td>
              <td className="px-5 py-3 text-right tabular-nums">₹65.00</td>
            </tr>
            <tr className="bg-primary/5 text-base font-semibold text-foreground">
              <td className="px-5 py-4" colSpan={3}>Total projected</td>
              <td className="px-5 py-4 text-right tabular-nums text-primary">₹{total.toLocaleString("en-IN")}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}