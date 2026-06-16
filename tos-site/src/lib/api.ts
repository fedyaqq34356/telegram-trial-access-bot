// Базовый URL backend-а. В деве next.config проксирует /api на :8000,
// в проде nginx отдаёт /api на backend. Можно переопределить NEXT_PUBLIC_API_BASE.
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

export interface Lesson { type: "video" | "text" | "checklist"; title: string; body?: string; url?: string; items?: string[]; image?: string; note?: string; video?: string }

export async function reportProgress(password: string, haloId: string, kind: "quick" | "full", stepsDone: number, stepsTotal: number, completed: boolean): Promise<void> {
  if (!haloId.trim()) return;
  try {
    await fetch(`${API_BASE}/public/training/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password, halo_id: haloId, kind, steps_done: stepsDone, steps_total: stepsTotal, completed }),
    });
  } catch { /* прогресс не критичен */ }
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
