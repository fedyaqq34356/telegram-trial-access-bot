"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, clearTokens, getAccess, setTokens } from "./api";
import type { Me } from "./types";

interface AuthCtx {
  me: Me | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
}

const Ctx = createContext<AuthCtx>(null as any);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  async function refreshMe() {
    try {
      const data = await api.get<Me>("/auth/me");
      setMe(data);
    } catch {
      setMe(null);
    }
  }

  useEffect(() => {
    (async () => {
      if (getAccess()) await refreshMe();
      setLoading(false);
    })();
  }, []);

  async function login(username: string, password: string) {
    const data = await api.post<{ access_token: string; refresh_token: string }>("/auth/login", {
      username,
      password,
    });
    setTokens(data.access_token, data.refresh_token);
    await refreshMe();
    router.push("/dashboard");
  }

  function logout() {
    api.post("/auth/logout").catch(() => {});
    clearTokens();
    setMe(null);
    router.push("/login");
  }

  return <Ctx.Provider value={{ me, loading, login, logout, refreshMe }}>{children}</Ctx.Provider>;
}

export const useAuth = () => useContext(Ctx);
