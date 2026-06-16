"use client";
import { useState } from "react";
import useSWR from "swr";
import { api, fetcher, qs, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge, Pagination, EmptyRow, Spinner } from "@/components/ui";
import { IconTrash } from "@/components/icons";
import { dt } from "@/lib/format";

const TYPES = [["", "Все действия"], ["ratio_change", "Изменение %"], ["split", "Split"], ["sync", "Обновление"], ["login", "Вход"]];
const ACTION_RU: Record<string, string> = { ratio_change: "Изменён процент", split: "Запущен Split", sync: "Обновление данных", login: "Вход в систему" };

export default function LogsPage() {
  const { me } = useAuth();
  const [type, setType] = useState("");
  const [page, setPage] = useState(1);
  const [clearing, setClearing] = useState(false);
  const limit = 20;
  const { data, isLoading, mutate } = useSWR<any>(`/logs/actions${qs({ action_type: type, page, limit })}`, fetcher, { keepPreviousData: true });

  async function clearLogs() {
    if (!confirm("Очистить весь журнал изменений? Действие необратимо.")) return;
    setClearing(true);
    try {
      await api.del("/logs/actions");
      setPage(1);
      mutate();
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "Ошибка очистки журнала");
    } finally { setClearing(false); }
  }

  function details(a: any): string {
    if (a.action_type === "ratio_change") return `${a.target || a.anchor_id} (ID: ${a.anchor_id}): ${a.old_value}% → ${a.new_value}%`;
    if (a.action_type === "split") return `${a.agency_name} · ${a.message}`;
    return a.message || a.agency_name || "—";
  }

  return (
    <>
      <PageHeader title="Журнал изменений" showRefresh={false}>
        <select className="input w-auto" value={type} onChange={(e) => { setType(e.target.value); setPage(1); }}>
          {TYPES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
        </select>
        {me?.is_superadmin && (
          <button className="btn-danger" disabled={clearing || !data?.total} onClick={clearLogs}>
            {clearing ? <Spinner className="w-4 h-4" /> : <IconTrash className="w-4 h-4" />} Очистить журнал
          </button>
        )}
      </PageHeader>

      <div className="card !p-0 overflow-hidden overflow-x-auto">
        <table className="w-full min-w-[760px]">
          <thead><tr className="border-b border-line">
            <th className="th">Дата и время</th><th className="th">Пользователь</th><th className="th">Действие</th>
            <th className="th">Детали</th><th className="th">Статус</th>
          </tr></thead>
          <tbody>
            {isLoading && !data ? <tr><td colSpan={5} className="td text-center py-12"><Spinner className="w-6 h-6 mx-auto text-brand-300" /></td></tr> :
              data?.items.length ? data.items.map((a: any) => (
                <tr key={a.id} className="border-b border-line/60 hover:bg-white/[0.02]">
                  <td className="td text-slate-400">{dt(a.created_at)}</td>
                  <td className="td font-medium">{a.username || "система"}</td>
                  <td className="td">{ACTION_RU[a.action_type] || a.action_type}</td>
                  <td className="td text-slate-400 max-w-[360px] whitespace-normal">{details(a)}</td>
                  <td className="td">{a.status ? <StatusBadge status={a.status} /> : "—"}</td>
                </tr>
              )) : <EmptyRow cols={5} text="Журнал пуст" />}
          </tbody>
        </table>
        <Pagination page={page} total={data?.total ?? 0} limit={limit} onPage={setPage} />
      </div>
    </>
  );
}
