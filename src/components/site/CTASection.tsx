import { ArrowRight } from "lucide-react";

export function CTASection() {
  return (
    <section className="px-4 pb-24">
      <div className="relative mx-auto max-w-6xl overflow-hidden rounded-3xl bg-gradient-hero p-10 text-center shadow-elegant md:p-16">
        <div className="absolute inset-0 -z-10 grid-pattern opacity-30" />
        <div className="absolute -left-20 -top-20 -z-10 h-72 w-72 rounded-full bg-primary/30 blur-3xl" />
        <div className="absolute -bottom-20 -right-20 -z-10 h-72 w-72 rounded-full bg-success/20 blur-3xl" />
        <h2 className="mx-auto max-w-2xl text-4xl font-semibold tracking-tight text-foreground md:text-5xl">
          Plug in. Power up. <span className="text-gradient-primary">Pay less.</span>
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-base text-muted-foreground">Deploy AmpAware on your first ESP32 in under 10 minutes. No credit card, no rip-and-replace.</p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <button className="group inline-flex items-center gap-2 rounded-xl bg-gradient-primary px-6 py-3.5 text-sm font-semibold text-primary-foreground shadow-elegant transition-transform hover:-translate-y-0.5">
            Start free trial
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </button>
          <button className="inline-flex items-center gap-2 rounded-xl border border-border bg-card/50 px-6 py-3.5 text-sm font-semibold text-foreground backdrop-blur transition-colors hover:bg-white/10">
            Talk to engineering
          </button>
        </div>
      </div>
    </section>
  );
}