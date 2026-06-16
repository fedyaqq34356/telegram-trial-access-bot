"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import { Spinner } from "@/components/ui";

export default function LoginPage() {
  const { login, me, loading } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && me) router.replace("/dashboard");
  }, [me, loading, router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка входа");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-700 grid place-items-center shadow-glow mb-4">
            <span className="text-white font-black text-2xl">V</span>
          </div>
          <h1 className="text-2xl font-extrabold">Tos Agency CRM</h1>
          <p className="text-sm text-slate-500 mt-1">Войдите в панель управления</p>
        </div>

        <form onSubmit={submit} className="card space-y-4">
          <div>
            <label className="label">Логин</label>
            <input className="input" value={username} onChange={(e) => setUsername(e.target.value)}
                   autoFocus placeholder="admin" />
          </div>
          <div>
            <label className="label">Пароль</label>
            <input className="input" type="password" value={password}
                   onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          {error && <div className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{error}</div>}
          <button type="submit" disabled={busy} className="btn-primary w-full">
            {busy ? <Spinner className="w-4 h-4" /> : null} Войти
          </button>
        </form>
      </div>
    </div>
  );
}
