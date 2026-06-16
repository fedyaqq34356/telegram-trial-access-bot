"use client";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { api, fetcher, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PageHeader } from "@/components/PageHeader";
import { Spinner } from "@/components/ui";

const GRADES = ["S", "A", "B", "C", "D"];
const EMOJI: Record<string, string> = { S: "💎", A: "🌟", B: "✨", C: "🌸", D: "🥀" };

export default function SettingsPage() {
  const { me } = useAuth();
  const readOnly = !me?.is_superadmin;
  const { data, mutate } = useSWR<any>("/settings", fetcher);
  const [tab, setTab] = useState<"general" | "levels">("general");
  const [form, setForm] = useState<any>(null);
  const [grades, setGrades] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (data) {
      setForm({
        coins_per_usd: data.coins_per_usd, max_ratio_percent: data.max_ratio_percent,
        sync_interval_minutes: data.sync_interval_minutes, split_min_balance: data.split_min_balance,
        warning_threshold: data.warning_threshold, show_blocked: data.show_blocked,
      });
      setGrades(data.grade_config);
    }
  }, [data]);

  if (!form || !grades) return <><PageHeader title="Настройки" showRefresh={false} /><div className="grid place-items-center h-40 text-brand-300"><Spinner className="w-7 h-7" /></div></>;

  const up = (k: string, v: string) => setForm((s: any) => ({ ...s, [k]: v }));
  const upGrade = (g: string, k: string, v: any) => setGrades((s: any) => ({ ...s, [g]: { ...s[g], [k]: v } }));

  async function save() {
    setBusy(true); setMsg("");
    try {
      await api.put("/settings", { values: { ...form, grade_config: JSON.stringify(grades) } });
      setMsg("Настройки сохранены");
      mutate();
      setTimeout(() => setMsg(""), 2500);
    } catch (e) { setMsg(e instanceof ApiError ? e.message : "Ошибка"); }
    finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Настройки" showRefresh={false}>
        {!readOnly && <button className="btn-primary" disabled={busy} onClick={save}>{busy ? <Spinner className="w-4 h-4" /> : null} Сохранить</button>}
      </PageHeader>

      <div className="flex gap-1 glass p-1 w-fit mb-5">
        <button onClick={() => setTab("general")} className={`px-4 py-1.5 rounded-lg text-sm font-medium ${tab === "general" ? "bg-brand-600 text-white" : "text-slate-400"}`}>Основные</button>
        <button onClick={() => setTab("levels")} className={`px-4 py-1.5 rounded-lg text-sm font-medium ${tab === "levels" ? "bg-brand-600 text-white" : "text-slate-400"}`}>Уровни и лимиты</button>
      </div>

      {msg && <div className="mb-4 text-sm text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">{msg}</div>}

      {tab === "general" ? (
        <div className="card max-w-2xl space-y-4">
          <Field label="Курс конвертации (coins за 1 USD)" value={form.coins_per_usd} onChange={(v) => up("coins_per_usd", v)} ro={readOnly} />
          <Field label="Максимальный процент пользователя (%)" value={form.max_ratio_percent} onChange={(v) => up("max_ratio_percent", v)} ro={readOnly} />
          <Field label="Интервал автообновления данных (мин.)" value={form.sync_interval_minutes} onChange={(v) => up("sync_interval_minutes", v)} ro={readOnly} />
          <Field label="Минимальный баланс для Split (coins)" value={form.split_min_balance} onChange={(v) => up("split_min_balance", v)} ro={readOnly} />
          <Field label="Порог предупреждения (доля лимита, напр. 0.9)" value={form.warning_threshold} onChange={(v) => up("warning_threshold", v)} ro={readOnly} />
          <label className="flex items-center gap-3 pt-2 cursor-pointer select-none">
            <input type="checkbox" disabled={readOnly}
                   checked={String(form.show_blocked).toLowerCase() === "true"}
                   onChange={(e) => up("show_blocked", e.target.checked ? "true" : "false")} />
            <span className="text-sm">Показывать заблокированных пользователей <span className="text-slate-500">(по умолчанию выкл.)</span></span>
          </label>
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <h2 className="font-bold text-lg mb-4">Лимиты по уровням</h2>
          <table className="w-full min-w-[640px]">
            <thead><tr className="border-b border-line">
              <th className="th">Уровень</th><th className="th">Мин. заработок (30 дней)</th>
              <th className="th">Лимит коэффициента</th><th className="th">Наказание при нарушении</th>
            </tr></thead>
            <tbody>
              {GRADES.map((g) => (
                <tr key={g} className="border-b border-line/60">
                  <td className="td font-bold text-lg">{EMOJI[g]} {g}</td>
                  <td className="td"><input className="input w-32" type="number" disabled={readOnly} value={grades[g]?.min ?? 0} onChange={(e) => upGrade(g, "min", Number(e.target.value))} /></td>
                  <td className="td"><input className="input w-28" type="number" step={0.01} disabled={readOnly} value={grades[g]?.limit ?? 0} onChange={(e) => upGrade(g, "limit", Number(e.target.value))} /></td>
                  <td className="td"><input className="input" disabled={readOnly} value={grades[g]?.punishment ?? ""} onChange={(e) => upGrade(g, "punishment", e.target.value)} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function Field({ label, value, onChange, ro }: { label: string; value: string; onChange: (v: string) => void; ro?: boolean }) {
  return (
    <div>
      <label className="label">{label}</label>
      <input className="input max-w-xs" value={value} disabled={ro} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}
