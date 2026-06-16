"use client";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { api, fetcher, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PageHeader } from "@/components/PageHeader";
import { Spinner } from "@/components/ui";
import { IconPlus, IconTrash } from "@/components/icons";
import type { Testimonial } from "@/lib/types";

type Tab = "contacts" | "faq" | "reviews" | "training";
interface FaqItem { q: string; a: string }
interface Lesson { type: "video" | "text" | "checklist"; title: string; body?: string; url?: string; items?: string[]; image?: string; note?: string; video?: string }

export default function SitePage() {
  const { me } = useAuth();
  const readOnly = !me?.is_superadmin;
  const { data, mutate } = useSWR<any>("/settings", fetcher);
  const [tab, setTab] = useState<Tab>("contacts");
  const [form, setForm] = useState<any>(null);
  const [exVideo, setExVideo] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (data) {
      setForm({
        social_telegram: data.social_telegram || "", social_instagram: data.social_instagram || "",
        social_tiktok: data.social_tiktok || "", social_whatsapp: data.social_whatsapp || "",
        notify_email: data.notify_email || "",
        owner_telegram_id: data.owner_telegram_id || "", training_password: data.training_password || "",
      });
      try { setExVideo(JSON.parse(data.apply_example_video_json || "{}")); } catch { setExVideo({}); }
    }
  }, [data]);

  if (!form) return <><PageHeader title="Мой сайт" showRefresh={false} /><div className="grid place-items-center h-40 text-brand-300"><Spinner className="w-7 h-7" /></div></>;

  const up = (k: string, v: string) => setForm((s: any) => ({ ...s, [k]: v }));

  async function save() {
    setBusy(true); setMsg("");
    try {
      await api.put("/settings", { values: { ...form, apply_example_video_json: JSON.stringify(exVideo) } });
      setMsg("Сохранено"); mutate(); setTimeout(() => setMsg(""), 2500);
    } catch (e) { setMsg(e instanceof ApiError ? e.message : "Ошибка"); }
    finally { setBusy(false); }
  }

  const TABS: [Tab, string][] = [["contacts", "Контакты и доступ"], ["faq", "FAQ"], ["reviews", "Отзывы"], ["training", "Обучение"]];

  return (
    <>
      <PageHeader title="Мой сайт" showRefresh={false}>
        {!readOnly && tab !== "reviews" && tab !== "faq" && tab !== "training" && (
          <button className="btn-primary min-w-[150px] justify-center" disabled={busy} onClick={save}>{busy ? <Spinner className="w-4 h-4" /> : null} Сохранить</button>
        )}
      </PageHeader>

      <div className="flex gap-1 glass p-1 w-fit mb-5 flex-wrap">
        {TABS.map(([t, label]) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-1.5 rounded-lg text-sm font-medium ${tab === t ? "bg-brand-600 text-white" : "text-slate-400"}`}>{label}</button>
        ))}
      </div>

      {msg && <div className="mb-4 text-sm text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">{msg}</div>}

      {tab === "contacts" && (
        <div className="card max-w-2xl space-y-4">
          <F label="Telegram (ссылка или @username)" v={form.social_telegram} on={(v) => up("social_telegram", v)} ro={readOnly} />
          <F label="WhatsApp (номер в межд. формате, напр. 79991234567)" v={form.social_whatsapp} on={(v) => up("social_whatsapp", v)} ro={readOnly} />
          <F label="Instagram (ссылка)" v={form.social_instagram} on={(v) => up("social_instagram", v)} ro={readOnly} />
          <F label="TikTok (ссылка)" v={form.social_tiktok} on={(v) => up("social_tiktok", v)} ro={readOnly} />
          <div className="border-t border-line pt-4 space-y-4">
            <F label="Email для уведомлений о заявках" v={form.notify_email} on={(v) => up("notify_email", v)} ro={readOnly} />
            <F label="Telegram ID владельца (кому слать заявки)" v={form.owner_telegram_id} on={(v) => up("owner_telegram_id", v)} ro={readOnly} />
            <F label="Пароль для страницы «Обучение» (один на всех)" v={form.training_password} on={(v) => up("training_password", v)} ro={readOnly} />
          </div>
          <div className="border-t border-line pt-4 space-y-3">
            <div className="label">Видео-пример для заявки (показывается, если девушка выбрала «не было опыта») — по языкам</div>
            {[["ru", "Русский"], ["en", "English"], ["ua", "Українська"]].map(([code, label]) => (
              <div key={code} className="flex items-center gap-3 flex-wrap">
                <span className="text-xs text-slate-400 w-20">{label}</span>
                <LessonVideo video={exVideo[code]} readOnly={readOnly}
                             onChange={(url) => setExVideo((s) => ({ ...s, [code]: url }))} />
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "faq" && <FaqTab readOnly={readOnly} />}

      {tab === "reviews" && <ReviewsTab readOnly={readOnly} />}

      {tab === "training" && <TrainingTab readOnly={readOnly} />}
    </>
  );
}

const LANG_OPTS: [string, string][] = [["ru", "Русский"], ["en", "English"], ["ua", "Українська"]];

type RDraft = {
  lang: string; flag: string; country: string; age: string; week: string; month: string;
  date: string; msg_in: string; msg_reply: string; time_in: string; time_reply: string;
};
const EMPTY_R: RDraft = { lang: "ru", flag: "🇺🇦", country: "", age: "", week: "", month: "", date: "", msg_in: "", msg_reply: "", time_in: "20:15", time_reply: "20:16" };

function ReviewsTab({ readOnly }: { readOnly: boolean }) {
  const { data, mutate } = useSWR<Testimonial[]>("/site-content/testimonials", fetcher);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [draft, setDraft] = useState<RDraft>(EMPTY_R);
  const [editId, setEditId] = useState<number | null>(null);
  const d = (k: keyof RDraft, v: string) => setDraft((s) => ({ ...s, [k]: v }));

  async function save() {
    if (!draft.country.trim() || !draft.msg_in.trim()) { setErr("Заполни страну и сообщение девушки"); return; }
    setBusy(true); setErr("");
    try {
      const body = { ...draft, age: Number(draft.age || 0), is_visible: true };
      if (editId) await api.put(`/site-content/testimonials/${editId}`, body);
      else await api.post("/site-content/testimonials", body);
      setDraft(EMPTY_R); setEditId(null); mutate();
    } catch (e) { setErr(e instanceof ApiError ? e.message : "Ошибка"); }
    finally { setBusy(false); }
  }
  function edit(t: Testimonial) {
    setEditId(t.id);
    setDraft({ lang: t.lang || "ru", flag: t.flag || "", country: t.country || "", age: String(t.age || ""), week: t.week || "", month: t.month || "", date: t.date || "", msg_in: t.msg_in || "", msg_reply: t.msg_reply || "", time_in: t.time_in || "20:15", time_reply: t.time_reply || "20:16" });
    if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "smooth" });
  }
  async function toggle(t: Testimonial) {
    await api.put(`/site-content/testimonials/${t.id}`, { is_visible: !t.is_visible }); mutate();
  }
  async function remove(id: number) {
    if (!confirm("Удалить отзыв?")) return;
    await api.del(`/site-content/testimonials/${id}`); mutate();
  }

  return (
    <div className="space-y-4">
      {err && <div className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{err}</div>}
      {!readOnly && (
        <div className="card max-w-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">{editId ? "Редактировать отзыв" : "Добавить отзыв"}</h3>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Язык ввода</span>
              <select className="input w-auto py-1.5" value={draft.lang} onChange={(e) => d("lang", e.target.value)}>
                {LANG_OPTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
          </div>
          <p className="text-xs text-slate-500">Текст переводится на остальные языки автоматически. Скриншоты не нужны — карточка рисуется по полям.</p>
          <div className="grid grid-cols-4 gap-3">
            <input className="input" placeholder="Флаг 🇺🇦" value={draft.flag} onChange={(e) => d("flag", e.target.value)} />
            <input className="input col-span-2" placeholder="Страна (напр. Украины)" value={draft.country} onChange={(e) => d("country", e.target.value)} />
            <input className="input" placeholder="Возраст" value={draft.age} onChange={(e) => d("age", e.target.value)} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <input className="input" placeholder="Первая неделя ($130)" value={draft.week} onChange={(e) => d("week", e.target.value)} />
            <input className="input" placeholder="Первый месяц ($820)" value={draft.month} onChange={(e) => d("month", e.target.value)} />
            <input className="input" placeholder="Дата (12 мая)" value={draft.date} onChange={(e) => d("date", e.target.value)} />
          </div>
          <div>
            <label className="label">Сообщение девушки (входящее)</label>
            <textarea className="input min-h-[70px]" placeholder="Привет! Хочу сказать огромное спасибо за..." value={draft.msg_in} onChange={(e) => d("msg_in", e.target.value)} />
          </div>
          <div>
            <label className="label">Ответ агентства (исходящее)</label>
            <textarea className="input min-h-[50px]" placeholder="Поздравляем! 🔥 Ты большая молодец!" value={draft.msg_reply} onChange={(e) => d("msg_reply", e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input className="input" placeholder="Время сообщения (20:15)" value={draft.time_in} onChange={(e) => d("time_in", e.target.value)} />
            <input className="input" placeholder="Время ответа (20:16)" value={draft.time_reply} onChange={(e) => d("time_reply", e.target.value)} />
          </div>
          <div className="flex gap-2">
            <button className="btn-primary w-fit" disabled={busy} onClick={save}>{busy ? <Spinner className="w-4 h-4" /> : <IconPlus className="w-4 h-4" />} {editId ? "Сохранить" : "Добавить"}</button>
            {editId && <button className="btn-ghost" onClick={() => { setDraft(EMPTY_R); setEditId(null); }}>Отмена</button>}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data?.map((t) => (
          <div key={t.id} className="card !p-3 space-y-2">
            <div className="text-sm font-medium">{t.flag} Девушка из {t.country || "—"}{t.age ? `, ${t.age}` : ""}</div>
            <div className="text-xs text-neon-300">{[t.week && `1 нед: ${t.week}`, t.month && `1 мес: ${t.month}`].filter(Boolean).join(" · ")}</div>
            <div className="text-xs text-slate-400 line-clamp-2">«{t.msg_in}»</div>
            {!readOnly && (
              <div className="flex gap-2 pt-1">
                <button className="btn-ghost text-xs px-2.5 py-1" onClick={() => edit(t)}>Изменить</button>
                <button className="btn-ghost text-xs px-2.5 py-1" onClick={() => toggle(t)}>{t.is_visible ? "Скрыть" : "Показать"}</button>
                <button className="btn-danger text-xs px-2.5 py-1" onClick={() => remove(t.id)}><IconTrash className="w-3.5 h-3.5" /></button>
                <span className={`chip text-[11px] ${t.is_visible ? "bg-emerald-500/15 text-emerald-300" : "bg-white/5 text-slate-400"}`}>{t.is_visible ? "На сайте" : "Скрыт"}</span>
              </div>
            )}
          </div>
        ))}
        {!data?.length && <div className="text-sm text-slate-500">Отзывов пока нет</div>}
      </div>
    </div>
  );
}

function FaqTab({ readOnly }: { readOnly: boolean }) {
  const [lang, setLang] = useState("ru");
  const { data, mutate } = useSWR<{ lang: string; items: FaqItem[] }>(`/site-content/faq?lang=${lang}`, fetcher);
  const [items, setItems] = useState<FaqItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  useEffect(() => { if (data) setItems(data.items); }, [data]);

  async function save() {
    setBusy(true); setMsg("");
    try {
      await api.put("/site-content/faq", { lang, items });
      setMsg("Сохранено и переведено"); mutate(); setTimeout(() => setMsg(""), 2500);
    } catch (e) { setMsg(e instanceof ApiError ? e.message : "Ошибка"); }
    finally { setBusy(false); }
  }

  return (
    <div className="card max-w-3xl space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Язык ввода</span>
          <select className="input w-auto py-1.5" value={lang} onChange={(e) => setLang(e.target.value)}>
            {LANG_OPTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        {!readOnly && <button className="btn-primary min-w-[150px] justify-center" disabled={busy} onClick={save}>{busy ? <Spinner className="w-4 h-4" /> : null} Сохранить</button>}
      </div>
      {msg && <div className="text-sm text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">{msg}</div>}
      <p className="text-xs text-slate-500">Вписывай на одном языке — при сохранении переведётся на все 3 языка сайта.</p>
      {items.map((item, i) => (
        <div key={i} className="border border-line rounded-xl p-3 space-y-2">
          <div className="flex items-center gap-2">
            <input className="input" placeholder="Вопрос" disabled={readOnly} value={item.q}
                   onChange={(e) => setItems((f) => f.map((x, j) => j === i ? { ...x, q: e.target.value } : x))} />
            {!readOnly && <button className="btn-danger px-2.5 py-2" onClick={() => setItems((f) => f.filter((_, j) => j !== i))}><IconTrash className="w-4 h-4" /></button>}
          </div>
          <textarea className="input min-h-[60px]" placeholder="Ответ" disabled={readOnly} value={item.a}
                    onChange={(e) => setItems((f) => f.map((x, j) => j === i ? { ...x, a: e.target.value } : x))} />
        </div>
      ))}
      {!readOnly && <button className="btn-ghost" onClick={() => setItems((f) => [...f, { q: "", a: "" }])}><IconPlus className="w-4 h-4" /> Добавить вопрос</button>}
      <p className="text-xs text-slate-500">Если список пуст, на сайте показываются стандартные вопросы.</p>
    </div>
  );
}

function F({ label, v, on, ro }: { label: string; v: string; on: (v: string) => void; ro?: boolean }) {
  return <div><label className="label">{label}</label><input className="input" value={v} disabled={ro} onChange={(e) => on(e.target.value)} /></div>;
}

function TrainingTab({ readOnly }: { readOnly: boolean }) {
  const [lang, setLang] = useState("ru");
  const { data: fullData, mutate: mFull } = useSWR<{ lessons: Lesson[] }>(`/site-content/training-lessons?kind=full&lang=${lang}`, fetcher);
  const { data: quickData, mutate: mQuick } = useSWR<{ lessons: Lesson[] }>(`/site-content/training-lessons?kind=quick&lang=${lang}`, fetcher);
  const [full, setFull] = useState<Lesson[]>([]);
  const [quick, setQuick] = useState<Lesson[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [isErr, setIsErr] = useState(false);
  useEffect(() => { if (fullData) setFull(fullData.lessons); }, [fullData]);
  useEffect(() => { if (quickData) setQuick(quickData.lessons); }, [quickData]);

  async function save() {
    setBusy(true); setMsg(""); setIsErr(false);
    try {
      const clean = (ls: Lesson[]) => ls.map((l) => l.items ? { ...l, items: l.items.filter((x) => x.trim()) } : l);
      await api.put("/site-content/training-lessons", { kind: "quick", lang, lessons: clean(quick) });
      await api.put("/site-content/training-lessons", { kind: "full", lang, lessons: clean(full) });
      setMsg("Сохранено и переведено на все языки"); mFull(); mQuick(); setTimeout(() => setMsg(""), 3000);
    } catch (e) { setIsErr(true); setMsg(e instanceof ApiError ? e.message : "Ошибка сохранения"); }
    finally { setBusy(false); }
  }

  return (
    <div className="card max-w-3xl space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Язык ввода</span>
          <select className="input w-auto py-1.5" value={lang} onChange={(e) => setLang(e.target.value)}>
            {LANG_OPTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        {!readOnly && <button className="btn-primary min-w-[150px] justify-center" disabled={busy} onClick={save}>{busy ? <Spinner className="w-4 h-4" /> : null} Сохранить</button>}
      </div>
      {msg && <div className={`text-sm rounded-lg px-3 py-2 border ${isErr ? "text-rose-400 bg-rose-500/10 border-rose-500/20" : "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"}`}>{msg}</div>}
      <p className="text-xs text-slate-500">Вписывай на одном языке — при сохранении переведётся на все 3 языка сайта (перевод занимает несколько секунд). Пароль входа — на вкладке «Контакты и доступ».</p>
      <LessonEditor title="Быстрый старт (5–10 мин)" lessons={quick} setLessons={setQuick} readOnly={readOnly} />
      <LessonEditor title="Полное обучение (1–2 часа)" lessons={full} setLessons={setFull} readOnly={readOnly} />
    </div>
  );
}

function LessonEditor({ title, lessons, setLessons, readOnly }: { title: string; lessons: Lesson[]; setLessons: React.Dispatch<React.SetStateAction<Lesson[]>>; readOnly: boolean }) {
  return (
    <div className="border-t border-line pt-3 space-y-3">
      <div className="label">{title}</div>
      {lessons.map((l, i) => (
        <div key={i} className="border border-line rounded-xl p-3 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 shrink-0 rounded-lg grid place-items-center text-sm font-bold text-white bg-gradient-to-br from-brand-600 to-brand-500">{i + 1}</span>
            <select className="input w-auto" disabled={readOnly} value={l.type}
                    onChange={(e) => setLessons((ls) => ls.map((x, j) => j === i ? { ...x, type: e.target.value as Lesson["type"] } : x))}>
              <option value="text">Текст</option><option value="video">Видео</option><option value="checklist">Чек-лист</option>
            </select>
            <input className="input" placeholder="Заголовок урока" disabled={readOnly} value={l.title}
                   onChange={(e) => setLessons((ls) => ls.map((x, j) => j === i ? { ...x, title: e.target.value } : x))} />
            {!readOnly && <button className="btn-danger px-2.5 py-2" onClick={() => setLessons((ls) => ls.filter((_, j) => j !== i))}><IconTrash className="w-4 h-4" /></button>}
          </div>
          {l.type === "video" && (
            <input className="input" placeholder="Ссылка YouTube (или загрузите файл ниже)" disabled={readOnly} value={l.url || ""}
                   onChange={(e) => setLessons((ls) => ls.map((x, j) => j === i ? { ...x, url: e.target.value } : x))} />
          )}
          <textarea className="input min-h-[80px]" placeholder="Текст / описание (необязательно)" disabled={readOnly} value={l.body || ""}
                    onChange={(e) => setLessons((ls) => ls.map((x, j) => j === i ? { ...x, body: e.target.value } : x))} />
          <textarea className="input min-h-[80px]" placeholder="Пункты чек-листа, по одному на строку (необязательно)" disabled={readOnly}
                    value={(l.items || []).join("\n")}
                    onChange={(e) => setLessons((ls) => ls.map((x, j) => j === i ? { ...x, items: e.target.value.split("\n") } : x))} />
          <textarea className="input min-h-[44px]" placeholder="Совет / выделенный блок (необязательно) — розовая врезка на шаге" disabled={readOnly} value={l.note || ""}
                    onChange={(e) => setLessons((ls) => ls.map((x, j) => j === i ? { ...x, note: e.target.value } : x))} />
          <LessonImage image={l.image} readOnly={readOnly}
                       onChange={(url) => setLessons((ls) => ls.map((x, j) => j === i ? { ...x, image: url } : x))} />
          <LessonVideo video={l.video} readOnly={readOnly}
                       onChange={(url) => setLessons((ls) => ls.map((x, j) => j === i ? { ...x, video: url } : x))} />
        </div>
      ))}
      {!readOnly && (
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => setLessons((ls) => [...ls, { type: "text", title: "", body: "" }])}><IconPlus className="w-4 h-4" /> Текст</button>
          <button className="btn-ghost" onClick={() => setLessons((ls) => [...ls, { type: "video", title: "", url: "" }])}><IconPlus className="w-4 h-4" /> Видео</button>
          <button className="btn-ghost" onClick={() => setLessons((ls) => [...ls, { type: "checklist", title: "", items: [] }])}><IconPlus className="w-4 h-4" /> Чек-лист</button>
        </div>
      )}
    </div>
  );
}

function LessonImage({ image, onChange, readOnly }: { image?: string; onChange: (url: string) => void; readOnly: boolean }) {
  const [busy, setBusy] = useState(false);
  async function upload(file: File | null) {
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData(); fd.set("image", file);
      const r = await api.upload<{ url: string }>("/site-content/lesson-image", fd);
      onChange(r.url);
    } catch { /* ignore */ }
    finally { setBusy(false); }
  }
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {image && <img src={image} alt="" className="h-16 rounded-lg border border-line object-contain bg-bg-soft" />}
      {!readOnly && (
        <>
          <label className="btn-ghost text-xs px-3 py-1.5 cursor-pointer">
            {busy ? <Spinner className="w-3.5 h-3.5" /> : (image ? "Заменить картинку" : "Добавить картинку")}
            <input type="file" accept="image/*" className="hidden" onChange={(e) => upload(e.target.files?.[0] || null)} />
          </label>
          {image && <button className="btn-danger text-xs px-2.5 py-1.5" onClick={() => onChange("")}><IconTrash className="w-3.5 h-3.5" /></button>}
        </>
      )}
    </div>
  );
}

function LessonVideo({ video, onChange, readOnly }: { video?: string; onChange: (url: string) => void; readOnly: boolean }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  async function upload(file: File | null) {
    if (!file) return;
    setBusy(true); setErr("");
    try {
      const fd = new FormData(); fd.set("video", file);
      const r = await api.upload<{ url: string }>("/site-content/lesson-video", fd);
      onChange(r.url);
    } catch (e) { setErr(e instanceof ApiError ? e.message : "Ошибка загрузки видео"); }
    finally { setBusy(false); }
  }
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {video && <video src={video} className="h-16 rounded-lg border border-line bg-black" muted />}
      {!readOnly && (
        <>
          <label className="btn-ghost text-xs px-3 py-1.5 cursor-pointer">
            {busy ? <Spinner className="w-3.5 h-3.5" /> : (video ? "Заменить видео" : "Загрузить видео (MP4)")}
            <input type="file" accept="video/*" className="hidden" onChange={(e) => upload(e.target.files?.[0] || null)} />
          </label>
          {video && <button className="btn-danger text-xs px-2.5 py-1.5" onClick={() => onChange("")}><IconTrash className="w-3.5 h-3.5" /></button>}
        </>
      )}
      {busy && <span className="text-xs text-slate-500">загрузка… (большое видео — подождите)</span>}
      {err && <span className="text-xs text-rose-400">{err}</span>}
    </div>
  );
}
