"use client";
import { useState } from "react";
import useSWR from "swr";
import { api, fetcher, qs, ApiError } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { AppStatusBadge, AuthImage, Modal, Pagination, EmptyRow, Spinner } from "@/components/ui";
import { IconSearch, IconCopy } from "@/components/icons";
import { dt } from "@/lib/format";
import type { Application, StatusOption } from "@/lib/types";

interface AppList {
  items: Application[];
  total: number;
  page: number;
  limit: number;
  statuses: StatusOption[];
}

function writeLink(a: Application): string | null {
  const tg = (a.contact_telegram || "").trim();
  if (tg && !tg.replace(/\+/g, "").match(/^\d+$/)) {
    const m = tg.match(/(?:t\.me\/|@)?([A-Za-z0-9_]{4,})/);
    if (m) return `https://t.me/${m[1]}`;
  }
  const wa = (a.contact_whatsapp || a.contact_telegram || "").replace(/\D/g, "");
  if (wa.length >= 8) return `https://wa.me/${wa}`;
  return null;
}

export default function ApplicationsPage() {
  const [status, setStatus] = useState("all");
  const [experience, setExperience] = useState("");
  const [country, setCountry] = useState("");
  const [q, setQ] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [openId, setOpenId] = useState<number | null>(null);
  const limit = 20;

  const query = qs({
    status, experience: experience || undefined, country: country || undefined,
    q: q || undefined, date_from: dateFrom || undefined, date_to: dateTo || undefined,
    page, limit,
  });
  const { data, mutate, isLoading } = useSWR<AppList>(`/applications${query}`, fetcher, { refreshInterval: 30000 });
  const statuses = data?.statuses ?? [];

  return (
    <>
      <PageHeader title="Заявки" showRefresh={false} />

      <div className="card mb-4">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="label">Статус</label>
            <select className="input w-auto min-w-[160px]" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="all">Все статусы</option>
              {statuses.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Опыт</label>
            <select className="input w-auto" value={experience} onChange={(e) => { setExperience(e.target.value); setPage(1); }}>
              <option value="">Любой</option>
              <option value="true">Есть опыт</option>
              <option value="false">Без опыта</option>
            </select>
          </div>
          <div>
            <label className="label">Страна</label>
            <input className="input w-auto min-w-[140px]" value={country} placeholder="Украина…"
                   onChange={(e) => { setCountry(e.target.value); setPage(1); }} />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="label">Поиск (Telegram / Email)</label>
            <div className="relative">
              <IconSearch className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input className="input pl-9" value={q} placeholder="@username или email"
                     onChange={(e) => { setQ(e.target.value); setPage(1); }} />
            </div>
          </div>
          <div>
            <label className="label">С даты</label>
            <input type="date" className="input w-auto" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }} />
          </div>
          <div>
            <label className="label">По дату</label>
            <input type="date" className="input w-auto" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1); }} />
          </div>
        </div>
      </div>

      <div className="card !p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[920px]">
            <thead><tr className="border-b border-line">
              <th className="th">ID</th><th className="th">Дата</th><th className="th">Возраст</th><th className="th">Страна</th>
              <th className="th">Контакт</th><th className="th">Email</th><th className="th">Опыт</th><th className="th">Время</th>
              <th className="th">Фото</th><th className="th">Статус</th><th className="th"></th>
            </tr></thead>
            <tbody>
              {isLoading && <tr><td colSpan={11} className="td text-center py-10"><Spinner className="w-5 h-5 mx-auto" /></td></tr>}
              {!isLoading && data?.items?.map((a) => (
                <tr key={a.id} className="border-b border-line/60 hover:bg-white/[0.02] cursor-pointer" onClick={() => setOpenId(a.id)}>
                  <td className="td font-semibold">#{a.id}</td>
                  <td className="td text-slate-400">{dt(a.created_at)}</td>
                  <td className="td">{a.age}</td>
                  <td className="td">{a.country}</td>
                  <td className="td">{a.contact_display}</td>
                  <td className="td text-slate-400">{a.email || "—"}</td>
                  <td className="td">{a.experience ? "Да" : "Нет"}</td>
                  <td className="td text-slate-400">{a.time_commitment || "—"}</td>
                  <td className="td">{a.photos_count} шт.</td>
                  <td className="td"><AppStatusBadge status={a.status} label={a.status_label} /></td>
                  <td className="td text-brand-300 text-sm">Открыть</td>
                </tr>
              ))}
              {!isLoading && !data?.items?.length && <EmptyRow cols={11} text="Заявок нет" />}
            </tbody>
          </table>
        </div>
        <Pagination page={page} total={data?.total ?? 0} limit={limit} onPage={setPage} />
      </div>

      {openId !== null && (
        <ApplicationCard id={openId} statuses={statuses} onClose={() => setOpenId(null)} onChanged={() => mutate()} />
      )}
    </>
  );
}

function ApplicationCard({ id, statuses, onClose, onChanged }: {
  id: number; statuses: StatusOption[]; onClose: () => void; onChanged: () => void;
}) {
  const { data: a, mutate } = useSWR<Application>(`/applications/${id}`, fetcher);
  const [comment, setComment] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [copied, setCopied] = useState(false);

  async function setStatus(s: string) {
    setBusy(true); setErr("");
    try { await api.patch(`/applications/${id}`, { status: s }); await mutate(); onChanged(); }
    catch (e) { setErr(e instanceof ApiError ? e.message : "Ошибка"); }
    finally { setBusy(false); }
  }
  async function saveComment() {
    if (comment === null) return;
    setBusy(true); setErr("");
    try { await api.patch(`/applications/${id}`, { manager_comment: comment }); await mutate(); onChanged(); setComment(null); }
    catch (e) { setErr(e instanceof ApiError ? e.message : "Ошибка"); }
    finally { setBusy(false); }
  }

  const link = a ? writeLink(a) : null;

  return (
    <Modal open onClose={onClose} title={a ? `Заявка #${a.id}` : "Заявка"} wide>
      {!a ? <div className="py-10 text-center"><Spinner className="w-6 h-6 mx-auto" /></div> : (
        <div className="space-y-5">
          {err && <div className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{err}</div>}

          <div className="grid grid-cols-2 gap-3 text-sm">
            <Field k="Дата" v={dt(a.created_at)} />
            <Field k="Статус" v={<AppStatusBadge status={a.status} label={a.status_label} />} />
            <Field k="Возраст" v={String(a.age)} />
            <Field k="Страна" v={a.country} />
            <Field k="Telegram" v={a.contact_telegram || "—"} />
            <Field k="WhatsApp" v={a.contact_whatsapp || "—"} />
            <Field k="Email" v={a.email || "—"} />
            <Field k="Опыт" v={a.experience ? `Да${a.experience_apps ? ` (${a.experience_apps})` : ""}` : "Нет"} />
            <Field k="Готова работать" v={a.time_commitment || "—"} />
            <Field k="Источник" v={a.source} />
          </div>

          {a.photos_count > 0 && (
            <div>
              <div className="label">Фото ({a.photos_count})</div>
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: a.photos_count }).map((_, i) => (
                  <a key={i} href={`/api/applications/${id}/photo/${i}`} target="_blank" rel="noreferrer" title="Открыть в полном размере">
                    <AuthImage path={`/applications/${id}/photo/${i}`} alt={`Фото ${i + 1}`}
                               className="w-24 h-24 rounded-lg object-cover border border-line" />
                  </a>
                ))}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">Фото доступны только в CRM и не публикуются на сайте.</p>
            </div>
          )}

          <div>
            <div className="label">Действия</div>
            <div className="flex flex-wrap gap-2">
              {statuses.filter((s) => s.value !== a.status).map((s) => (
                <button key={s.value} disabled={busy} onClick={() => setStatus(s.value)} className="btn-ghost text-xs px-3 py-1.5">{s.label}</button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {link && <a href={link} target="_blank" rel="noreferrer" className="btn-primary text-xs px-3 py-1.5">✍️ Написать</a>}
              {a.email && (
                <button className="btn-ghost text-xs px-3 py-1.5" onClick={() => { navigator.clipboard.writeText(a.email); setCopied(true); setTimeout(() => setCopied(false), 1500); }}>
                  <IconCopy className="w-3.5 h-3.5" /> {copied ? "Скопировано" : "Скопировать email"}
                </button>
              )}
            </div>
          </div>

          <div>
            <div className="label">Комментарий менеджера</div>
            <textarea className="input min-h-[70px]" value={comment ?? a.manager_comment}
                      onChange={(e) => setComment(e.target.value)} placeholder="Заметка по заявке…" />
            {comment !== null && comment !== a.manager_comment && (
              <button disabled={busy} onClick={saveComment} className="btn-primary text-xs px-3 py-1.5 mt-2">Сохранить комментарий</button>
            )}
          </div>

          <div>
            <div className="label">История статусов</div>
            <div className="space-y-1.5">
              {(a.events ?? []).slice().reverse().map((ev) => (
                <div key={ev.id} className="flex items-center gap-2 text-xs text-slate-400">
                  <span className="text-slate-500">{dt(ev.created_at)}</span>
                  <span>{ev.old_status_label ? `${ev.old_status_label} → ` : ""}<span className="text-slate-200">{ev.new_status_label}</span></span>
                  <span className="text-slate-600">· {ev.actor}</span>
                </div>
              ))}
              {!(a.events ?? []).length && <div className="text-xs text-slate-500">Нет событий</div>}
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
}

function Field({ k, v }: { k: string; v: React.ReactNode }) {
  return <div><div className="text-[11px] text-slate-500">{k}</div><div className="font-medium">{v}</div></div>;
}
