"use client";
import { useState } from "react";
import useSWR from "swr";
import { api, fetcher, qs, ApiError } from "@/lib/api";
import { useAgencies } from "@/lib/agency";
import { PageHeader } from "@/components/PageHeader";
import { Avatar, GradeBadge, RiskBadge, Pagination, Spinner, EmptyRow, Modal, CoinsCell } from "@/components/ui";
import { IconSearch, IconEdit } from "@/components/icons";
import { coins, usd, pct } from "@/lib/format";
import type { Host, Paged } from "@/lib/types";

const LEVELS = ["S", "A", "B", "C", "D"];
const RISKS = [["safe", "Безопасно"], ["warning", "Предупреждение"], ["danger", "В зоне риска"]];

function rateColor(status: string) {
  return status === "danger" ? "text-rose-400" : status === "warning" ? "text-amber-400" : "text-emerald-400";
}

export default function UsersPage() {
  const { selected, agencies } = useAgencies();
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState("");
  const [risk, setRisk] = useState("");
  const [sort, setSort] = useState("monthly_income");
  const [order, setOrder] = useState("desc");
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(100);
  const [edit, setEdit] = useState<Host | null>(null);

  const query = qs({ agency_id: selected ?? undefined, search, level, risk_status: risk, sort, order, page, limit });
  const { data, isLoading, mutate } = useSWR<Paged<Host>>(`/hosts${query}`, fetcher, { keepPreviousData: true });

  function toggleSort(field: string) {
    if (sort === field) setOrder(order === "desc" ? "asc" : "desc");
    else { setSort(field); setOrder("desc"); }
    setPage(1);
  }

  const canEdit = (h: Host) => agencies.find((a) => a.id === h.agency_id)?.can_change_ratio;

  return (
    <>
      <PageHeader title="Пользователи" />

      <div className="card !p-0 overflow-hidden">
        <div className="flex flex-wrap items-center gap-3 p-4 border-b border-line">
          <div className="relative flex-1 min-w-[220px]">
            <IconSearch className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input className="input pl-9" placeholder="Поиск по нику или ID..." value={search}
                   onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
          </div>
          <select className="input w-auto" value={level} onChange={(e) => { setLevel(e.target.value); setPage(1); }}>
            <option value="">Все уровни</option>
            {LEVELS.map((l) => <option key={l} value={l}>Уровень {l}</option>)}
          </select>
          <select className="input w-auto" value={risk} onChange={(e) => { setRisk(e.target.value); setPage(1); }}>
            <option value="">Все статусы риска</option>
            {RISKS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
          <select className="input w-auto" value={`${sort}:${order}`} onChange={(e) => { const [s, o] = e.target.value.split(":"); setSort(s); setOrder(o); setPage(1); }}>
            <option value="monthly_income:desc">Заработок за последние 30 дней ↓</option>
            <option value="last_day_income:desc">Заработок за вчера ↓</option>
            <option value="approval_date:desc">Дата регистрации (сначала новые) ↓</option>
            <option value="approval_date:asc">Дата регистрации (сначала старые) ↑</option>
            <option value="real_down_rate:desc">Коэфф. 30 дней ↓</option>
            <option value="grade:asc">Уровень ↑</option>
            <option value="risk_status:asc">Статус риска ↑</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1300px]">
            <thead><tr className="border-b border-line">
              <th className="th">Девушка</th>
              <th className="th">Агентство</th>
              <th className="th">%</th>
              <th className="th cursor-pointer" onClick={() => toggleSort("down_rate")}>Коэфф. профиля</th>
              <th className="th cursor-pointer" onClick={() => toggleSort("real_down_rate")}>Коэфф. 30 дней</th>
              <th className="th cursor-pointer" onClick={() => toggleSort("last_day_income")}>Хосты: за вчера</th>
              <th className="th cursor-pointer" onClick={() => toggleSort("monthly_income")}>Хосты: за 30 дней</th>
              <th className="th">Агентство: за вчера</th>
              <th className="th">Агентство: за 30 дней</th>
              <th className="th">Онлайн вчера</th>
              <th className="th">Онлайн 30 дн.</th>
              <th className="th cursor-pointer" onClick={() => toggleSort("approval_date")}>Дата рег.</th>
              <th className="th">Уровень</th>
              <th className="th">Статус риска</th>
              <th className="th text-right">Действия</th>
            </tr></thead>
            <tbody>
              {isLoading && !data ? <tr><td colSpan={15} className="td text-center py-12"><Spinner className="w-6 h-6 mx-auto text-brand-300" /></td></tr> :
                data?.items.length ? data.items.map((h) => (
                  <tr key={h.id} className="border-b border-line/60 hover:bg-white/[0.02]">
                    <td className="td">
                      <div className="flex items-center gap-3">
                        <Avatar url={h.avatar_url} name={h.nickname} />
                        <div className="leading-tight">
                          <div className="font-semibold flex items-center gap-1.5">
                            {h.nickname || "—"}
                            {h.is_blocked && <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 font-medium">Blocked</span>}
                          </div>
                          <div className="text-[11px] text-slate-500">ID: {h.display_account_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="td text-slate-400">{h.agency_name}</td>
                    <td className="td font-semibold">{pct(h.ratio_percent)}</td>
                    <td className={`td font-semibold ${h.down_rate >= 0.18 ? "text-rose-400" : "text-emerald-400"}`}>{h.down_rate}</td>
                    <td className={`td font-semibold ${rateColor(h.risk_status)}`}>{h.real_down_rate}</td>
                    <td className="td"><CoinsCell value={h.last_day_income_host} sub={h.last_day_income_host_usd} /></td>
                    <td className="td"><CoinsCell value={h.month_income_host} sub={h.month_income_host_usd} /></td>
                    <td className="td text-brand-200"><CoinsCell value={h.last_day_income_agency} sub={h.last_day_income_agency_usd} /></td>
                    <td className="td text-brand-200"><CoinsCell value={h.month_income_agency} sub={h.month_income_agency_usd} /></td>
                    <td className="td text-slate-400">{h.last_day_online || "—"}</td>
                    <td className="td text-slate-400">{h.monthly_online || "—"}</td>
                    <td className="td text-slate-400 whitespace-nowrap">{h.approval_date ? h.approval_date.slice(0, 10) : "—"}</td>
                    <td className="td"><GradeBadge grade={h.grade} range={h.grade_range} limit={h.grade_limit} /></td>
                    <td className="td"><RiskBadge status={h.risk_status} /></td>
                    <td className="td text-right">
                      {canEdit(h) && <button className="btn-ghost px-2.5 py-2" onClick={() => setEdit(h)}><IconEdit className="w-4 h-4" /></button>}
                    </td>
                  </tr>
                )) : <EmptyRow cols={15} text="Девушки не найдены" />}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between flex-wrap">
          <Pagination page={page} total={data?.total ?? 0} limit={limit} onPage={setPage} />
          <div className="px-4 text-sm text-slate-400 flex items-center gap-2">
            На странице:
            <select className="input w-auto py-1.5" value={limit} onChange={(e) => { setLimit(Number(e.target.value)); setPage(1); }}>
              {[50, 100, 200, 500].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
        </div>
      </div>

      <RatioModal host={edit} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); mutate(); }} />
    </>
  );
}

function RatioModal({ host, onClose, onSaved }: { host: Host | null; onClose: () => void; onSaved: () => void }) {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);

  if (!host) return null;

  async function save() {
    setBusy(true); setError(""); setOk(false);
    try {
      await api.post(`/hosts/${host!.id}/ratio`, { ratio_percent: Number(value) });
      setOk(true);
      setTimeout(onSaved, 700);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка");
    } finally { setBusy(false); }
  }

  return (
    <Modal open={!!host} onClose={onClose} title="Изменить процент">
      <div className="flex items-center gap-3 mb-5">
        <Avatar url={host.avatar_url} name={host.nickname} size={44} />
        <div><div className="font-semibold">{host.nickname}</div><div className="text-xs text-slate-500">ID: {host.display_account_id} · {host.agency_name}</div></div>
      </div>
      <label className="label">Новый процент (текущий: {pct(host.ratio_percent)}, макс. 20%)</label>
      <input className="input" type="number" min={0} max={20} step={0.5} value={value}
             onChange={(e) => setValue(e.target.value)} placeholder={String(host.ratio_percent)} autoFocus />
      {error && <div className="text-sm text-rose-400 mt-3">{error}</div>}
      {ok && <div className="text-sm text-emerald-400 mt-3">✓ Процент успешно изменён</div>}
      <div className="flex gap-3 mt-5">
        <button className="btn-ghost flex-1" onClick={onClose}>Отмена</button>
        <button className="btn-primary flex-1" disabled={busy || !value} onClick={save}>
          {busy ? <Spinner className="w-4 h-4" /> : null} Сохранить
        </button>
      </div>
    </Modal>
  );
}
