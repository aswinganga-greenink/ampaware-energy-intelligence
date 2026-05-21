import { Link } from "@tanstack/react-router";
import { Zap } from "lucide-react";

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="absolute inset-0 -z-10 bg-gradient-hero opacity-95" />
      <div className="absolute inset-0 -z-10 grid-pattern opacity-30" />
      <div className="absolute -left-40 top-20 -z-10 h-96 w-96 rounded-full bg-primary/30 blur-3xl" />
      <div className="absolute -right-32 bottom-0 -z-10 h-96 w-96 rounded-full bg-success/20 blur-3xl" />

      <div className="mx-auto flex min-h-screen max-w-md flex-col px-6 py-10">
        <Link to="/" className="flex items-center gap-2 self-start">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary text-primary-foreground shadow-glow">
            <Zap className="h-4 w-4" strokeWidth={2.5} />
          </span>
          <span className="text-lg font-semibold tracking-tight text-foreground">
            Amp<span className="text-primary-glow">Aware</span>
          </span>
        </Link>
        <div className="my-auto">
          <div className="rounded-3xl border border-border bg-card/50 p-8 shadow-elegant backdrop-blur-xl">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
            <div className="mt-6">{children}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function AuthField({
  icon: Icon, label, type, value, onChange, placeholder, required,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</span>
      <div className="mt-1.5 flex items-center gap-2 rounded-xl border border-border bg-muted/50 px-3 py-2.5 focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/30">
        <Icon className="h-4 w-4 text-muted-foreground" />
        <input
          required={required}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-transparent text-sm text-foreground placeholder:text-foreground/30 focus:outline-none"
        />
      </div>
    </label>
  );
}
