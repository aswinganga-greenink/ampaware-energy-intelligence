import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type User = { id: string; name: string; email: string; full_name: string; role: string };
type AuthCtx = {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);
const TOKEN_KEY = "ampaware.auth.token";
const USER_KEY = "ampaware.auth.user";

// ── Static mock auth ────────────────────────────────────────────────────────
// Backend is not reachable in this deployment. All auth is handled locally.
// Replace these functions with real API calls once the backend is live.
// Demo credentials: demo@ampaware.com / demo1234
// ────────────────────────────────────────────────────────────────────────────

function makeUser(name: string, email: string): User {
  return {
    id: btoa(email).slice(0, 12),
    name,
    email,
    full_name: name,
    role: "customer",
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  // Restore session from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    const stored = localStorage.getItem(USER_KEY);
    if (token && stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      }
    }
    setReady(true);
  }, []);

  function persistSession(u: User) {
    localStorage.setItem(TOKEN_KEY, "static-mock-token-" + u.id);
    localStorage.setItem(USER_KEY, JSON.stringify(u));
    setUser(u);
  }

  return (
    <Ctx.Provider
      value={{
        user,
        ready,
        login: async (email, password) => {
          // Simulate a brief network delay for realistic UX
          await new Promise((r) => setTimeout(r, 600));

          if (!email || !password) throw new Error("Email and password are required.");
          if (password.length < 4) throw new Error("Password must be at least 4 characters.");

          // Accept any valid-looking credentials; use email as display name
          const displayName =
            email === "demo@ampaware.com"
              ? "Demo User"
              : email.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

          persistSession(makeUser(displayName, email));
        },
        signup: async (name, email, password) => {
          await new Promise((r) => setTimeout(r, 600));
          if (!name || !email || !password) throw new Error("All fields are required.");
          if (password.length < 6) throw new Error("Password must be at least 6 characters.");
          persistSession(makeUser(name, email));
        },
        logout: () => {
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(USER_KEY);
          setUser(null);
        },
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used inside AuthProvider");
  return v;
}