import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";
import { Bell, Moon, Sun, Wifi, Save } from "lucide-react";

export const Route = createFileRoute("/dashboard/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const { user } = useAuth();
  const { theme, toggle } = useTheme();
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [alerts, setAlerts] = useState(true);
  const [emailDigest, setEmailDigest] = useState(true);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your profile, preferences and devices.</p>
      </header>

      <Card title="Profile" desc="Your account details.">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Full name" value={name} onChange={setName} />
          <Field label="Email" type="email" value={email} onChange={setEmail} />
        </div>
        <div className="mt-5 flex justify-end">
          <button className="inline-flex items-center gap-2 rounded-xl bg-gradient-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-elegant">
            <Save className="h-4 w-4" /> Save changes
          </button>
        </div>
      </Card>

      <Card title="Appearance" desc="Switch between light and dark themes.">
        <button
          onClick={toggle}
          className="flex w-full items-center justify-between rounded-xl border border-border bg-muted/40 p-4 text-left"
        >
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-lg bg-card text-foreground">
              {theme === "dark" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            </span>
            <div>
              <div className="text-sm font-semibold text-foreground">{theme === "dark" ? "Dark mode" : "Light mode"}</div>
              <div className="text-xs text-muted-foreground">Click to switch theme</div>
            </div>
          </div>
          <span className="text-xs font-medium text-primary">Toggle</span>
        </button>
      </Card>

      <Card title="Notifications" desc="Choose what alerts you receive.">
        <Toggle icon={Bell} label="Real-time anomaly alerts" desc="Notify me about power spikes and outages." checked={alerts} onChange={setAlerts} />
        <Toggle icon={Wifi} label="Weekly email digest" desc="Summary of energy use and savings every Monday." checked={emailDigest} onChange={setEmailDigest} />
      </Card>

      <Card title="Connected devices" desc="ESP32 endpoints currently streaming.">
        <ul className="divide-y divide-border">
          {[
            { id: "esp32-001", loc: "Main feeder", status: "Online" },
            { id: "esp32-014", loc: "HVAC sub-meter", status: "Online" },
            { id: "esp32-027", loc: "Lighting circuit", status: "Online" },
          ].map((d) => (
            <li key={d.id} className="flex items-center justify-between py-3">
              <div>
                <div className="text-sm font-semibold text-foreground">{d.loc}</div>
                <div className="text-xs text-muted-foreground">{d.id}</div>
              </div>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-success/15 px-2.5 py-1 text-xs font-medium text-success">
                <span className="h-1.5 w-1.5 rounded-full bg-success" /> {d.status}
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function Card({ title, desc, children }: { title: string; desc: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-card-soft">
      <h2 className="text-base font-semibold text-foreground">{title}</h2>
      <p className="text-xs text-muted-foreground">{desc}</p>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (v: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</span>
      <input
        type={type} value={value} onChange={(e) => onChange(e.target.value)}
        className="mt-1.5 w-full rounded-xl border border-border bg-background px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
      />
    </label>
  );
}

function Toggle({
  icon: Icon, label, desc, checked, onChange,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string; desc: string;
  checked: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border py-4 last:border-0">
      <div className="flex items-start gap-3">
        <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-4 w-4" />
        </span>
        <div>
          <div className="text-sm font-semibold text-foreground">{label}</div>
          <div className="text-xs text-muted-foreground">{desc}</div>
        </div>
      </div>
      <button
        onClick={() => onChange(!checked)}
        aria-pressed={checked}
        className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${checked ? "bg-primary" : "bg-muted"}`}
      >
        <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? "translate-x-5" : "translate-x-0.5"}`} />
      </button>
    </div>
  );
}