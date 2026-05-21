import { Zap } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border bg-card">
      <div className="mx-auto max-w-7xl px-4 py-14">
        <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-2">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary text-primary-foreground">
                <Zap className="h-4 w-4" />
              </span>
              <span className="text-lg font-semibold tracking-tight text-secondary">
                Amp<span className="text-primary">Aware</span>
              </span>
            </div>
            <p className="mt-4 max-w-xs text-sm text-muted-foreground">Smart energy intelligence for homes, factories and utilities — engineered in Kerala for the world.</p>
          </div>
          {[
            { t: "Product", l: ["Platform", "Monitoring", "Billing", "Pricing"] },
            { t: "Company", l: ["About", "Careers", "Press", "Contact"] },
            { t: "Resources", l: ["Docs", "API", "Status", "Security"] },
          ].map((c) => (
            <div key={c.t}>
              <div className="text-sm font-semibold text-secondary">{c.t}</div>
              <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                {c.l.map((i) => (
                  <li key={i}><a href="#" className="transition-colors hover:text-foreground">{i}</a></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-6 text-xs text-muted-foreground">
          <div>© 2026 AmpAware Energy Systems. All rights reserved.</div>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-foreground">Privacy</a>
            <a href="#" className="hover:text-foreground">Terms</a>
            <a href="#" className="hover:text-foreground">Security</a>
          </div>
        </div>
      </div>
    </footer>
  );
}