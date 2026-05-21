import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { Zap, Mail, Lock, ArrowRight, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — AmpAware" },
      { name: "description", content: "Sign in to your AmpAware energy intelligence dashboard." },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate({ to: "/dashboard" });
    } catch (err) {
      setError("Could not sign in. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return <AuthShell title="Welcome back" subtitle="Sign in to your AmpAware workspace.">
    <form onSubmit={onSubmit} className="space-y-4">
      {error && <div className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>}
      <AuthField icon={Mail} label="Email" type="email" required value={email} onChange={setEmail} placeholder="you@company.com" />
      <AuthField icon={Lock} label="Password" type="password" required value={password} onChange={setPassword} placeholder="••••••••" />
      <button disabled={loading} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-elegant transition-transform hover:-translate-y-0.5 disabled:opacity-60">
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Sign in <ArrowRight className="h-4 w-4" /></>}
      </button>
    </form>
    <p className="mt-6 text-center text-sm text-muted-foreground">
      New to AmpAware? <Link to="/signup" className="font-semibold text-primary hover:underline">Create an account</Link>
    </p>
  </AuthShell>;
}

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
          <span className="text-lg font-semibold tracking-tight text-white">
            Amp<span className="text-primary-glow">Aware</span>
          </span>
        </Link>
        <div className="my-auto">
          <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8 shadow-elegant backdrop-blur-xl">
            <h1 className="text-2xl font-semibold tracking-tight text-white">{title}</h1>
            <p className="mt-1 text-sm text-white/60">{subtitle}</p>
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
      <span className="text-xs font-medium uppercase tracking-wider text-white/60">{label}</span>
      <div className="mt-1.5 flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2.5 focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/30">
        <Icon className="h-4 w-4 text-white/40" />
        <input
          required={required}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-transparent text-sm text-white placeholder:text-white/30 focus:outline-none"
        />
      </div>
    </label>
  );
}