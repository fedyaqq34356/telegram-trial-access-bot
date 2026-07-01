"use client";
import { useState } from "react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PageHeader } from "@/components/PageHeader";
import { StatsCard } from "@/components/StatsCard";
import { Spinner } from "@/components/ui";
import { IconChart, IconUsers, IconInbox, IconGlobe, IconRefresh } from "@/components/icons";
import { nf } from "@/lib/format";
import type { TrafficStats, TrafficKV } from "@/lib/types";

const RANGES = [
  { days: 7, label: "7 дней" },
  { days: 30, label: "30 дней" },
  { days: 90, label: "90 дней" },
];

const PAGE_LABELS: Record<string, string> = {
  "/": "Главная",
  "/apply": "Заявка",
  "/about": "О нас",
  "/benefits": "Преимущества",
  "/reviews": "Отзывы",
  "/faq": "FAQ",
  "/contacts": "Контакты",
  "/instruction": "Инструкция",
  "/download": "Скачать приложение",
  "/training": "Обучение",
  "/start": "Старт",
};

const DEVICE_LABELS: Record<string, string> = {
  mobile: "Смартфоны", desktop: "Компьютеры", tablet: "Планшеты", unknown: "Неизвестно",
};

export default function TrafficPage() {
  const { me } = useAuth();
  const [days, setDays] = useState(30);
  const { data, isLoading, mutate } = useSWR<TrafficStats>(`/traffic/stats?days=${days}`, fetcher, {
    refreshInterval: 120000,
  });

  if (!me?.can_view_traffic) {
    return <div className="card text-slate-400">Нет доступа к статистике сайта.</div>;
  }

  const t = data?.totals;
  const delta = t?.visits_delta_percent;

  return (
    <>
      <PageHeader title="Статистика сайта" showRefresh={false}>
        <div className="flex items-center gap-1 rounded-xl bg-white/[0.03] border border-line p-1">
          {RANGES.map((r) => (
            <button key={r.days} onClick={() => setDays(r.days)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${days === r.days ? "bg-brand-500/25 text-brand-200" : "text-slate-400 hover:text-slate-200"}`}>
              {r.label}
            </button>
          ))}
        </div>
        <button onClick={() => mutate()} className="btn-primary"><IconRefresh className="w-4 h-4" /> Обновить данные</button>
      </PageHeader>

      {isLoading && !data ? (
        <div className="card grid place-items-center py-16"><Spinner className="w-6 h-6" /></div>
      ) : !data ? (
        <div className="card text-slate-400">Не удалось загрузить статистику.</div>
      ) : (
        <div className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatsCard title="Посещений" value={nf(t!.visits)} icon={<IconChart className="w-5 h-5" />} tone="purple"
              sub={delta === null || delta === undefined ? `за ${days} дн.` : `${delta >= 0 ? "▲" : "▼"} ${Math.abs(delta)}% к пред. периоду`} />
            <StatsCard title="Уникальных посетителей" value={nf(t!.uniques)} icon={<IconUsers className="w-5 h-5" />} tone="blue" />
            <StatsCard title="Заявок с сайта" value={nf(t!.applications)} icon={<IconInbox className="w-5 h-5" />} tone="green" />
            <StatsCard title="Конверсия в заявку" value={`${t!.conversion_rate}%`} icon={<IconGlobe className="w-5 h-5" />} tone="orange"
              sub="визиты → заявки" />
          </div>

          <DailyChart daily={data.daily} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <BarList title="Источники трафика" items={data.sources} total={t!.visits} />
            <BarList title="Рекламные кампании" items={data.campaigns} total={t!.visits}
              empty="Нет данных по кампаниям. Добавьте UTM-метки к рекламным ссылкам (например ?utm_source=instagram&utm_campaign=june)." />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <BarList title="Популярные страницы" items={data.top_pages} total={t!.visits} labelMap={PAGE_LABELS} />
            <BarList title="Устройства" items={data.devices} total={t!.visits} labelMap={DEVICE_LABELS} />
          </div>

          <ConversionTable rows={data.conversion_by_source} />
        </div>
      )}
    </>
  );
}

function DailyChart({ daily }: { daily: { date: string; visits: number; uniques: number }[] }) {
  const max = Math.max(1, ...daily.map((d) => d.visits));
  return (
    <div className="card">
      <div className="text-sm font-semibold mb-4">Посещения по дням</div>
      <div className="flex items-end gap-[3px] h-40">
        {daily.map((d) => {
          const h = Math.round((d.visits / max) * 100);
          const uh = Math.round((d.uniques / max) * 100);
          const label = new Date(d.date + "T00:00:00").toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
          return (
            <div key={d.date} className="flex-1 min-w-0 h-full flex flex-col justify-end group relative">
              <div className="relative w-full rounded-t bg-brand-500/25" style={{ height: `${h}%` }}>
                <div className="absolute bottom-0 left-0 right-0 rounded-t bg-brand-500" style={{ height: `${d.visits ? (uh / h) * 100 : 0}%` }} />
              </div>
              <div className="pointer-events-none absolute -top-1 left-1/2 -translate-x-1/2 -translate-y-full opacity-0 group-hover:opacity-100 transition bg-bg-sidebar border border-line rounded-lg px-2 py-1 text-[11px] whitespace-nowrap z-10">
                <div className="font-semibold">{label}</div>
                <div className="text-brand-300">{d.visits} посещ.</div>
                <div className="text-slate-400">{d.uniques} уник.</div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex items-center gap-4 mt-3 text-[11px] text-slate-500">
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-brand-500" /> Уникальные</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-brand-500/25" /> Все посещения</span>
      </div>
    </div>
  );
}

function BarList({ title, items, total, labelMap, empty }: {
  title: string; items: TrafficKV[]; total: number; labelMap?: Record<string, string>; empty?: string;
}) {
  const max = Math.max(1, ...items.map((i) => i.count));
  return (
    <div className="card">
      <div className="text-sm font-semibold mb-4">{title}</div>
      {items.length === 0 ? (
        <div className="text-xs text-slate-500">{empty || "Нет данных"}</div>
      ) : (
        <div className="space-y-2.5">
          {items.map((i) => {
            const label = (labelMap && labelMap[i.key]) || i.key || "—";
            const share = total ? Math.round((i.count / total) * 100) : 0;
            return (
              <div key={i.key || "_"}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-slate-300 truncate mr-2" title={label}>{label}</span>
                  <span className="text-slate-500 shrink-0">{nf(i.count)} · {share}%</span>
                </div>
                <div className="h-2 rounded-full bg-white/[0.04] overflow-hidden">
                  <div className="h-full rounded-full bg-brand-500/70" style={{ width: `${Math.round((i.count / max) * 100)}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ConversionTable({ rows }: { rows: { source: string; visits: number; applications: number; rate: number }[] }) {
  return (
    <div className="card !p-0 overflow-hidden overflow-x-auto">
      <div className="px-5 pt-4 pb-2 text-sm font-semibold">Конверсия по источникам</div>
      <table className="w-full min-w-[520px]">
        <thead><tr className="border-b border-line">
          <th className="th">Источник</th><th className="th text-right">Посещений</th>
          <th className="th text-right">Заявок</th><th className="th text-right">Конверсия</th>
        </tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.source} className="border-b border-line/60 hover:bg-white/[0.02]">
              <td className="td font-medium">{r.source}</td>
              <td className="td text-right text-slate-400">{nf(r.visits)}</td>
              <td className="td text-right text-slate-400">{nf(r.applications)}</td>
              <td className="td text-right">
                <span className={`chip ${r.rate >= 3 ? "bg-emerald-500/15 text-emerald-300" : r.rate > 0 ? "bg-brand-500/15 text-brand-200" : "bg-slate-500/15 text-slate-400"}`}>{r.rate}%</span>
              </td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td className="td text-slate-500 text-center" colSpan={4}>Нет данных</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
