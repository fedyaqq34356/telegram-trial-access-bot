"use client";
import { useState } from "react";
import useSWR from "swr";
import { api, fetcher, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PageHeader } from "@/components/PageHeader";
import { Modal, Spinner, EmptyRow } from "@/components/ui";
import { IconPlus, IconEdit, IconTrash } from "@/components/icons";
import { dt } from "@/lib/format";
import type { CrmUser, Agency } from "@/lib/types";

export default function AdminsPage() {
  const { me } = useAuth();
  const { data: users, mutate } = useSWR<CrmUser[]>("/users", fetcher);
  const { data: agencies } = useSWR<Agency[]>("/agencies", fetcher);
  const [form, setForm] = useState<CrmUser | "new" | null>(null);

  function permLabel(u: CrmUser): string {
    if (u.role === "superadmin") return "Полный доступ";
    const parts: string[] = ["Просмотр"];
    if (u.accesses.some((a) => a.can_change_ratio)) parts.push("Изменение %");
    if (u.accesses.some((a) => a.can_split)) parts.push("Split");
    if (u.accesses.some((a) => a.can_withdraw)) parts.push("Вывод средств");
    if (u.can_manage_users) parts.push("Управление польз.");
    if (u.can_view_traffic) parts.push("Статистика сайта");
    return parts.join(", ");
  }

  function agencyLabel(u: CrmUser): string {
    if (u.role === "superadmin") return "Все агентства";
    if (u.accesses.length === 0) return "—";
    return u.accesses.map((a) => a.agency_name).join(", ");
  }

  return (
    <>
      <PageHeader title="Администраторы" showRefresh={false}>
        <button className="btn-primary" onClick={() => setForm("new")}><IconPlus className="w-4 h-4" /> Добавить администратора</button>
      </PageHeader>

      <div className="card !p-0 overflow-hidden overflow-x-auto">
        <table className="w-full min-w-[820px]">
          <thead><tr className="border-b border-line">
            <th className="th">Имя</th><th className="th">Логин</th><th className="th">Доступные агентства</th>
            <th className="th">Права доступа</th><th className="th">Статус</th><th className="th">Вход</th><th className="th text-right">Действия</th>
          </tr></thead>
          <tbody>
            {users?.map((u) => (
              <tr key={u.id} className="border-b border-line/60 hover:bg-white/[0.02]">
                <td className="td"><div className="font-semibold">{u.name || u.username}</div>{u.role === "superadmin" && <div className="text-[11px] text-brand-300">Главный админ</div>}</td>
                <td className="td text-slate-400">{u.username}</td>
                <td className="td text-slate-400 max-w-[200px] truncate">{agencyLabel(u)}</td>
                <td className="td text-slate-400 max-w-[220px] truncate">{permLabel(u)}</td>
                <td className="td"><span className={`chip ${u.is_active ? "bg-emerald-500/15 text-emerald-300" : "bg-slate-500/15 text-slate-400"}`}>{u.is_active ? "Активен" : "Отключён"}</span></td>
                <td className="td text-slate-500 text-xs">{u.last_login ? dt(u.last_login) : "—"}</td>
                <td className="td text-right">
                  <div className="flex gap-1 justify-end">
                    <button className="btn-ghost px-2 py-1.5" onClick={() => setForm(u)}><IconEdit className="w-4 h-4" /></button>
                    {u.id !== me?.id && <button className="btn-ghost px-2 py-1.5 text-rose-300" onClick={async () => {
                      if (!confirm(`Удалить пользователя ${u.username}?`)) return;
                      try { await api.del(`/users/${u.id}`); mutate(); } catch (e) { alert(e instanceof ApiError ? e.message : "Ошибка"); }
                    }}><IconTrash className="w-4 h-4" /></button>}
                  </div>
                </td>
              </tr>
            ))}
            {users?.length === 0 && <EmptyRow cols={7} />}
          </tbody>
        </table>
      </div>

      {form && <UserForm user={form === "new" ? null : form} agencies={agencies || []} isSuperadmin={!!me?.is_superadmin}
                         onClose={() => setForm(null)} onSaved={() => { setForm(null); mutate(); }} />}
    </>
  );
}

function UserForm({ user, agencies, isSuperadmin, onClose, onSaved }: {
  user: CrmUser | null; agencies: Agency[]; isSuperadmin: boolean; onClose: () => void; onSaved: () => void;
}) {
  const isNew = !user;
  const [f, setF] = useState<any>({
    username: user?.username || "", password: "", name: user?.name || "",
    role: user?.role || "admin", can_manage_users: user?.can_manage_users || false,
    can_view_traffic: user?.can_view_traffic || false,
    is_active: user?.is_active ?? true,
  });
  const [access, setAccess] = useState<Record<number, { can_view: boolean; can_change_ratio: boolean; can_split: boolean; can_withdraw: boolean }>>(() => {
    const m: any = {};
    user?.accesses.forEach((a) => (m[a.agency_id] = { can_view: a.can_view, can_change_ratio: a.can_change_ratio, can_split: a.can_split, can_withdraw: a.can_withdraw }));
    return m;
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const up = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  function toggleAgency(id: number) {
    setAccess((s) => { const n = { ...s }; if (n[id]) delete n[id]; else n[id] = { can_view: true, can_change_ratio: false, can_split: false, can_withdraw: false }; return n; });
  }
  function setPerm(id: number, perm: string, v: boolean) {
    setAccess((s) => ({ ...s, [id]: { ...s[id], [perm]: v } }));
  }

  async function save() {
    setBusy(true); setError("");
    const accesses = Object.entries(access).map(([id, p]) => ({ agency_id: Number(id), ...p }));
    const body: any = { name: f.name, role: f.role, can_manage_users: f.can_manage_users, can_view_traffic: f.can_view_traffic, accesses };
    if (f.password) body.password = f.password;
    try {
      if (isNew) await api.post("/users", { username: f.username, password: f.password || "changeme", ...body });
      else await api.put(`/users/${user!.id}`, { ...body, is_active: f.is_active });
      onSaved();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Ошибка");
    } finally { setBusy(false); }
  }

  const isSuper = f.role === "superadmin";

  return (
    <Modal open onClose={onClose} title={isNew ? "Новый администратор" : `Редактировать: ${user!.username}`} wide>
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div><label className="label">Имя</label><input className="input" value={f.name} onChange={(e) => up("name", e.target.value)} /></div>
          <div><label className="label">Логин</label><input className="input" value={f.username} disabled={!isNew} onChange={(e) => up("username", e.target.value)} /></div>
          <div><label className="label">Пароль {!isNew && "(оставьте пустым)"}</label><input className="input" type="password" value={f.password} onChange={(e) => up("password", e.target.value)} /></div>
          <div><label className="label">Роль</label>
            <select className="input" value={f.role} onChange={(e) => up("role", e.target.value)} disabled={!isSuperadmin}>
              <option value="admin">Администратор</option>
              <option value="superadmin">Главный администратор</option>
            </select>
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.can_manage_users} onChange={(e) => up("can_manage_users", e.target.checked)} /> Может управлять пользователями CRM и сайтом агентства</label>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.can_view_traffic} onChange={(e) => up("can_view_traffic", e.target.checked)} /> Доступ к статистике посещений сайта</label>
        {!isNew && <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.is_active} onChange={(e) => up("is_active", e.target.checked)} /> Активен</label>}

        {!isSuper && (
          <div>
            <label className="label">Доступ к агентствам и права</label>
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {agencies.map((a) => {
                const on = !!access[a.id];
                return (
                  <div key={a.id} className={`rounded-xl border p-3 ${on ? "border-brand-500/40 bg-brand-500/5" : "border-line"}`}>
                    <label className="flex items-center gap-2 font-medium text-sm">
                      <input type="checkbox" checked={on} onChange={() => toggleAgency(a.id)} /> {a.name}
                    </label>
                    {on && (
                      <div className="flex flex-wrap gap-4 mt-2 ml-6 text-xs text-slate-400">
                        <label className="flex items-center gap-1.5"><input type="checkbox" checked={access[a.id].can_change_ratio} onChange={(e) => setPerm(a.id, "can_change_ratio", e.target.checked)} /> Изменение %</label>
                        <label className="flex items-center gap-1.5"><input type="checkbox" checked={access[a.id].can_split} onChange={(e) => setPerm(a.id, "can_split", e.target.checked)} /> Запуск Split</label>
                        <label className="flex items-center gap-1.5"><input type="checkbox" checked={access[a.id].can_withdraw} onChange={(e) => setPerm(a.id, "can_withdraw", e.target.checked)} /> Вывод средств</label>
                      </div>
                    )}
                  </div>
                );
              })}
              {agencies.length === 0 && <div className="text-sm text-slate-500">Нет агентств</div>}
            </div>
            <p className="text-[11px] text-slate-500 mt-2">Главный администратор всегда видит все агентства.</p>
          </div>
        )}

        {error && <div className="text-sm text-rose-400">{error}</div>}
        <div className="flex gap-3 pt-2">
          <button className="btn-ghost ml-auto" onClick={onClose}>Отмена</button>
          <button className="btn-primary" disabled={busy || !f.username} onClick={save}>{busy ? <Spinner className="w-4 h-4" /> : null} Сохранить</button>
        </div>
      </div>
    </Modal>
  );
}
