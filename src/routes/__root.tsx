import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";

import appCss from "../styles.css?url";
import { AuthProvider } from "@/lib/auth";
import { ThemeProvider } from "@/lib/theme";
import { Preloader } from "@/components/site/Preloader";
import { useEffect } from "react";

import { ZapOff, Home, AlertTriangle, RotateCcw } from "lucide-react";

function NotFoundComponent() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4">
      {/* Animated Backgrounds */}
      <div className="absolute inset-0 -z-10 bg-gradient-hero opacity-80" />
      <div className="absolute inset-0 -z-10 grid-pattern opacity-30" />
      <div className="absolute top-1/4 -left-32 -z-10 h-96 w-96 rounded-full bg-primary/20 blur-[100px] animate-pulse" />
      <div className="absolute bottom-1/4 -right-32 -z-10 h-96 w-96 rounded-full bg-destructive/10 blur-[100px] animate-pulse" />
      
      <div className="relative z-10 flex flex-col items-center max-w-2xl text-center glass rounded-3xl p-12 shadow-elegant animate-fade-up">
        {/* Animated Icon */}
        <div className="relative mb-8">
          <div className="absolute inset-0 blur-2xl bg-destructive/30 rounded-full animate-pulse-ring" />
          <div className="relative flex h-24 w-24 items-center justify-center rounded-full bg-card shadow-card-soft border border-border">
            <ZapOff className="h-10 w-10 text-destructive animate-float" />
          </div>
        </div>

        {/* Text Content */}
        <h1 className="text-8xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-foreground to-muted-foreground">
          404
        </h1>
        <h2 className="mt-4 text-2xl font-semibold tracking-tight text-foreground">
          Grid Disconnected
        </h2>
        <p className="mt-4 text-muted-foreground max-w-md mx-auto leading-relaxed">
          We couldn't find the power source you're looking for. The node might be offline, moved, or completely disconnected from the network.
        </p>

        {/* Actions */}
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <Link
            to="/"
            className="group relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-full bg-primary px-8 py-3 text-sm font-semibold text-primary-foreground shadow-glow transition-all hover:scale-105 hover:bg-primary/90"
          >
            <span className="absolute inset-0 shimmer opacity-20" />
            <Home className="h-4 w-4" />
            Reconnect to Grid
          </Link>
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center justify-center gap-2 rounded-full border border-border bg-card px-8 py-3 text-sm font-semibold text-foreground shadow-sm transition-all hover:bg-muted"
          >
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4">
      {/* Animated Backgrounds */}
      <div className="absolute inset-0 -z-10 bg-gradient-hero opacity-80" />
      <div className="absolute inset-0 -z-10 grid-pattern opacity-30" />
      <div className="absolute top-1/4 -left-32 -z-10 h-96 w-96 rounded-full bg-destructive/20 blur-[100px] animate-pulse" />
      <div className="absolute bottom-1/4 -right-32 -z-10 h-96 w-96 rounded-full bg-accent/20 blur-[100px] animate-pulse" />

      <div className="relative z-10 flex flex-col items-center max-w-2xl text-center glass rounded-3xl p-12 shadow-elegant animate-fade-up">
        {/* Animated Icon */}
        <div className="relative mb-8">
          <div className="absolute inset-0 blur-2xl bg-destructive/30 rounded-full animate-pulse-ring" />
          <div className="relative flex h-24 w-24 items-center justify-center rounded-full bg-card shadow-card-soft border border-border">
            <AlertTriangle className="h-10 w-10 text-destructive animate-float" />
          </div>
        </div>

        <h1 className="text-4xl font-bold tracking-tight text-foreground">
          System Fault Detected
        </h1>
        <p className="mt-4 text-muted-foreground max-w-md mx-auto leading-relaxed">
          A critical exception occurred in the UI circuit. Our systems have logged the anomaly. You can attempt to reset the connection.
        </p>

        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="group relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-full bg-destructive px-8 py-3 text-sm font-semibold text-destructive-foreground shadow-glow transition-all hover:scale-105 hover:bg-destructive/90"
          >
            <span className="absolute inset-0 shimmer opacity-20" />
            <RotateCcw className="h-4 w-4" />
            Reset Circuit
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center gap-2 rounded-full border border-border bg-card px-8 py-3 text-sm font-semibold text-foreground shadow-sm transition-all hover:bg-muted"
          >
            <Home className="h-4 w-4" />
            Return Home
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "AmpAware — Smart Energy Intelligence Platform" },
      { name: "description", content: "Real-time smart energy monitoring, KSEB billing intelligence and AI insights for homes and industries. Engineered with ESP32-grade precision." },
      { name: "author", content: "AmpAware" },
      { property: "og:title", content: "AmpAware — Smart Energy Intelligence Platform" },
      { property: "og:description", content: "Live energy monitoring, billing forecasts and savings insights — built for the modern grid." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "twitter:site", content: "@Lovable" },
    ],
    links: [
      {
        rel: "stylesheet",
        href: appCss,
      },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap",
      },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <Preloader />
          <Outlet />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
