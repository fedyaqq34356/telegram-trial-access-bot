"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import useSWR from "swr";
import { useAuth } from "@/lib/auth";
import { AgencyProvider } from "@/lib/agency";
import { fetcher } from "@/lib/api";
import { Sidebar } from "@/components/Sidebar";
import { AgencySelect } from "@/components/AgencySelect";
import { Spinner } from "@/components/ui";
import { IconBell, IconCrown, IconMenu, IconRisk } from "@/components/icons";
import type { Paged, Host } from "@/lib/types";

const SEEN_KEY = "notif_seen_ids";
function loadSeen(): Set<number> {
  if (typeof window === "undefined") return new Set();
  try { return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || "[]")); }
  catch { return new Set(); }
}

function NotificationsBell() {
  const [open, setOpen] = useState(false);
  const [seen, setSeen] = useState<Set<number>>(() => new Set());
  const ref = useRef<HTMLDivElement>(null);
  const { data: risk } = useSWR<Paged<Host>>("/risk?status=danger&limit=30", fetcher, { refreshInterval: 60000 });

  useEffect(() => { setSeen(loadSeen()); }, []);

  const items = risk?.items ?? [];
  const unread = items.filter((h) => !seen.has(h.id)).length;

  function markAllSeen() {
    const next = new Set(seen);
    items.forEach((h) => next.add(h.id));
    setSeen(next);
    if (typeof window !== "undefined") localStorage.setItem(SEEN_KEY, JSON.stringify([...next]));
  }

  function toggle() {
    const willOpen = !open;
    setOpen(willOpen);
    if (willOpen) markAllSeen(); // открыли колокольчик — помечаем прочитанными
  }

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button className="btn-ghost px-2.5 py-2.5 relative" onClick={toggle}>
        <IconBell className="w-4 h-4" />
        {unread > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold grid place-items-center">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-[300px] max-w-[calc(100vw-2rem)] popover rounded-2xl border border-line shadow-2xl z-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-line flex items-center justify-between">
            <span className="font-semibold text-sm">Уведомления</span>
            <span className="text-[11px] text-slate-500">{items.length} в зоне риска</span>
          </div>
          <div className="max-h-[320px] overflow-y-auto">
            {items.length === 0 ? (
              <div className="px-4 py-6 text-center text-sm text-slate-500">Нет новых уведомлений</div>
            ) : (
              items.map((h) => (
                <Link key={h.id} href="/risk" onClick={() => setOpen(false)}
                      className="flex items-start gap-3 px-4 py-3 hover:bg-white/[0.03] border-b border-line/50">
                  <span className="mt-0.5 text-rose-400"><IconRisk className="w-4 h-4" /></span>
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{h.nickname || h.display_account_id}</div>
                    <div className="text-[11px] text-slate-500">{h.agency_name} · коэфф. {h.real_down_rate}</div>
                  </div>
                </Link>
              ))
            )}
          </div>
          <Link href="/risk" onClick={() => setOpen(false)}
                className="block px-4 py-3 text-center text-sm text-brand-300 hover:bg-white/[0.03] border-t border-line">
            Открыть зону риска
          </Link>
        </div>
      )}
    </div>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  const router = useRouter();
  const [mobileNav, setMobileNav] = useState(false);

  useEffect(() => {
    if (!loading && !me) router.replace("/login");
  }, [me, loading, router]);

  if (loading || !me) {
    return <div className="h-screen grid place-items-center text-brand-300"><Spinner className="w-8 h-8" /></div>;
  }

  return (
    <AgencyProvider>
      <div className="flex min-h-screen">
        <div className="hidden lg:block"><Sidebar /></div>

        {mobileNav && (
          <div className="fixed inset-0 z-40 lg:hidden">
            <div className="absolute inset-0 bg-black/60" onClick={() => setMobileNav(false)} />
            <div className="absolute left-0 top-0"><Sidebar onNavigate={() => setMobileNav(false)} /></div>
          </div>
        )}

        <div className="flex-1 min-w-0 flex flex-col">
          <header className="sticky top-0 z-20 flex items-center gap-3 px-4 lg:px-8 py-3.5 border-b border-line bg-bg/70 backdrop-blur-xl">
            <button className="lg:hidden flex items-center gap-2 rounded-xl border border-brand-500/40 bg-brand-500/5 px-3 py-2"
                    onClick={() => setMobileNav(true)} aria-label="Меню">
              <IconCrown className="w-5 h-5 text-brand-400" />
              <IconMenu className="w-5 h-5 text-slate-200" />
            </button>
            <div className="glass px-3 py-1.5 text-xs text-slate-400 hidden sm:block">
              20 coins = 1 USD · <span className="text-slate-300">1 coin = $0.05</span>
            </div>
            <div className="ml-auto flex items-center gap-3">
              <AgencySelect />
              <NotificationsBell />
            </div>
          </header>

          <main className="flex-1 p-4 lg:p-8">{children}</main>
        </div>
      </div>
    </AgencyProvider>
  );
}
