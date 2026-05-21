import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Bolt, Gauge, Plug, TrendingDown } from "lucide-react";

function seed() {
  return Array.from({ length: 28 }, (_, i) => ({
    t: i,
    w: 380 + Math.sin(i / 2.4) * 80 + Math.random() * 60,
  }));
}

export function LiveDashboardPreview() {
  const [data, setData] = useState(seed);
  const [live, setLive] = useState({ v: 230.4, a: 6.2, pf: 0.98, kwh: 142.6 });

  useEffect(() => {
    const id = setInterval(() => {
      setData((d) => {
        const next = [...d.slice(1), {
          t: d[d.length - 1].t + 1,
          w: 360 + Math.sin(d.length / 2) * 90 + Math.random() * 80,
        }];
        return next;
      });
      setLive((s) => ({
        v: +(229 + Math.random() * 3).toFixed(1),
        a: +(5.6 + Math.random() * 1.2).toFixed(2),
        pf: +(0.94 + Math.random() * 0.05).toFixed(2),
        kwh: +(s.kwh + 0.04).toFixed(2),
      }));
    }, 1600);
    return () => clearInterval(id);
  }, []);

  const watts = useMemo(() => Math.round(data[data.length - 1].w), [data]);

  return (
    <div className="rounded-3xl glass-dark p-4 shadow-elegant">
      <div className="flex items-center justify-between px-2 pb-3">
        <div className="flex items-center gap-2 text-xs text-white/70">
          <span className="h-2 w-2 animate-pulse rounded-full bg-success" />
          Home / Main feeder
        </div>
        <div className="flex items-center gap-1 text-[11px] text-white/50">
          <span className="rounded-md bg-white/5 px-1.5 py-0.5">1H</span>
          <span className="rounded-md bg-primary/30 px-1.5 py-0.5 text-white">24H</span>
          <span className="rounded-md bg-white/5 px-1.5 py-0.5">7D</span>
        </div>
      </div>

      {/* Big metric */}
      <div className="rounded-2xl bg-gradient-to-br from-white/[0.06] to-white/[0.02] p-5">
        <div className="flex items-end justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-white/50">Live load</div>
            <div className="mt-1 flex items-baseline gap-2 text-white">
              <span className="text-5xl font-semibold tabular-nums tracking-tight">{watts}</span>
              <span className="text-sm text-white/60">W</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 rounded-full bg-success/15 px-2.5 py-1 text-xs font-medium text-success">
            <TrendingDown className="h-3 w-3" /> 12% vs avg
          </div>
        </div>

        <div className="mt-3 h-32">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="liveFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(217 91% 60%)" stopOpacity={0.55} />
                  <stop offset="100%" stopColor="hsl(217 91% 60%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="t" hide />
              <YAxis hide domain={["dataMin-40", "dataMax+40"]} />
              <Tooltip
                contentStyle={{
                  background: "rgba(10,31,68,0.9)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 10,
                  color: "white",
                  fontSize: 12,
                }}
                labelStyle={{ color: "rgba(255,255,255,0.5)" }}
                formatter={(v: number) => [`${Math.round(v)} W`, "Load"]}
              />
              <Area
                type="monotone"
                dataKey="w"
                stroke="#1A6EF5"
                strokeWidth={2}
                fill="url(#liveFill)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Metric tiles */}
      <div className="mt-3 grid grid-cols-4 gap-2">
        {[
          { i: Bolt, l: "Voltage", v: `${live.v}`, u: "V" },
          { i: Plug, l: "Current", v: `${live.a}`, u: "A" },
          { i: Gauge, l: "PF", v: `${live.pf}`, u: "" },
          { i: Bolt, l: "Today", v: `${live.kwh}`, u: "kWh" },
        ].map(({ i: Icon, l, v, u }) => (
          <div key={l} className="rounded-xl bg-white/[0.04] p-3">
            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-white/45">
              <Icon className="h-3 w-3" />
              {l}
            </div>
            <div className="mt-1 text-sm font-semibold text-white tabular-nums">
              {v}
              <span className="ml-0.5 text-[10px] font-normal text-white/50">{u}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}