"use client";
import { useState, useRef, useEffect, Fragment } from "react";
import useSWR from "swr";
import { api, fetcher, qs, ApiError } from "@/lib/api";
import { useAgencies } from "@/lib/agency";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge, Spinner, Pagination, EmptyRow } from "@/components/ui";
import { IconSplit, IconChevron } from "@/components/icons";
import { coins, usd, dt, nf } from "@/lib/format";
import type { Paged, SplitOp, Agency } from "@/lib/types";

export default function SplitPage() {
  const { agencies, selected, setSelected, reload } = useAgencies();
  const [tab, setTab] = useState<"run" | "history">("run");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<SplitOp | null>(null);
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<number | null>(null);
  const limit = 10;

  const { data: history, mutate } = useSWR<Paged<SplitOp>>(`/split/history${qs({ agency_id: selected ?? undefined, page, limit })}`, fetcher);
  const splitAgencies = agencies.filter((a) => a.can_split);
  const scopeLabel = selected === null ? "Все доступные агентства" : agencies.find((a) => a.id === selected)?.name;

  // Кулдаун 15 мин на агентство: считаем абсолютное время разблокировки и тикаем раз в секунду.
  const [nowTs, setNowTs] = useState(Date.now());
  useEffect(() => { const t = setInterval(() => setNowTs(Date.now()), 1000); return () => clearInterval(t); }, []);
  const availableAt = useRef<Record<number, number>>({});
  useEffect(() => {
    const m: Record<number, number> = {};
    for (const a of agencies) {
      const rem = a.cooldown_remaining_seconds ?? 0;
      m[a.id] = rem > 0 ? Date.now() + rem * 1000 : 0;
    }
    availableAt.current = m;
  }, [agencies]);
  const remMs = (id: number) => Math.max(0, (availableAt.current[id] || 0) - nowTs);
  const selRemMs = selected !== null ? remMs(selected) : 0;
  const onCooldown = selRemMs > 0;
  const cooledCount = splitAgencies.filter((a) => remMs(a.id) > 0).length;

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  async function run() {
    if (pollRef.current) clearInterval(pollRef.current);
    setBusy(true); setError(""); setResult(null);
    try {
      // Запуск идёт в фоне: бэкенд сразу отдаёт операцию со статусом «running».
      const op = await api.post<SplitOp>("/split/run", { agency_id: selected ?? undefined });
      setResult(op);
      mutate();
      // Опрашиваем историю, пока операция не завершится — без таймаутов и ошибок 500.
      const startedAt = Date.now();
      pollRef.current = setInterval(async () => {
        try {
          const h = await fetcher<Paged<SplitOp>>(`/split/history${qs({ agency_id: selected ?? undefined, page: 1, limit: 10 })}`);
          const cur = h.items?.find((o) => o.id === op.id);
          if (cur) {
            setResult(cur);
            if (cur.status !== "running") {
              clearInterval(pollRef.current!); pollRef.current = null;
              setBusy(false); mutate(); reload();  // reload — подтянуть свежий кулдаун агентств
            }
          }
          if (Date.now() - startedAt > 10 * 60 * 1000) { // предохранитель: 10 мин
            clearInterval(pollRef.current!); pollRef.current = null; setBusy(false);
          }
        } catch { /* временная сетевая ошибка — продолжаем опрос */ }
      }, 2500);
    } catch (e) {
      setBusy(false);
      setError(e instanceof ApiError ? e.message : "Ошибка запуска Split");
    }
  }

  const last = result || history?.items?.[0];

  return (
    <>
      <PageHeader title="Split" showRefresh={false}>
        <div className="flex gap-1 glass p-1">
          <button onClick={() => setTab("run")} className={`px-4 py-1.5 rounded-lg text-sm font-medium ${tab === "run" ? "bg-brand-600 text-white" : "text-slate-400"}`}>Запуск Split</button>
          <button onClick={() => setTab("history")} className={`px-4 py-1.5 rounded-lg text-sm font-medium ${tab === "history" ? "bg-brand-600 text-white" : "text-slate-400"}`}>История Split</button>
        </div>
      </PageHeader>

      {tab === "run" ? (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div className="xl:col-span-2 card">
            <h2 className="font-bold text-lg mb-4">Запустить Split</h2>
            <label className="label">Выберите агентство</label>
            <div className="flex flex-wrap gap-3">
              <select className="input w-auto min-w-[240px]" value={selected ?? "all"}
                      onChange={(e) => setSelected(e.target.value === "all" ? null : Number(e.target.value))}>
                <option value="all">Все доступные агентства</option>
                {splitAgencies.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
              <button className="btn-primary" disabled={busy || splitAgencies.length === 0 || onCooldown} onClick={run}>
                {busy ? <Spinner className="w-4 h-4" /> : <IconSplit className="w-4 h-4" />}
                {onCooldown ? `Доступно через ${fmtMs(selRemMs)}` : "Запустить Split"}
              </button>
            </div>
            {selected === null && cooledCount > 0 && (
              <div className="text-xs text-amber-300/90 mt-3 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                На кулдауне сейчас {cooledCount} {cooledCount === 1 ? "агентство" : "агентств"} — они будут пропущены, остальные сплитнутся.
              </div>
            )}
            <p className="text-xs text-slate-500 mt-3">
              Обрабатываются только девушки с балансом ≥ 100 coins. Меньший баланс пропускается.
              Split выполняется последовательно по {scopeLabel}. Повторный сплит одного агентства — не раньше, чем через 15 минут.
            </p>
            {error && <div className="text-sm text-rose-400 mt-4 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{error}</div>}
            {busy && <div className="text-sm text-brand-300 mt-4 flex items-center gap-2"><Spinner className="w-4 h-4" /> Выполняется Split, это может занять время...</div>}

            <div className="mt-6 overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead><tr className="border-b border-line">
                  <th className="th">Дата и время</th><th className="th">Область</th><th className="th">Обработано</th>
                  <th className="th">Пропущено</th><th className="th">Ошибки</th><th className="th">Мой заработок</th><th className="th">Общий сплит</th><th className="th">Статус</th>
                </tr></thead>
                <tbody>
                  {history?.items?.slice(0, 5).map((o) => (
                    <tr key={o.id} className="border-b border-line/60">
                      <td className="td text-slate-400">{dt(o.started_at)}</td>
                      <td className="td">{o.scope_label}</td>
                      <td className="td">{o.processed}</td><td className="td">{o.skipped}</td>
                      <td className={`td ${o.errors ? "text-rose-400" : ""}`}>{o.errors}</td>
                      <td className="td text-brand-200"><div className="leading-tight"><div>{nf(o.agency_amount_coins)} coins</div><div className="text-[11px] text-slate-500">{usd(o.agency_amount_usd)}</div></div></td>
                      <td className="td"><div className="leading-tight"><div>{nf(o.total_amount_coins)} coins</div><div className="text-[11px] text-slate-500">{usd(o.total_amount_usd)}</div></div></td>
                      <td className="td"><StatusBadge status={o.status} /></td>
                    </tr>
                  ))}
                  {!history?.items?.length && <EmptyRow cols={8} text="Нет операций" />}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <h2 className="font-bold text-lg mb-4">Последний Split</h2>
            {last ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Статус</span><StatusBadge status={last.status} /></div>
                <Row a="Область" b={last.scope_label} />
                <Row a="Дата" b={dt(last.started_at)} />
                <Row a="Обработано" b={`${last.processed} пользователей`} />
                <Row a="Пропущено" b={`${last.skipped} пользователей`} />
                <Row a="Ошибки" b={`${last.errors}`} />
                <Row a="Длительность" b={`${last.duration_seconds} сек`} />
                <div className="pt-3 border-t border-line space-y-3">
                  <div className="rounded-xl bg-brand-500/10 border border-brand-500/20 px-3 py-2.5">
                    <div className="text-xs text-brand-200/80">Мой заработок (агентство)</div>
                    <div className="text-2xl font-extrabold text-brand-200">{nf(last.agency_amount_coins)} <span className="text-base font-bold">coins</span></div>
                    <div className="text-sm text-slate-400">{usd(last.agency_amount_usd)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500">Общий сплит (девушки + агентство)</div>
                    <div className="text-xl font-extrabold">{nf(last.total_amount_coins)} coins</div>
                    <div className="text-sm text-slate-500">{usd(last.total_amount_usd)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500">Из них девушкам</div>
                    <div className="font-semibold">{nf(last.host_amount_coins)} coins <span className="text-slate-500 text-xs">{usd(last.host_amount_usd)}</span></div>
                  </div>
                </div>
              </div>
            ) : <div className="text-slate-500 text-sm py-8 text-center">Split ещё не запускался</div>}
          </div>
        </div>
      ) : (
        <div className="card !p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px]">
              <thead><tr className="border-b border-line">
                <th className="th">Дата и время</th><th className="th">Область</th><th className="th">Обработано</th>
                <th className="th">Пропущено</th><th className="th">Ошибки</th><th className="th">Мой заработок</th><th className="th">Общий сплит</th>
                <th className="th">Длительность</th><th className="th">Статус</th>
              </tr></thead>
              <tbody>
                {history?.items?.map((o) => {
                  const breakdown = o.details?.agencies as any[] | undefined;
                  const canExpand = Array.isArray(breakdown) && breakdown.length > 0;
                  const isOpen = expanded === o.id;
                  return (
                    <Fragment key={o.id}>
                      <tr className={`border-b border-line/60 hover:bg-white/[0.02] ${canExpand ? "cursor-pointer" : ""}`}
                          onClick={() => canExpand && setExpanded(isOpen ? null : o.id)}>
                        <td className="td text-slate-400">{dt(o.started_at)}</td>
                        <td className="td font-medium">
                          <span className="inline-flex items-center gap-1.5">
                            {canExpand && <IconChevron className={`w-3.5 h-3.5 text-slate-500 transition-transform ${isOpen ? "rotate-180" : ""}`} />}
                            {o.scope_label}
                          </span>
                        </td>
                        <td className="td">{o.processed}</td><td className="td">{o.skipped}</td>
                        <td className={`td ${o.errors ? "text-rose-400" : ""}`}>{o.errors}</td>
                        <td className="td text-brand-200"><div className="leading-tight"><div>{nf(o.agency_amount_coins)} coins</div><div className="text-[11px] text-slate-500">{usd(o.agency_amount_usd)}</div></div></td>
                        <td className="td"><div className="leading-tight"><div>{nf(o.total_amount_coins)} coins</div><div className="text-[11px] text-slate-500">{usd(o.total_amount_usd)}</div></div></td>
                        <td className="td text-slate-400">{o.duration_seconds}s</td>
                        <td className="td"><StatusBadge status={o.status} /></td>
                      </tr>
                      {isOpen && canExpand && (
                        <tr className="bg-black/20 border-b border-line/60">
                          <td colSpan={9} className="px-4 py-3">
                            <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-2">Разбивка по агентствам</div>
                            <table className="w-full">
                              <thead><tr className="text-left text-[11px] text-slate-500">
                                <th className="py-1 pr-4">Агентство</th><th className="py-1 pr-4">Обработано</th><th className="py-1 pr-4">Пропущено</th>
                                <th className="py-1 pr-4">Ошибки</th><th className="py-1 pr-4">Мой заработок</th><th className="py-1 pr-4">Общий сплит</th>
                              </tr></thead>
                              <tbody>
                                {breakdown!.map((b, i) => (
                                  <tr key={i} className="border-t border-line/40">
                                    <td className="py-1.5 pr-4 font-medium">{b.agency}</td>
                                    <td className="py-1.5 pr-4">{b.status === "ok" ? (b.processed ?? 0) : <span className="text-rose-400">{b.status}</span>}</td>
                                    <td className="py-1.5 pr-4 text-slate-400">{b.skipped ?? 0}</td>
                                    <td className={`py-1.5 pr-4 ${b.errors ? "text-rose-400" : "text-slate-400"}`}>{b.errors ?? 0}</td>
                                    <td className="py-1.5 pr-4 text-brand-200">{nf(b.agency_amount ?? 0)} coins</td>
                                    <td className="py-1.5 pr-4">{nf(b.amount ?? 0)} coins</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
                {!history?.items?.length && <EmptyRow cols={9} text="История пуста" />}
              </tbody>
            </table>
          </div>
          <Pagination page={page} total={history?.total ?? 0} limit={limit} onPage={setPage} />
        </div>
      )}
    </>
  );
}

function fmtMs(ms: number): string {
  const s = Math.ceil(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function Row({ a, b }: { a: string; b: string }) {
  return <div className="flex items-center justify-between text-sm"><span className="text-slate-400">{a}</span><span className="font-medium">{b}</span></div>;
}
