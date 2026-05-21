import { Link } from "@tanstack/react-router";
import { Zap } from "lucide-react";
import { ThemeToggle } from "@/lib/theme";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50">
      <div className="mx-auto mt-4 max-w-7xl px-4">
        <nav className="glass flex items-center justify-between rounded-2xl px-4 py-3 shadow-card-soft">
          <Link to="/" className="flex items-center gap-2">
            <span className="relative grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary text-primary-foreground shadow-glow">
              <Zap className="h-4 w-4" strokeWidth={2.5} />
            </span>
            <span className="text-lg font-semibold tracking-tight text-foreground">
              Amp<span className="text-primary">Aware</span>
            </span>
          </Link>
          <ul className="hidden items-center gap-8 text-sm font-medium text-muted-foreground md:flex">
            <li><a href="#platform" className="transition-colors hover:text-foreground">Platform</a></li>
            <li><a href="#monitoring" className="transition-colors hover:text-foreground">Monitoring</a></li>
            <li><a href="#billing" className="transition-colors hover:text-foreground">Billing</a></li>
            <li><a href="#security" className="transition-colors hover:text-foreground">Security</a></li>
          </ul>
          <div className="flex items-center gap-2">
            <ThemeToggle className="hidden sm:inline-flex" />
            <Link to="/login" className="hidden rounded-lg px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted sm:inline-flex">
              Sign in
            </Link>
            <Link to="/signup" className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-elegant transition-transform hover:-translate-y-0.5">
              Get started
            </Link>
          </div>
        </nav>
      </div>
    </header>
  );
}