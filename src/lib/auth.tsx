import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";

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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  const fetchUser = async () => {
    try {
      const data = await api.get("/auth/me");
      setUser(data);
    } catch (e) {
      setUser(null);
      localStorage.removeItem(TOKEN_KEY);
    }
  };

  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        await fetchUser();
      }
      setReady(true);
    };
    init();
  }, []);

  return (
    <Ctx.Provider
      value={{
        user,
        ready,
        login: async (email, password) => {
          const formData = new URLSearchParams();
          formData.append("username", email);
          formData.append("password", password);
          
          const data = await api.post("/auth/login", formData, true);
          localStorage.setItem(TOKEN_KEY, data.access_token);
          await fetchUser();
        },
        signup: async (name, email, password) => {
          // Fallback mock since signup endpoint isn't implemented on backend yet
          await new Promise((r) => setTimeout(r, 500));
          console.warn("Signup is mocked. Use seed data to login.");
        },
        logout: () => {
          localStorage.removeItem(TOKEN_KEY);
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