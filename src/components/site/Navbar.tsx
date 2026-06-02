import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Zap, Menu, X } from "lucide-react";
import { ThemeToggle } from "@/lib/theme";

export function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50">
      <div className="mx-auto mt-4 max-w-7xl px-4">
        <nav className="glass rounded-2xl shadow-card-soft">
          {/* Top bar */}
          <div className="flex items-center justify-between px-4 py-3">
            <Link to="/" className="flex items-center gap-2" onClick={() => setOpen(false)}>
              <span className="relative grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary text-primary-foreground shadow-glow">
                <Zap className="h-4 w-4" strokeWidth={2.5} />
              </span>
              <span className="text-lg font-semibold tracking-tight text-foreground">
                Amp<span className="text-primary">Aware</span>
              </span>
            </Link>

            {/* Desktop nav links */}
            <ul className="hidden items-center gap-8 text-sm font-medium text-muted-foreground md:flex">
              <li><a href="#platform" className="transition-colors hover:text-foreground">Platform</a></li>
              <li><a href="#monitoring" className="transition-colors hover:text-foreground">Monitoring</a></li>
              <li><a href="#billing" className="transition-colors hover:text-foreground">Billing</a></li>
              <li><a href="#security" className="transition-colors hover:text-foreground">Security</a></li>
            </ul>

            {/* Desktop CTA + mobile hamburger */}
            <div className="flex items-center gap-2">
              <ThemeToggle className="hidden sm:inline-flex" />
              <Link
                to="/login"
                className="hidden rounded-lg px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted sm:inline-flex"
              >
                Sign in
              </Link>
              <Link
                to="/signup"
                className="hidden items-center gap-1.5 rounded-lg bg-gradient-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-elegant transition-transform hover:-translate-y-0.5 sm:inline-flex"
              >
                Get started
              </Link>

              {/* Burger — visible only on mobile */}
              <button
                id="mobile-menu-toggle"
                aria-label={open ? "Close menu" : "Open menu"}
                aria-expanded={open}
                onClick={() => setOpen((v) => !v)}
                className="relative inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-foreground transition-colors hover:bg-muted sm:hidden"
              >
                <span
                  className="absolute transition-all duration-200"
                  style={{ opacity: open ? 0 : 1, transform: open ? "rotate(90deg) scale(0.5)" : "rotate(0deg) scale(1)" }}
                >
                  <Menu className="h-5 w-5" />
                </span>
                <span
                  className="absolute transition-all duration-200"
                  style={{ opacity: open ? 1 : 0, transform: open ? "rotate(0deg) scale(1)" : "rotate(-90deg) scale(0.5)" }}
                >
                  <X className="h-5 w-5" />
                </span>
              </button>
            </div>
          </div>

          {/* Mobile drawer */}
          <div
            id="mobile-menu"
            className="overflow-hidden transition-all duration-300 ease-in-out sm:hidden"
            style={{ maxHeight: open ? "400px" : "0px", opacity: open ? 1 : 0 }}
          >
            <div className="border-t border-border px-4 pb-4 pt-3 flex flex-col gap-1">
              <a
                href="#platform"
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                Platform
              </a>
              <a
                href="#monitoring"
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                Monitoring
              </a>
              <a
                href="#billing"
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                Billing
              </a>
              <a
                href="#security"
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                Security
              </a>

              {/* Divider */}
              <div className="my-2 h-px bg-border" />

              {/* Auth + theme row */}
              <div className="flex items-center gap-2">
                <ThemeToggle />
                <Link
                  to="/login"
                  onClick={() => setOpen(false)}
                  className="flex-1 rounded-lg border border-border px-3 py-2.5 text-center text-sm font-medium text-foreground transition-colors hover:bg-muted"
                >
                  Sign in
                </Link>
                <Link
                  to="/signup"
                  onClick={() => setOpen(false)}
                  className="flex-1 inline-flex items-center justify-center rounded-lg bg-gradient-primary px-3 py-2.5 text-sm font-semibold text-primary-foreground shadow-elegant"
                >
                  Get started
                </Link>
              </div>
            </div>
          </div>
        </nav>
      </div>
    </header>
  );
}