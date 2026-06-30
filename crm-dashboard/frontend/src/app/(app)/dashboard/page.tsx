"use client";
import useSWR from "swr";
import { fetcher, qs } from "@/lib/api";
import { useAgencies } from "@/lib/agency";
import { PageHeader } from "@/components/PageHeader";
import { StatsCard } from "@/components/StatsCard";
import { StatusBadge, Spinner } from "@/components/ui";
import { IconCoins, IconWallet, IconOnline, IconRisk, IconSplit } from "@/components/icons";
import { coins, usd, nf, onlineLabel, dt, timeAgo } from "@/lib/format";

const GRADE_BAR: Record<string, string> = {
  S: "bg-brand-500", A: "bg-emerald-500", B: "bg-sky-500", C: "bg-orange-500", D: "bg-rose-500",
};

export default function DashboardPage() {
  const { selected, agencies } = useAgencies();
  
  const viewingAll = selected === null && agencies.length > 1;
  const agWord = viewingAll ? "агентств" : "агентства";
  const { data, isLoading } = useSWR<any>(`/dashboard/stats${qs({ agency_id: selected ?? undefined })}`, fetcher, {
    refreshInterval: 60000,
  });

  if (isLoading || !data) {
    return (<><PageHeader title="Дашборд" /><div className="grid place-items-center h-60 text-brand-300"><Spinner className="w-8 h-8" /></div></>);
  }

  const c = data.cards;
  return (
    <>
      <PageHeader title="Дашборд" />

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatsCard tone="purple" title="Заработок хостов за вчера" icon={<IconCoins className="w-5 h-5" />}
                   value={coins(c.yesterday_income_coins)} sub={usd(c.yesterday_income_usd)} />
        <StatsCard tone="blue" title="Заработок хостов за последние 30 дней" icon={<IconWallet className="w-5 h-5" />}
                   value={coins(c.month_income_coins)} sub={usd(c.month_income_usd)} />
        <StatsCard tone="purple" title={`Доход ${agWord} за вчера`} icon={<IconWallet className="w-5 h-5" />}
                   value={coins(c.yesterday_agency_income_coins)} sub={usd(c.yesterday_agency_income_usd)} />
        <StatsCard tone="blue" title={`Доход ${agWord} за последние 30 дней`} icon={<IconWallet className="w-5 h-5" />}
                   value={coins(c.month_agency_income_coins)} sub={usd(c.month_agency_income_usd)} />
        <StatsCard tone="green" title="Онлайн за вчера" icon={<IconOnline className="w-5 h-5" />}
                   value={nf(c.yesterday_online?.hours)} sub={onlineLabel(c.yesterday_online)} />
        <StatsCard tone="orange" title="Онлайн за последние 30 дней" icon={<IconOnline className="w-5 h-5" />}
                   value={nf(c.month_online?.hours)} sub={onlineLabel(c.month_online)} />
        <StatsCard tone="red" title="Пользователей в зоне риска" icon={<IconRisk className="w-5 h-5" />}
                   value={String(c.at_risk_count + c.warnings_count)} sub={`(${c.at_risk_percent}%)`} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-6">
        <div className="card xl:col-span-2">
          <h2 className="font-bold text-lg mb-4">Статистика по агентствам</h2>
          <div className="overflow-x-auto -mx-5">
            <table className="w-full min-w-[640px]">
              <thead><tr className="border-b border-line">
                <th className="th">Агентство</th><th className="th">Польз.</th>
                <th className="th">За вчера</th><th className="th">За 30 дней</th>
                <th className="th">Доход агент. (30 дн.)</th>
                <th className="th">Онлайн вчера</th><th className="th">В зоне риска</th>
              </tr></thead>
              <tbody>
                {data.per_agency.map((a: any) => (
                  <tr key={a.agency_id} className="border-b border-line/60">
                    <td className="td font-semibold">{a.agency_name}</td>
                    <td className="td">{a.users}</td>
                    <td className="td"><div className="leading-tight"><div>{coins(a.yesterday_income_coins)}</div><div className="text-[11px] text-slate-500">{usd(a.yesterday_income_usd)}</div></div></td>
                    <td className="td"><div className="leading-tight"><div>{coins(a.month_income_coins)}</div><div className="text-[11px] text-slate-500">{usd(a.month_income_usd)}</div></div></td>
                    <td className="td text-brand-200"><div className="leading-tight"><div>{coins(a.month_agency_income_coins)}</div><div className="text-[11px] text-slate-500">{usd(a.month_agency_income_usd)}</div></div></td>
                    <td className="td text-slate-400">{onlineLabel(a.yesterday_online)}</td>
                    <td className="td text-rose-300">{a.at_risk_count + a.warnings_count}</td>
                  </tr>
                ))}
                {data.per_agency.length === 0 && <tr><td colSpan={7} className="td text-center text-slate-500 py-8">Нет агентств</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h2 className="font-bold text-lg mb-4">Последний Split</h2>
          {data.last_split ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-brand-500/15 text-brand-300 grid place-items-center"><IconSplit /></div>
                <StatusBadge status={data.last_split.status} />
              </div>
              <Grid2 a="Область" b={data.last_split.scope_label} c="Дата" d={dt(data.last_split.date)} />
              <Grid2 a="Обработано" b={`${data.last_split.processed}`} c="Пропущено" d={`${data.last_split.skipped}`} />
              <Grid2 a="Ошибки" b={`${data.last_split.errors}`} c="Сумма" d={`${nf(data.last_split.total_amount_coins)} coins`} />
            </div>
          ) : <div className="text-slate-500 text-sm py-8 text-center">Split ещё не запускался</div>}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="card">
          <h2 className="font-bold text-lg mb-4">Последние действия</h2>
          <div className="space-y-3">
            {data.recent_actions.map((a: any) => (
              <div key={a.id} className="flex items-start gap-3 text-sm">
                <span className="w-2 h-2 rounded-full bg-brand-500 mt-1.5 shrink-0" />
                <div className="min-w-0">
                  <div className="truncate">{actionLabel(a)}</div>
                  <div className="text-[11px] text-slate-500">{a.username} · {timeAgo(a.created_at)}</div>
                </div>
              </div>
            ))}
            {data.recent_actions.length === 0 && <div className="text-slate-500 text-sm py-4">Нет действий</div>}
          </div>
        </div>

        <div className="card">
          <h2 className="font-bold text-lg mb-4">Последние операции Split</h2>
          <div className="space-y-3">
            {data.recent_splits.map((s: any) => (
              <div key={s.id} className="flex items-center justify-between text-sm">
                <div><div className="font-medium">{s.scope_label}</div><div className="text-[11px] text-slate-500">{dt(s.date)}</div></div>
                <div className="text-right"><div>{nf(s.total_amount_coins)} <span className="text-slate-500">coins</span></div><StatusBadge status={s.status} /></div>
              </div>
            ))}
            {data.recent_splits.length === 0 && <div className="text-slate-500 text-sm py-4">Нет операций</div>}
          </div>
        </div>

        <div className="card">
          <h2 className="font-bold text-lg mb-4">Распределение уровней</h2>
          <div className="space-y-3">
            {data.level_distribution.map((l: any) => (
              <div key={l.grade}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="font-semibold">{l.grade} <span className="text-[11px] text-slate-500 font-normal">{l.range}</span></span>
                  <span className="text-slate-400">{l.count} ({l.percent}%)</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className={`h-full rounded-full ${GRADE_BAR[l.grade]}`} style={{ width: `${l.percent}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {data.updated_at && <div className="text-xs text-slate-500 mt-6 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400" /> Данные обновлены {timeAgo(data.updated_at)}
      </div>}
    </>
  );
}

function Grid2({ a, b, c, d }: { a: string; b: string; c: string; d: string }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div><div className="text-xs text-slate-500">{a}</div><div className="font-semibold">{b}</div></div>
      <div><div className="text-xs text-slate-500">{c}</div><div className="font-semibold">{d}</div></div>
    </div>
  );
}

function actionLabel(a: any): string {
  if (a.action_type === "ratio_change") return `Изменён процент ${a.target ? `у ${a.target}` : ""} (ID: ${a.anchor_id}) ${a.old_value}% → ${a.new_value}%`;
  if (a.action_type === "split") return `Запуск Split · ${a.agency_name}`;
  if (a.action_type === "sync") return `Обновление данных`;
  if (a.action_type === "login") return `Вход в систему`;
  return a.message || a.action_type;
}
