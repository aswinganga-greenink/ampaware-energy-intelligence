import { Lock, KeyRound, ShieldCheck, Cpu } from "lucide-react";

const pillars = [
  { i: ShieldCheck, t: "End-to-end TLS", b: "Every ESP32 packet encrypted in transit and at rest." },
  { i: KeyRound, t: "JWT + RBAC", b: "Granular roles across customers, technicians and admins." },
  { i: Lock, t: "Hashed secrets", b: "Argon2id password hashing with rotated session keys." },
  { i: Cpu, t: "Edge isolation", b: "Per-device certificates with revocation and replay protection." },
];

export function SecuritySection() {
  return (
    <section id="security" className="py-24">
      <div className="mx-auto max-w-7xl px-4">
        <div className="grid items-center gap-12 lg:grid-cols-[1fr_1.2fr]">
          <div>
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Trust & security</span>
            <h2 className="mt-3 text-4xl font-semibold tracking-tight text-foreground md:text-5xl">Built for the grid. Hardened for production.</h2>
            <p className="mt-4 text-base leading-relaxed text-muted-foreground">AmpAware is engineered with the same security primitives that utilities and industrial IoT operators demand — without the friction.</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {pillars.map(({ i: I, t, b }) => (
              <div key={t} className="rounded-2xl border border-border bg-card p-5 shadow-card-soft">
                <span className="inline-grid h-10 w-10 place-items-center rounded-xl bg-secondary text-secondary-foreground">
                  <I className="h-4 w-4" />
                </span>
                <h3 className="mt-4 text-base font-semibold text-foreground">{t}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{b}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}