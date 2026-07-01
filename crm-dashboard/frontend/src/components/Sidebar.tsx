"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import useSWR from "swr";
import { useAuth } from "@/lib/auth";
import { fetcher } from "@/lib/api";
import {
  IconDashboard, IconUsers, IconRisk, IconAgency, IconSplit,
  IconAdmins, IconLogs, IconSettings, IconLogout, IconCrown, IconInbox, IconGlobe, IconGraduation, IconChart,
} from "./icons";
import { Avatar } from "./ui";
import type { Paged, Host } from "@/lib/types";

const SECTIONS: { title: string; items: { href: string; label: string; icon: typeof IconDashboard; badge?: string; manage?: boolean; perm?: "traffic" }[] }[] = [
  {
    title: "Сайт-визитка",
    items: [
      { href: "/applications", label: "Заявки", icon: IconInbox, badge: "applications", manage: true },
      { href: "/site", label: "Мой сайт", icon: IconGlobe, manage: true },
      { href: "/training-progress", label: "Прогресс обучения", icon: IconGraduation, manage: true },
      { href: "/traffic", label: "Статистика сайта", icon: IconChart, perm: "traffic" },
    ],
  },
  {
    title: "Halo CRM",
    items: [
      { href: "/dashboard", label: "Дашборд", icon: IconDashboard },
      { href: "/users", label: "Пользователи", icon: IconUsers },
      { href: "/risk", label: "Зона риска", icon: IconRisk, badge: "risk" },
      { href: "/agencies", label: "Агентства", icon: IconAgency },
      { href: "/split", label: "Split", icon: IconSplit },
    ],
  },
  {
    title: "Администрирование",
    items: [
      { href: "/admins", label: "Администраторы", icon: IconAdmins, manage: true },
      { href: "/logs", label: "Журнал изменений", icon: IconLogs, manage: true },
      { href: "/settings", label: "Настройки", icon: IconSettings, manage: true },
    ],
  },
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { me, logout } = useAuth();
  const { data: risk } = useSWR<Paged<Host>>("/risk?status=all&limit=1", fetcher, { refreshInterval: 60000 });
  const { data: appsCount } = useSWR<{ count: number }>("/applications/new-count", fetcher, { refreshInterval: 30000 });

  return (
    <aside className="w-[260px] shrink-0 h-[100dvh] sticky top-0 flex flex-col bg-bg-sidebar/80 backdrop-blur-xl border-r border-line">
      <div className="px-6 py-6 flex items-center gap-3">
        <div className="w-10 h-10 grid place-items-center text-brand-400 drop-shadow-[0_0_10px_rgba(139,92,246,0.55)]">
          <IconCrown className="w-9 h-9" />
        </div>
        <div className="leading-tight">
          <span className="block text-xl font-extrabold tracking-tight">Tos Agency</span>
          <span className="block text-[11px] text-slate-500 font-medium">CRM Dashboard</span>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-4 overflow-y-auto pb-4">
        {SECTIONS.map((section) => {
          const items = section.items.filter((item) =>
            !(item.manage && !me?.can_manage_users) && !(item.perm === "traffic" && !me?.can_view_traffic)
          );
          if (items.length === 0) return null;
          return (
            <div key={section.title} className="space-y-1">
              <div className="px-3 pt-1 pb-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-600">{section.title}</div>
              {items.map((item) => {
                const active = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link key={item.href} href={item.href} onClick={onNavigate}
                        className={`nav-link ${active ? "nav-link-active" : ""}`}>
                    {active && <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-full bg-brand-500" />}
                    <Icon className="w-5 h-5" />
                    <span className="flex-1">{item.label}</span>
                    {item.badge === "risk" && (risk?.total ?? 0) > 0 && (
                      <span className="chip bg-rose-500/20 text-rose-300 px-1.5 py-0.5 text-[11px]">{risk!.total}</span>
                    )}
                    {item.badge === "applications" && (appsCount?.count ?? 0) > 0 && (
                      <span className="chip bg-brand-500/25 text-brand-200 px-1.5 py-0.5 text-[11px]">{appsCount!.count}</span>
                    )}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>

      <div className="p-3 border-t border-line">
        <div className="flex items-center gap-3 px-2 py-2">
          <Avatar name={me?.name || me?.username} size={36} />
          <div className="min-w-0 flex-1">
            <div className="text-sm font-semibold truncate">{me?.name || me?.username}</div>
            <div className="text-[11px] text-slate-500">{me?.is_superadmin ? "Главный админ" : "Администратор"}</div>
          </div>
        </div>
        <button onClick={logout} className="nav-link w-full mt-1 text-slate-400 hover:text-rose-300">
          <IconLogout className="w-5 h-5" /> Выйти
        </button>
      </div>
    </aside>
  );
}
