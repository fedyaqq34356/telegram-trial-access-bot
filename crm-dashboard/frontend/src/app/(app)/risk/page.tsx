"use client";
import { useState } from "react";
import useSWR from "swr";
import { fetcher, qs } from "@/lib/api";
import { useAgencies } from "@/lib/agency";
import { PageHeader } from "@/components/PageHeader";
import { Avatar, GradeBadge, RiskBadge, Pagination, Spinner, EmptyRow } from "@/components/ui";
import { IconSearch } from "@/components/icons";
import { coins, usd } from "@/lib/format";
import type { Host, Paged } from "@/lib/types";

const TABS = [["all", "Все"], ["warning", "Предупреждение"], ["danger", "В зоне риска"]];
const LEVELS = ["S", "A", "B", "C", "D"];

export default function RiskPage() {
  const { selected } = useAgencies();
  const [status, setStatus] = useState("all");
  const [level, setLevel] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const limit = 10;

  const query = qs({ agency_id: selected ?? undefined, status, level, search, page, limit });
  const { data, isLoading } = useSWR<Paged<Host>>(`/risk${query}`, fetcher, { keepPreviousData: true });

  return (
    <>
      <PageHeader title="Зона риска" />

      <div className="card !p-0 overflow-hidden">
        <div className="flex flex-wrap items-center gap-3 p-4 border-b border-line">
          <div className="flex gap-1 glass p-1">
            {TABS.map(([v, t]) => (
              <button key={v} onClick={() => { setStatus(v); setPage(1); }}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium ${status === v ? "bg-brand-600 text-white" : "text-slate-400 hover:text-white"}`}>{t}</button>
            ))}
          </div>
          <div className="relative flex-1 min-w-[200px]">
            <IconSearch className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input className="input pl-9" placeholder="Поиск по нику или ID..." value={search}
                   onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
          </div>
          <select className="input w-auto" value={level} onChange={(e) => { setLevel(e.target.value); setPage(1); }}>
            <option value="">Все уровни</option>
            {LEVELS.map((l) => <option key={l} value={l}>Уровень {l}</option>)}
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1050px]">
            <thead><tr className="border-b border-line">
              <th className="th">Девушка</th><th className="th">Агентство</th><th className="th">Уровень</th>
              <th className="th">Заработок 30 дней</th><th className="th">Коэфф. 30 дней</th>
              <th className="th">Лимит</th><th className="th">Превышение</th><th className="th">Наказание</th>
              <th className="th">Статус</th><th className="th">Причина риска</th>
            </tr></thead>
            <tbody>
              {isLoading && !data ? <tr><td colSpan={10} className="td text-center py-12"><Spinner className="w-6 h-6 mx-auto text-brand-300" /></td></tr> :
                data?.items.length ? data.items.map((h) => (
                  <tr key={h.id} className="border-b border-line/60 hover:bg-white/[0.02]">
                    <td className="td">
                      <div className="flex items-center gap-3">
                        <Avatar url={h.avatar_url} name={h.nickname} />
                        <div className="leading-tight"><div className="font-semibold">{h.nickname || "—"}</div><div className="text-[11px] text-slate-500">ID: {h.display_account_id}</div></div>
                      </div>
                    </td>
                    <td className="td text-slate-400">{h.agency_name}</td>
                    <td className="td"><GradeBadge grade={h.grade} /></td>
                    <td className="td"><div className="leading-tight"><div>{coins(h.monthly_income)}</div><div className="text-[11px] text-slate-500">{usd(h.monthly_income_usd)}</div></div></td>
                    <td className={`td font-semibold ${h.risk_status === "danger" ? "text-rose-400" : "text-amber-400"}`}>{h.real_down_rate}</td>
                    <td className="td text-slate-400">{h.grade_limit ?? "—"}</td>
                    <td className={`td font-semibold ${(h.risk_excess ?? 0) > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                      {h.risk_excess != null ? (h.risk_excess > 0 ? "+" : "") + h.risk_excess : "—"}
                    </td>
                    <td className="td text-slate-400">{h.punishment || "—"}</td>
                    <td className="td"><RiskBadge status={h.risk_status} /></td>
                    <td className="td max-w-[260px] whitespace-normal text-xs text-slate-400">{h.risk_reason}</td>
                  </tr>
                )) : <EmptyRow cols={10} text="В зоне риска никого нет 🎉" />}
            </tbody>
          </table>
        </div>
        <Pagination page={page} total={data?.total ?? 0} limit={limit} onPage={setPage} />
      </div>
    </>
  );
}
