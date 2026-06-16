const ACCESS = "vio_access";
const REFRESH = "vio_refresh";

export function getAccess(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS);
}
export function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS, access);
  localStorage.setItem(REFRESH, refresh);
}
export function clearTokens() {
  localStorage.removeItem(ACCESS);
  localStorage.removeItem(REFRESH);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function refreshToken(): Promise<boolean> {
  const refresh = localStorage.getItem(REFRESH);
  if (!refresh) return false;
  const r = await fetch("/api/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!r.ok) return false;
  const data = await r.json();
  setTokens(data.access_token, data.refresh_token);
  return true;
}

async function raw(path: string, init: RequestInit, retry = true): Promise<Response> {
  const token = getAccess();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  // для FormData Content-Type выставляет браузер (boundary); JSON — ставим сами
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  const res = await fetch(`/api${path}`, { ...init, headers });
  if (res.status === 401 && retry) {
    const ok = await refreshToken();
    if (ok) return raw(path, init, false);
    clearTokens();
    const bp = process.env.NEXT_PUBLIC_BASE_PATH || "";
    if (typeof window !== "undefined" && !window.location.pathname.startsWith(`${bp}/login`)) {
      window.location.href = `${bp}/login`;
    }
  }
  return res;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail || detail;
    } catch {}
    throw new ApiError(res.status, typeof detail === "string" ? detail : "Ошибка запроса");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => raw(path, { method: "GET" }).then((r) => handle<T>(r)),
  post: <T>(path: string, body?: any) =>
    raw(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }).then((r) => handle<T>(r)),
  put: <T>(path: string, body?: any) =>
    raw(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }).then((r) => handle<T>(r)),
  patch: <T>(path: string, body?: any) =>
    raw(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }).then((r) => handle<T>(r)),
  del: <T>(path: string) => raw(path, { method: "DELETE" }).then((r) => handle<T>(r)),
  // multipart (FormData): Content-Type выставит браузер
  upload: <T>(path: string, form: FormData, method: "POST" | "PUT" = "POST") =>
    raw(path, { method, body: form }).then((r) => handle<T>(r)),
  // приватный файл (фото заявки) → object URL (нужна авторизация в заголовке)
  blob: (path: string) =>
    raw(path, { method: "GET" }).then(async (r) => {
      if (!r.ok) throw new ApiError(r.status, "Не удалось загрузить файл");
      return URL.createObjectURL(await r.blob());
    }),
};

export const fetcher = <T>(path: string) => api.get<T>(path);

export function qs(params: Record<string, any>): string {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") p.set(k, String(v));
  });
  const s = p.toString();
  return s ? `?${s}` : "";
}
