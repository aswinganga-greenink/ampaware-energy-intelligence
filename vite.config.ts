// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - tanstackStart, viteReact, tailwindcss, tsConfigPaths, cloudflare (build-only),
//     componentTagger (dev-only), VITE_* env injection, @ path alias, React/TanStack dedupe,
//     error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... } }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

// For Vercel deployment: disable @cloudflare/vite-plugin (Cloudflare Workers incompatible
// with Vercel) and prerender all known routes so Vercel can serve static HTML directly.
// Client-side TanStack Router takes over navigation after the initial page load.
export default defineConfig({
  // Disable the Cloudflare Workers bundler — it produces an output format Vercel cannot run.
  cloudflare: false,
  tanstackStart: {
    server: { entry: "server" },
    prerender: {
      enabled: true,
      routes: ["/", "/login", "/signup", "/dashboard", "/dashboard/billing", "/dashboard/settings"],
      crawlLinks: false,
    },
  },
});
