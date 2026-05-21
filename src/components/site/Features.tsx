import { Activity, BrainCircuit, Receipt, Radio, ShieldCheck, Sparkles } from "lucide-react";

const items = [
  { icon: Radio, title: "Real-time ingestion", body: "MQTT and REST pipelines stream voltage, current, watt, kWh and PF from ESP32 devices with sub-second latency." },
  { icon: Activity, title: "Live visualization", body: "Interactive area, heatmap and flow charts rendered with TimescaleDB-backed precision." },
  { icon: Receipt, title: "KSEB billing engine", body: "Slab, peak-hour and dynamic tariff calculations with taxes and end-of-cycle forecasting." },
  { icon: BrainCircuit, title: "AI anomaly detection", body: "Detect spikes, leakages and failing appliances before they impact your bill." },
  { icon: Sparkles, title: "Savings insights", body: "Appliance-level estimates and personalised recommendations tuned to your load profile." },
  { icon: ShieldCheck, title: "Enterprise security", body: "JWT sessions, role-based access control and end-to-end TLS on every device channel." },
];

export function Features() {
  return (
    <section id="platform" className="relative py-24">
      <div className="mx-auto max-w-7xl px-4">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">The platform</span>
          <h2 className="mt-3 text-4xl font-semibold tracking-tight text-foreground md:text-5xl">One stack for every electron.</h2>
          <p className="mt-4 text-base text-muted-foreground">From the meter on the wall to the dashboard in your pocket — AmpAware is engineered as a single, coherent energy intelligence layer.</p>
        </div>
        <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map(({ icon: Icon, title, body }) => (
            <div key={title} className="group relative overflow-hidden rounded-2xl border border-border bg-card p-6 shadow-card-soft transition-all hover:-translate-y-1 hover:shadow-elegant">
              <div className="absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
              <span className="inline-grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary">
                <Icon className="h-5 w-5" strokeWidth={1.8} />
              </span>
              <h3 className="mt-5 text-lg font-semibold text-foreground">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}