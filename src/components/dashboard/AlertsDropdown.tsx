import { useEffect, useRef, useState } from "react";
import { Bell, AlertTriangle, Zap, TrendingUp } from "lucide-react";

const ALERTS = [
  { i: AlertTriangle, c: "text-destructive", t: "Voltage spike detected", d: "Feeder A · 248V for 4s · 2m ago" },
  { i: Zap, c: "text-accent", t: "Anomalous load on Compressor 3", d: "+34% above 7-day baseline · 18m ago" },
  { i: TrendingUp, c: "text-success", t: "Forecast updated", d: "Projected bill revised to ₹4,820 · 1h ago" },
];

export function AlertsDropdown() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-foreground hover:bg-muted"
        aria-label="Alerts"
      >
        <Bell className="h-4 w-4" />
        <span className="absolute right-1.5 top-1.5 grid h-4 w-4 place-items-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground">
          {ALERTS.length}
        </span>
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 origin-top-right rounded-2xl border border-border bg-popover p-2 shadow-elegant animate-fade-up">
          <div className="flex items-center justify-between px-3 py-2">
            <span className="text-sm font-semibold text-foreground">Anomalies &amp; alerts</span>
            <span className="text-xs text-muted-foreground">Live</span>
          </div>
          <ul className="space-y-1">
            {ALERTS.map((a) => (
              <li key={a.t} className="flex gap-3 rounded-xl p-3 transition-colors hover:bg-muted">
                <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-muted ${a.c}`}>
                  <a.i className="h-4 w-4" />
                </span>
                <div className="min-w-0">
                  <div className="text-sm font-medium text-foreground">{a.t}</div>
                  <div className="text-xs text-muted-foreground">{a.d}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}