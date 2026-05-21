import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type User = { name: string; email: string };
type AuthCtx = {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);
const KEY = "ampaware.auth.user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setUser(JSON.parse(raw));
    } catch {}
    setReady(true);
  }, []);

  const persist = (u: User | null) => {
    setUser(u);
    if (typeof window !== "undefined") {
      if (u) localStorage.setItem(KEY, JSON.stringify(u));
      else localStorage.removeItem(KEY);
    }
  };

  return (
    <Ctx.Provider
      value={{
        user,
        ready,
        login: async (email) => {
          await new Promise((r) => setTimeout(r, 400));
          persist({ name: email.split("@")[0] || "Operator", email });
        },
        signup: async (name, email) => {
          await new Promise((r) => setTimeout(r, 500));
          persist({ name, email });
        },
        logout: () => persist(null),
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