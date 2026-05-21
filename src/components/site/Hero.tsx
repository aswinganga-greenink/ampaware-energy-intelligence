import heroImg from "@/assets/hero-energy.jpg";
import { ArrowRight, Activity, ShieldCheck } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { LiveDashboardPreview } from "./LiveDashboardPreview";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Background canvas */}
      <div className="absolute inset-0 -z-10 bg-gradient-hero" />
      <img
        src={heroImg}
        alt=""
        width={1920}
        height={1080}
        className="absolute inset-0 -z-10 h-full w-full object-cover opacity-50 mix-blend-screen"
      />
      <div className="absolute inset-0 -z-10 grid-pattern opacity-40" />
      <div className="absolute -left-40 top-20 -z-10 h-96 w-96 rounded-full bg-primary/30 blur-3xl" />
      <div className="absolute -right-40 bottom-0 -z-10 h-96 w-96 rounded-full bg-success/20 blur-3xl" />

      <div className="mx-auto max-w-7xl px-4 pb-24 pt-20 md:pb-32 md:pt-28">
        <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_1fr]">
          <div className="animate-fade-up text-secondary-foreground">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-medium text-white/80 backdrop-blur">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
              </span>
              Live across 12,400 ESP32 devices
            </span>

            <h1 className="mt-6 text-5xl font-semibold leading-[1.05] tracking-tight text-white md:text-6xl lg:text-7xl">
              Energy intelligence,
              <br />
              <span className="text-gradient-primary">measured to the watt.</span>
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/70">
              AmpAware streams voltage, current, power factor and kWh from your
              smart meters in real time — then turns it into KSEB-accurate bills,
              forecasts and savings you can act on.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link to="/dashboard" className="group inline-flex items-center gap-2 rounded-xl bg-gradient-primary px-6 py-3.5 text-sm font-semibold text-primary-foreground shadow-elegant transition-transform hover:-translate-y-0.5">
                Launch dashboard
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <button className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white backdrop-blur transition-colors hover:bg-white/10">
                Watch 90s demo
              </button>
            </div>

            <dl className="mt-12 grid max-w-lg grid-cols-3 gap-6 border-t border-white/10 pt-6">
              {[
                { k: "12.4k", v: "Live devices" },
                { k: "99.98%", v: "Uptime" },
                { k: "₹2.3Cr", v: "Saved / yr" },
              ].map((s) => (
                <div key={s.v}>
                  <dt className="text-2xl font-semibold text-white">{s.k}</dt>
                  <dd className="mt-1 text-xs uppercase tracking-wider text-white/50">{s.v}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Right preview */}
          <div className="relative animate-fade-up [animation-delay:160ms]">
            <div className="absolute -inset-6 -z-10 rounded-3xl bg-primary/20 blur-3xl" />
            <LiveDashboardPreview />

            <div className="absolute -bottom-6 -left-6 hidden items-center gap-3 rounded-2xl glass-dark px-4 py-3 text-white shadow-elegant md:flex">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-success/15">
                <ShieldCheck className="h-4 w-4 text-success" />
              </span>
              <div className="text-xs">
                <div className="font-semibold">All systems healthy</div>
                <div className="text-white/60">PF 0.98 · 230.4 V nominal</div>
              </div>
            </div>
            <div className="absolute -right-4 -top-4 hidden items-center gap-2 rounded-full glass-dark px-3 py-2 text-xs text-white md:flex">
              <Activity className="h-3.5 w-3.5 text-accent" />
              Streaming · 1.2s latency
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}