import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { Zap, Mail, Lock, ArrowRight, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { AuthShell, AuthField } from "@/components/auth/AuthLayout";

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
    } catch (err: any) {
      setError(err.message || "Could not sign in. Please check your credentials.");
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