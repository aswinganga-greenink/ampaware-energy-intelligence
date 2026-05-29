import { createFileRoute, Link, Outlet, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect } from "react";
import { Zap, LayoutDashboard, Receipt, Settings, LogOut, Search } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { ThemeToggle } from "@/lib/theme";
import { AlertsDropdown } from "@/components/dashboard/AlertsDropdown";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — AmpAware" },
      { name: "description", content: "Real-time energy monitoring dashboard." },
    ],
  }),
  component: DashboardLayout,
});

const NAV = [
  { to: "/dashboard", label: "Overview", icon: LayoutDashboard, exact: true },
  { to: "/dashboard/billing", label: "KSEB Billing", icon: Receipt, exact: false },
  { to: "/dashboard/settings", label: "Settings", icon: Settings, exact: false },
] as const;

function DashboardLayout() {
  const { user, ready, logout } = useAuth();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  useEffect(() => {
    if (ready && !user) navigate({ to: "/login" });
  }, [ready, user, navigate]);

  if (!ready || !user) {
    return (
      <div className="grid min-h-screen place-items-center bg-background text-muted-foreground">
        Loading workspace…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/40">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-border bg-card md:flex">
        <div className="flex h-16 items-center gap-2 px-5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary text-primary-foreground shadow-glow">
            <Zap className="h-4 w-4" strokeWidth={2.5} />
          </span>
          <span className="text-lg font-semibold tracking-tight text-foreground">
            Amp<span className="text-primary">Aware</span>
          </span>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV.map((n) => {
            const active = n.exact ? pathname === n.to : pathname.startsWith(n.to);
            return (
              <Link
                key={n.to}
                to={n.to}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-gradient-primary text-primary-foreground shadow-elegant"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                <n.icon className="h-4 w-4" />
                {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-border p-3">
          <div className="flex items-center gap-3 rounded-xl p-2">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-primary text-sm font-semibold text-primary-foreground">
              {user.full_name ? user.full_name.slice(0, 1).toUpperCase() : "A"}
            </span>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-foreground">{user.full_name}</div>
              <div className="truncate text-xs text-muted-foreground">{user.email}</div>
            </div>
            <button
              onClick={() => { logout(); navigate({ to: "/" }); }}
              className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground"
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <div className="md:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur md:px-8">
          <div className="hidden flex-1 items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 md:flex md:max-w-md">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input
              placeholder="Search devices, feeders, alerts…"
              className="w-full bg-transparent text-sm focus:outline-none"
            />
          </div>
          <div className="ml-auto flex items-center gap-2">
            <ThemeToggle />
            <AlertsDropdown />
          </div>
        </header>
        <main className="px-4 py-8 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}