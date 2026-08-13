"use client";
import { useState } from "react";
import useSWR from "swr";
import { api, fetcher, qs, ApiError } from "@/lib/api";
import { useAgencies } from "@/lib/agency";
import { PageHeader } from "@/components/PageHeader";
import { Modal, StatusBadge, Spinner, EmptyRow } from "@/components/ui";
import { IconWallet, IconCheck } from "@/components/icons";
import { dt } from "@/lib/format";
import type { Paged, WithdrawOp } from "@/lib/types";

type Step = "idle" | "tfa" | "confirm" | "done";

export default function WithdrawPage() {
  const { agencies } = useAgencies();
  const withdrawable = agencies.filter((a) => a.withdraw_configured && a.can_withdraw);

  const [agencyId, setAgencyId] = useState<number | null>(null);
  const [step, setStep] = useState<Step>("idle");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [code, setCode] = useState("");
  const [preview, setPreview] = useState<{ address: string; network: string; balanceUsd?: number } | null>(null);
  const [insufficient, setInsufficient] = useState<{ balance: number; min: number } | null>(null);
  const [result, setResult] = useState<WithdrawOp | null>(null);
  const [diagBusy, setDiagBusy] = useState(false);
  const [diagResults, setDiagResults] = useState<any[] | null>(null);

  const { data: history, mutate } = useSWR<Paged<WithdrawOp>>(
    `/withdraw/history${qs({ agency_id: agencyId ?? undefined, page: 1, limit: 10 })}`,
    fetcher
  );

  async function runDiagnose() {
    if (!agencyId) return;
    setDiagBusy(true); setDiagResults(null); setError("");
    try {
      const res = await api.post<any>(`/withdraw/${agencyId}/diagnose`, {});
      if (res.status === "need_tfa") {
        setError("Нужен код 2FA — сначала выполните обычный «Проверить и подготовить вывод», введите код, затем повторите диагностику.");
        return;
      }
      setDiagResults(res.results || []);
      if (res.results?.some((r: any) => r.ok)) mutate();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка диагностики");
    } finally {
      setDiagBusy(false);
    }
  }

  function reset() {
    setStep("idle"); setError(""); setCode(""); setPreview(null); setInsufficient(null); setResult(null);
  }

  async function startPreview() {
    if (!agencyId) return;
    setBusy(true); setError(""); setInsufficient(null);
    try {
      const res = await api.post<any>(`/withdraw/${agencyId}/preview`, {});
      if (res.status === "need_tfa") { setStep("tfa"); setBusy(false); return; }
      if (res.status === "insufficient_balance") {
        setInsufficient({ balance: res.balance_usd, min: res.min_withdraw_usd });
        setStep("idle"); setBusy(false); return;
      }
      if (res.status === "ready") {
        setPreview({ address: res.address, network: res.network, balanceUsd: res.balance_usd });
        setStep("confirm");
        setBusy(false);
        return;
      }
      setError(`Не удалось начать вывод: ${res.status}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка запроса на вывод");
    } finally {
      setBusy(false);
    }
  }

  async function submitTfa() {
    if (!agencyId) return;
    setBusy(true); setError(""); setInsufficient(null);
    try {
      const res = await api.post<any>("/withdraw/verify-2fa", { agency_id: agencyId, code });
      if (res.status === "insufficient_balance") {
        setInsufficient({ balance: res.balance_usd, min: res.min_withdraw_usd });
        setStep("idle");
        return;
      }
      if (res.status === "ready") {
        setPreview({ address: res.address, network: res.network, balanceUsd: res.balance_usd });
        setStep("confirm");
      } else {
        setError(`Не удалось начать вывод: ${res.status}`);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Неверный код");
    } finally {
      setBusy(false);
    }
  }

  // Финальный запрос уходит на Halo Live прямо отсюда, из браузера администратора.
  // С IP сервера тот же запрос отклоняется с retCode -117, с обычного устройства проходит,
  // поэтому бэкенд только готовит запрос (логин, 2FA, токен, адрес) и принимает результат.
  async function confirmWithdraw() {
    if (!agencyId) return;
    setBusy(true); setError("");
    let opId: number | null = null;
    try {
      const req = await api.post<any>(`/withdraw/${agencyId}/client-request`, {});
      opId = req.op_id;

      let data: any;
      try {
        const res = await fetch(req.url, {
          method: "POST",
          headers: req.headers,
          body: JSON.stringify(req.body),
        });
        data = await res.json();
      } catch (netErr) {
        const message = `Запрос до Halo Live не дошёл: ${netErr instanceof Error ? netErr.message : "ошибка сети"}`;
        await api.post(`/withdraw/${agencyId}/client-result`, { op_id: opId, ret_code: null, message });
        setError(`${message}. Ответ не получен — прежде чем повторять, проверьте баланс агентства: запрос мог успеть пройти.`);
        mutate();
        return;
      }

      const op = await api.post<WithdrawOp>(`/withdraw/${agencyId}/client-result`, {
        op_id: opId,
        ret_code: data?.retCode ?? null,
        message: data?.message || "",
      });
      setResult(op);
      setStep("done");
      mutate();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка вывода");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader title="Вывод средств" showRefresh={false} />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 card">
          <h2 className="font-bold text-lg mb-4 flex items-center gap-2"><IconWallet className="w-5 h-5 text-brand-400" /> Вывести средства агентства</h2>

          {withdrawable.length === 0 ? (
            <div className="text-sm text-slate-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
              {agencies.some((a) => a.withdraw_configured)
                ? "У вас нет права на вывод средств ни для одного агентства. Обратитесь к главному администратору."
                : "Ни у одного агентства не заданы реквизиты вывода. Откройте «Агентства» → нужное агентство → заполните блок «Вывод средств»."}
            </div>
          ) : (
            <>
              <label className="label">Агентство</label>
              <select
                className="input w-auto min-w-[260px]"
                value={agencyId ?? ""}
                disabled={step !== "idle"}
                onChange={(e) => { setAgencyId(e.target.value ? Number(e.target.value) : null); reset(); }}
              >
                <option value="">Выберите агентство</option>
                {withdrawable.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>

              {error && <div className="text-sm text-rose-400 mt-4 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{error}</div>}

              {insufficient && (
                <div className="text-sm text-amber-300 mt-4 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                  Недостаточно средств для вывода: на балансе ${insufficient.balance.toFixed(2)},
                  минимум для вывода у Halo Live — ${insufficient.min.toFixed(0)}.
                </div>
              )}

              {step === "idle" && agencyId && (
                <div className="mt-4">
                  <button className="btn-primary" disabled={busy} onClick={startPreview}>
                    {busy ? <Spinner className="w-4 h-4" /> : <IconWallet className="w-4 h-4" />} Проверить и подготовить вывод
                  </button>
                  <button className="btn-ghost ml-2" disabled={diagBusy} onClick={runDiagnose}>
                    {diagBusy ? <Spinner className="w-4 h-4" /> : null} Диагностика (перебрать варианты)
                  </button>
                  <p className="text-xs text-slate-500 mt-2">
                    Деньги ещё не списываются — сначала покажем адрес и сеть для подтверждения.
                    Минимальная сумма для вывода у Halo Live — $100.
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    «Диагностика» перебирает несколько форм запроса подряд (каждая — реальная попытка
                    вывода со свежим токеном) и останавливается на первой, которая сработает.
                  </p>
                </div>
              )}

              {diagResults && (
                <div className="mt-4 space-y-2">
                  {diagResults.map((r: any, i: number) => (
                    <div key={i} className={`text-sm rounded-lg px-3 py-2 border ${r.ok ? "bg-emerald-500/10 border-emerald-500/20" : "bg-rose-500/10 border-rose-500/20"}`}>
                      <span className="font-mono">{r.variant}</span>: {r.ok ? "✅ УСПЕХ" : `❌ retCode ${r.retCode ?? "—"} — ${r.message || r.error || ""}`}
                    </div>
                  ))}
                  {diagResults.every((r: any) => !r.ok) && (
                    <p className="text-xs text-amber-300/80">
                      Ни один вариант не сработал — значит, дело не в форме запроса. Полные детали каждой
                      попытки — в логах бэкенда (journalctl).
                    </p>
                  )}
                </div>
              )}

              {step === "confirm" && preview && (
                <div className="mt-4 space-y-3">
                  <div className="rounded-xl bg-brand-500/10 border border-brand-500/20 px-4 py-3">
                    <div className="text-xs text-slate-400 mb-1">Вывод пойдёт на адрес (сеть {preview.network}):</div>
                    <div className="font-mono text-sm break-all">{preview.address}</div>
                    {typeof preview.balanceUsd === "number" && (
                      <div className="text-xs text-slate-400 mt-2">Баланс к выводу: ${preview.balanceUsd.toFixed(2)}</div>
                    )}
                  </div>
                  <div className="flex gap-3">
                    <button className="btn-ghost" onClick={reset} disabled={busy}>Отмена</button>
                    <button className="btn-primary" onClick={confirmWithdraw} disabled={busy}>
                      {busy ? <Spinner className="w-4 h-4" /> : <IconCheck className="w-4 h-4" />} Подтвердить вывод
                    </button>
                  </div>
                  <p className="text-xs text-amber-300/80">
                    Действие необратимо. Проверьте адрес перед подтверждением.
                  </p>
                </div>
              )}

              {step === "done" && result && (
                <div className="mt-4 space-y-3">
                  <div className={`rounded-xl border px-4 py-3 ${result.status === "ok" ? "bg-emerald-500/10 border-emerald-500/20" : "bg-rose-500/10 border-rose-500/20"}`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold">{result.status === "ok" ? "Вывод выполнен" : "Ошибка вывода"}</span>
                      <StatusBadge status={result.status} />
                    </div>
                    {result.message && <div className="text-sm text-slate-400">{result.message}</div>}
                  </div>
                  <button className="btn-ghost" onClick={reset}>Новый вывод</button>
                </div>
              )}
            </>
          )}

          <div className="mt-8">
            <h3 className="text-sm font-semibold text-slate-400 mb-3">История выводов</h3>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px]">
                <thead><tr className="border-b border-line">
                  <th className="th">Дата</th><th className="th">Агентство</th><th className="th">Адрес</th>
                  <th className="th">Сеть</th><th className="th">Статус</th>
                </tr></thead>
                <tbody>
                  {history?.items?.map((o) => (
                    <tr key={o.id} className="border-b border-line/60">
                      <td className="td text-slate-400">{dt(o.created_at)}</td>
                      <td className="td">{o.agency_name}</td>
                      <td className="td font-mono text-xs">{o.address}</td>
                      <td className="td">{o.network}</td>
                      <td className="td"><StatusBadge status={o.status} /></td>
                    </tr>
                  ))}
                  {!history?.items?.length && <EmptyRow cols={5} text="Выводов ещё не было" />}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="font-bold text-lg mb-4">Как это работает</h2>
          <ol className="text-sm text-slate-400 space-y-3 list-decimal list-inside">
            <li>Выбираете агентство и жмёте «Проверить и подготовить вывод».</li>
            <li>Если нужен код Google Authenticator — вводите его один раз.</li>
            <li>Бот показывает адрес, сеть и баланс — проверьте перед подтверждением.</li>
            <li>Жмёте «Подтвердить вывод» — только после этого деньги списываются. Отменить нельзя.</li>
          </ol>
          <p className="text-xs text-slate-500 mt-4">
            Последний шаг выполняет сам браузер с вашего устройства — Halo Live принимает вывод только
            с обычного IP, а не с IP сервера. Не закрывайте вкладку до появления результата.
          </p>
          <p className="text-xs text-slate-500 mt-4 pt-4 border-t border-line">
            Минимальная сумма для вывода у Halo Live — $100; если баланс меньше, вывод не начнётся.
          </p>
          <p className="text-xs text-slate-500 mt-2">
            Право «Вывод средств» на конкретное агентство выдаётся в разделе «Администраторы» — по умолчанию
            его нет ни у кого, кроме главного администратора.
          </p>
          <p className="text-xs text-slate-500 mt-2">
            История ниже — это записи именно тех выводов, что были сделаны через эту кнопку. Halo Live не
            отдаёт отдельный API с историей выводов, поэтому старые операции (сделанные не отсюда) в списке
            не появятся.
          </p>
        </div>
      </div>

      <Modal open={step === "tfa"} onClose={reset} title="Код подтверждения">
        <div className="space-y-4">
          <p className="text-sm text-slate-400">Требуется код Google Authenticator для входа в панель Halo Live.</p>
          <input className="input text-center text-lg tracking-[0.4em]" maxLength={6} placeholder="000000"
                 value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} autoFocus />
          {error && <div className="text-sm text-rose-400">{error}</div>}
          <button className="btn-primary w-full" disabled={busy || code.length !== 6} onClick={submitTfa}>
            {busy ? <Spinner className="w-4 h-4" /> : <IconCheck className="w-4 h-4" />} Подтвердить
          </button>
        </div>
      </Modal>
    </>
  );
}
