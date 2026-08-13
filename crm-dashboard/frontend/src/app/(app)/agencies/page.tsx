"use client";
import { useState } from "react";
import useSWR from "swr";
import { api, fetcher, qs, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useAgencies } from "@/lib/agency";
import { PageHeader } from "@/components/PageHeader";
import { Modal, Spinner, StatusBadge } from "@/components/ui";
import { IconAgency, IconPlus, IconEdit, IconTrash, IconCheck } from "@/components/icons";
import { coins, usd, onlineLabel, dt, nf } from "@/lib/format";
import type { Agency } from "@/lib/types";

export default function AgenciesPage() {
  const { me } = useAuth();
  const { reload } = useAgencies();
  const { data: list, mutate: mutateList } = useSWR<Agency[]>("/agencies", fetcher);
  const { data: stats, mutate: mutateStats } = useSWR<any>("/dashboard/stats", fetcher);
  const [form, setForm] = useState<Partial<Agency> | null>(null);

  const statMap: Record<number, any> = {};
  stats?.per_agency?.forEach((a: any) => (statMap[a.agency_id] = a));

  function refreshAll() { mutateList(); mutateStats(); reload(); }

  return (
    <>
      <PageHeader title="Агентства" showRefresh={!me?.is_superadmin}>
        {me?.is_superadmin && (
          <button className="btn-primary" onClick={() => setForm({ url: "https://admin.livegirl.me" })}>
            <IconPlus className="w-4 h-4" /> Добавить агентство
          </button>
        )}
      </PageHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {list?.map((a) => {
          const s = statMap[a.id] || {};
          return (
            <div key={a.id} className="card">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-xl bg-brand-500/15 text-brand-300 grid place-items-center"><IconAgency /></div>
                  <div>
                    <div className="font-bold text-lg">{a.name}</div>
                    <div className="flex items-center gap-2 text-[11px]">
                      <span className={`w-1.5 h-1.5 rounded-full ${a.has_session ? "bg-emerald-400" : "bg-slate-600"}`} />
                      <span className="text-slate-500">{a.has_session ? "Сессия активна" : "Нет сессии"}</span>
                    </div>
                  </div>
                </div>
                {me?.is_superadmin && (
                  <div className="flex gap-1">
                    <button className="btn-ghost px-2 py-1.5" onClick={() => setForm(a)}><IconEdit className="w-4 h-4" /></button>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-y-3 gap-x-4 text-sm">
                <Stat label="Пользователей" value={String(s.users ?? 0)} />
                <Stat label="За вчера" value={coins(s.yesterday_income_coins ?? 0)} sub={usd(s.yesterday_income_usd ?? 0)} />
                <Stat label="За 30 дней" value={coins(s.month_income_coins ?? 0)} sub={usd(s.month_income_usd ?? 0)} />
                <Stat label="Доход агентства (30 дн.)" value={coins(s.month_agency_income_coins ?? 0)} sub={usd(s.month_agency_income_usd ?? 0)} />
                <Stat label="Онлайн за вчера" value={onlineLabel(s.yesterday_online)} />
                <Stat label="Онлайн за 30 дней" value={onlineLabel(s.month_online)} />
                <Stat label="В зоне риска" value={String(s.at_risk_count ?? 0)} danger />
                <Stat label="Предупреждений" value={String(s.warnings_count ?? 0)} warn />
              </div>

              <div className="mt-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 px-4 py-3">
                <div className="text-[11px] text-emerald-300/80">Готово к выводу</div>
                <div className="font-bold text-lg text-emerald-300">
                  {coins(s.withdrawable_coins ?? 0)} <span className="text-sm font-medium text-emerald-300/70">({usd(s.withdrawable_usd ?? 0)})</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-line flex items-center justify-between text-xs text-slate-500">
                <span>Последний Split: {s.last_split_date ? dt(s.last_split_date) : "—"}</span>
                <span>{nf(s.last_split_amount ?? 0)} coins</span>
              </div>
            </div>
          );
        })}
        {list?.length === 0 && <div className="card text-slate-500 text-center py-10">Нет доступных агентств</div>}
      </div>

      {me?.is_superadmin && form && (
        <AgencyForm agency={form} onClose={() => setForm(null)} onSaved={() => { setForm(null); refreshAll(); }} />
      )}
    </>
  );
}

function Stat({ label, value, sub, danger, warn }: { label: string; value: string; sub?: string; danger?: boolean; warn?: boolean }) {
  return (
    <div>
      <div className="text-[11px] text-slate-500">{label}</div>
      <div className={`font-semibold ${danger ? "text-rose-300" : warn ? "text-amber-300" : ""}`}>{value}</div>
      {sub && <div className="text-[11px] text-slate-500">{sub}</div>}
    </div>
  );
}

function AgencyForm({ agency, onClose, onSaved }: { agency: Partial<Agency>; onClose: () => void; onSaved: () => void }) {
  const isNew = !agency.id;
  const [f, setF] = useState<any>({
    name: agency.name || "", url: agency.url || "https://admin.livegirl.me",
    account: "", password: "", aemail: "", apassword: "", tfa_required: agency.tfa_required || false,
    withdraw_account_name: agency.withdraw_account_name || "", withdraw_password: "",
    withdraw_info_domain: agency.withdraw_info_domain || "", withdraw_info_port: agency.withdraw_info_port || "",
    withdraw_domain: agency.withdraw_domain || "", withdraw_port: agency.withdraw_port || "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tfa, setTfa] = useState<{ agencyId: number } | null>(null);
  const [code, setCode] = useState("");

  const up = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));

  async function save() {
    setBusy(true); setError("");
    try {
      const payload: any = {
        ...f,
        withdraw_info_port: f.withdraw_info_port === "" ? 0 : Number(f.withdraw_info_port),
        withdraw_port: f.withdraw_port === "" ? 0 : Number(f.withdraw_port),
      };
      if (!isNew && !payload.withdraw_password) delete payload.withdraw_password;
      let saved: Agency;
      if (isNew) saved = await api.post<Agency>("/agencies", payload);
      else saved = await api.put<Agency>(`/agencies/${agency.id}`, payload);
      
      const res = await api.post<{ status: string }>(`/agencies/${saved.id}/login`);
      if (res.status === "need_tfa") { setTfa({ agencyId: saved.id }); setBusy(false); return; }
      onSaved();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка сохранения");
    } finally { setBusy(false); }
  }

  async function submitTfa() {
    setBusy(true); setError("");
    try {
      await api.post("/agencies/verify-2fa", { agency_id: tfa!.agencyId, code });
      onSaved();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Неверный код");
    } finally { setBusy(false); }
  }

  async function remove() {
    if (!confirm("Удалить агентство и все его данные?")) return;
    setBusy(true);
    try { await api.del(`/agencies/${agency.id}`); onSaved(); }
    catch (e) { setError(e instanceof ApiError ? e.message : "Ошибка"); setBusy(false); }
  }

  return (
    <Modal open onClose={onClose} title={isNew ? "Новое агентство" : `Агентство: ${agency.name}`} wide>
      {tfa ? (
        <div className="space-y-4">
          <p className="text-sm text-slate-400">Требуется код Google Authenticator для входа в панель Halo Live.</p>
          <input className="input text-center text-lg tracking-[0.4em]" maxLength={6} placeholder="000000"
                 value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} autoFocus />
          {error && <div className="text-sm text-rose-400">{error}</div>}
          <button className="btn-primary w-full" disabled={busy || code.length !== 6} onClick={submitTfa}>
            {busy ? <Spinner className="w-4 h-4" /> : <IconCheck className="w-4 h-4" />} Подтвердить
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div><label className="label">Название агентства</label><input className="input" value={f.name} onChange={(e) => up("name", e.target.value)} /></div>
            <div><label className="label">URL панели</label><input className="input" value={f.url} onChange={(e) => up("url", e.target.value)} /></div>
            <div><label className="label">Логин (шаг 1)</label><input className="input" value={f.account} onChange={(e) => up("account", e.target.value)} placeholder={isNew ? "" : "оставьте пустым, чтобы не менять"} /></div>
            <div><label className="label">Пароль (шаг 1)</label><input className="input" type="password" value={f.password} onChange={(e) => up("password", e.target.value)} /></div>
            <div><label className="label">Логин агентства (шаг 2)</label><input className="input" value={f.aemail} onChange={(e) => up("aemail", e.target.value)} /></div>
            <div><label className="label">Пароль агентства (шаг 2)</label><input className="input" type="password" value={f.apassword} onChange={(e) => up("apassword", e.target.value)} /></div>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={f.tfa_required} onChange={(e) => up("tfa_required", e.target.checked)} /> Требуется 2FA (Google Authenticator)
          </label>
          <div className="pt-2 border-t border-line">
            <div className="text-sm font-semibold mb-1">Вывод средств</div>
            <p className="text-xs text-slate-500 mb-3">
              Реквизиты отдельного аккаунта на сервере мира Halo Live — подсматриваются один раз
              в реальном запросе на вывод (DevTools → Network) и вводятся сюда.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div><label className="label">Имя аккаунта (accountName)</label><input className="input" value={f.withdraw_account_name} onChange={(e) => up("withdraw_account_name", e.target.value)} placeholder="TosAgency-Ukraine" /></div>
              <div><label className="label">Пароль</label><input className="input" type="password" value={f.withdraw_password} onChange={(e) => up("withdraw_password", e.target.value)} placeholder={isNew ? "" : "оставьте пустым, чтобы не менять"} /></div>
              <div><label className="label">Домен реквизитов (GetAgentWithdrawInfo)</label><input className="input" value={f.withdraw_info_domain} onChange={(e) => up("withdraw_info_domain", e.target.value)} placeholder="v.halolive.online" /></div>
              <div><label className="label">Порт реквизитов</label><input className="input" value={f.withdraw_info_port} onChange={(e) => up("withdraw_info_port", e.target.value.replace(/\D/g, ""))} placeholder="9002" /></div>
              <div><label className="label">Домен вывода (WithdrawByAgent)</label><input className="input" value={f.withdraw_domain} onChange={(e) => up("withdraw_domain", e.target.value)} placeholder="v.dragongirl.club" /></div>
              <div><label className="label">Порт вывода</label><input className="input" value={f.withdraw_port} onChange={(e) => up("withdraw_port", e.target.value.replace(/\D/g, ""))} placeholder="9006" /></div>
            </div>
          </div>
          {error && <div className="text-sm text-rose-400">{error}</div>}
          <div className="flex gap-3 pt-2">
            {!isNew && <button className="btn-danger" onClick={remove} disabled={busy}><IconTrash className="w-4 h-4" /> Удалить</button>}
            <button className="btn-ghost ml-auto" onClick={onClose}>Отмена</button>
            <button className="btn-primary" onClick={save} disabled={busy || !f.name}>
              {busy ? <Spinner className="w-4 h-4" /> : null} Сохранить и войти
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
