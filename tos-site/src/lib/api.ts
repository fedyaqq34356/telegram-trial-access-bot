

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export interface AdminReview {
  id: number; flag: string; age: number; week: string; month: string;
  time_in: string; time_reply: string;
  country: Record<string, string>; date: Record<string, string>;
  msg_in: Record<string, string>; msg_reply: Record<string, string>;
}

export interface SiteContent {
  social: { telegram: string; instagram: string; tiktok: string; whatsapp: string };
  faq: { ru: { q: string; a: string }[]; en: { q: string; a: string }[]; ua: { q: string; a: string }[] };
  text_overrides: Record<string, string>;
  reviews: AdminReview[];
  apply_example_video?: Record<string, string>;
  app_downloads?: Record<string, { type: string; href: string }>;
  instruction?: Record<string, Lesson[]>;
  instruction_important?: Record<string, string[]>;
}

export async function getSiteContent(): Promise<SiteContent | null> {
  try {
    const r = await fetch(`${API_BASE}/public/site-content`, { cache: "no-store" });
    if (!r.ok) return null;
    return r.json();
  } catch {
    return null;
  }
}

export async function submitApplication(form: FormData): Promise<{ ok: boolean; id: number }> {
  const r = await fetch(`${API_BASE}/public/applications`, { method: "POST", body: form });
  if (!r.ok) {
    let detail = "Ошибка отправки заявки";
    try { detail = (await r.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return r.json();
}

export interface Callout { kind: "tip" | "important" | "forbidden" | "example"; text: string; langs?: string[] }
export interface GalleryItem { image: string; caption: string }
export interface Lesson { type: "video" | "text" | "checklist"; title: string; body?: string; url?: string; items?: string[]; image?: string; note?: string; video?: string; callouts?: Callout[]; gallery?: GalleryItem[] }

export async function reportProgress(password: string, haloId: string, kind: "quick" | "full", stepsDone: number, stepsTotal: number, completed: boolean): Promise<void> {
  if (!haloId.trim()) return;
  try {
    await fetch(`${API_BASE}/public/training/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password, halo_id: haloId, kind, steps_done: stepsDone, steps_total: stepsTotal, completed }),
    });
  } catch {  }
}

export interface TrainingData { lessons_full: Record<string, Lesson[]>; lessons_quick: Record<string, Lesson[]> }

export async function trainingLogin(password: string, appId: string): Promise<TrainingData> {
  const r = await fetch(`${API_BASE}/public/training/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password, app_id: appId }),
  });
  if (!r.ok) {
    let detail = "Неверный пароль";
    try { detail = (await r.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  const j = await r.json();
  return { lessons_full: j.lessons_full || {}, lessons_quick: j.lessons_quick || {} };
}

export interface CoefficientResult {
  id: string; agency: string; ranking: number | null; grade: string;
  monthly_income: number; down_rate: number; real_down_rate: number;
  profile_ok: boolean; monthly_ok: boolean; grade_limit: number | null;
  risk_status: "safe" | "warning" | "danger"; blocked: boolean;
}

export async function checkCoefficient(password: string, haloId: string): Promise<CoefficientResult> {
  const r = await fetch(`${API_BASE}/public/coefficient`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password, halo_id: haloId }),
  });
  if (!r.ok) {
    let detail = "Не удалось проверить коэффициент";
    try { detail = (await r.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return r.json();
}

export function mediaUrl(path: string): string {
  return path.startsWith("http") ? path : `${API_BASE.replace(/\/api$/, "")}${path}`;
}

const VISITOR_KEY = "tos_visitor_id";
const UTM_KEY = "tos_utm";
const UTM_FIELDS = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"] as const;

export function getVisitorId(): string {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem(VISITOR_KEY);
  if (!id) {
    id = (crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`);
    localStorage.setItem(VISITOR_KEY, id);
  }
  return id;
}

/** UTM «первого касания»: сохраняем при первом заходе с меткой, отдаём при заявке. */
export function captureUtm(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  const fresh: Record<string, string> = {};
  UTM_FIELDS.forEach((k) => {
    const v = params.get(k);
    if (v) fresh[k] = v.slice(0, 255);
  });
  if (Object.keys(fresh).length && !localStorage.getItem(UTM_KEY)) {
    localStorage.setItem(UTM_KEY, JSON.stringify(fresh));
  }
  return fresh;
}

export function storedUtm(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try { return JSON.parse(localStorage.getItem(UTM_KEY) || "{}"); } catch { return {}; }
}

export function trackVisit(path: string, lang: string): void {
  if (typeof window === "undefined") return;
  const utm = { ...storedUtm(), ...captureUtm() };
  const body = {
    path,
    referrer: document.referrer || "",
    visitor_id: getVisitorId(),
    lang,
    ...utm,
  };
  try {
    const json = JSON.stringify(body);
    if (navigator.sendBeacon) {
      navigator.sendBeacon(`${API_BASE}/public/track`, new Blob([json], { type: "application/json" }));
    } else {
      fetch(`${API_BASE}/public/track`, { method: "POST", headers: { "Content-Type": "application/json" }, body: json, keepalive: true }).catch(() => {});
    }
  } catch {  }
}
