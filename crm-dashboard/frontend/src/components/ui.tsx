"use client";
import { useEffect, useState } from "react";
import { coins, usd } from "@/lib/format";
import { api } from "@/lib/api";
import { IconClose } from "./icons";

const GRADE_STYLE: Record<string, string> = {
  S: "bg-brand-500/15 text-brand-300 border-brand-500/30",
  A: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  B: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  C: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  D: "bg-rose-500/15 text-rose-300 border-rose-500/30",
};
const GRADE_EMOJI: Record<string, string> = { S: "💎", A: "🌟", B: "✨", C: "🌸", D: "🥀" };

export function GradeBadge({ grade, range, limit }: { grade: string; range?: string; limit?: number | null }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className={`chip border ${GRADE_STYLE[grade] || GRADE_STYLE.D}`}>
        {GRADE_EMOJI[grade]} {grade}
      </span>
      {range && <span className="text-[11px] text-slate-500">{range}</span>}
      {limit != null && <span className="text-[11px] text-slate-500">Лимит: {limit}</span>}
    </div>
  );
}

const RISK: Record<string, { t: string; c: string }> = {
  safe: { t: "Безопасно", c: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  warning: { t: "Предупреждение", c: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
  danger: { t: "В зоне риска", c: "bg-rose-500/15 text-rose-300 border-rose-500/30" },
};
export function RiskBadge({ status }: { status: string }) {
  const r = RISK[status] || RISK.safe;
  return <span className={`chip border ${r.c}`}>{r.t}</span>;
}

const STATUS: Record<string, string> = {
  done: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  Выполнено: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  partial: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  error: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  running: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  active: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
};
const STATUS_LABEL: Record<string, string> = {
  done: "Выполнено", partial: "Частично", error: "Ошибка", running: "В процессе",
};
export function StatusBadge({ status }: { status: string }) {
  return <span className={`chip border ${STATUS[status] || "bg-white/5 text-slate-300 border-line"}`}>
    {STATUS_LABEL[status] || status}
  </span>;
}

const APP_STATUS: Record<string, string> = {
  new: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  in_progress: "bg-violet-500/15 text-violet-300 border-violet-500/30",
  contacted: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
  approved: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  rejected: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  registered: "bg-teal-500/15 text-teal-300 border-teal-500/30",
  office_activated: "bg-indigo-500/15 text-indigo-300 border-indigo-500/30",
  training: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  working: "bg-emerald-500/20 text-emerald-200 border-emerald-500/40",
};
export function AppStatusBadge({ status, label }: { status: string; label: string }) {
  return <span className={`chip border ${APP_STATUS[status] || "bg-white/5 text-slate-300 border-line"}`}>{label}</span>;
}

export function AuthImage({ path, alt, className = "" }: { path: string; alt?: string; className?: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let url: string | null = null;
    let alive = true;
    setSrc(null); setErr(false);
    api.blob(path).then((u) => { url = u; if (alive) setSrc(u); }).catch(() => { if (alive) setErr(true); });
    return () => { alive = false; if (url) URL.revokeObjectURL(url); };
  }, [path]);
  if (err) return <div className={`grid place-items-center text-slate-600 text-xs bg-bg-soft ${className}`}>нет фото</div>;
  if (!src) return <div className={`bg-bg-soft animate-pulse ${className}`} />;
  
  return <img src={src} alt={alt} className={className} />;
}

export function CoinsCell({ value, sub }: { value: number; sub?: number }) {
  return (
    <div className="leading-tight">
      <div className="font-semibold text-slate-100">{coins(value)}</div>
      <div className="text-[11px] text-slate-500">{usd(sub ?? value / 20)}</div>
    </div>
  );
}

export function Avatar({ url, name, size = 38 }: { url?: string; name?: string; size?: number }) {
  const letter = (name || "?").charAt(0).toUpperCase();
  return url ? (
    
    <img src={url} alt={name} width={size} height={size}
         className="rounded-full object-cover border border-line bg-bg-soft"
         style={{ width: size, height: size }}
         onError={(e) => ((e.target as HTMLImageElement).style.display = "none")} />
  ) : (
    <div className="rounded-full grid place-items-center bg-brand-600/30 text-brand-200 font-semibold border border-brand-500/30"
         style={{ width: size, height: size }}>
      {letter}
    </div>
  );
}

export function Spinner({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg className={`spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" opacity="0.2" />
      <path d="M21 12a9 9 0 00-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function Modal({ open, onClose, title, children, wide }: {
  open: boolean; onClose: () => void; title: string; children: React.ReactNode; wide?: boolean;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className={`glass w-full ${wide ? "max-w-2xl" : "max-w-md"} max-h-[90vh] overflow-y-auto`}
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-line sticky top-0 bg-bg-soft/80 backdrop-blur-xl">
          <h3 className="font-semibold text-lg">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><IconClose /></button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

export function Pagination({ page, total, limit, onPage }: {
  page: number; total: number; limit: number; onPage: (p: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / limit));
  const from = total === 0 ? 0 : (page - 1) * limit + 1;
  const to = Math.min(page * limit, total);
  const nums: (number | string)[] = [];
  for (let i = 1; i <= pages; i++) {
    if (i <= 2 || i > pages - 1 || Math.abs(i - page) <= 1) nums.push(i);
    else if (nums[nums.length - 1] !== "…") nums.push("…");
  }
  return (
    <div className="flex items-center justify-between px-4 py-3 text-sm text-slate-400 border-t border-line">
      <span>Показано {from}–{to} из {total}</span>
      <div className="flex items-center gap-1">
        <button className="btn-ghost px-2.5 py-1.5" disabled={page <= 1} onClick={() => onPage(page - 1)}>‹</button>
        {nums.map((n, i) =>
          n === "…" ? <span key={i} className="px-2 text-slate-600">…</span> :
          <button key={i} onClick={() => onPage(n as number)}
                  className={`px-3 py-1.5 rounded-lg ${n === page ? "bg-brand-600 text-white" : "hover:bg-white/5"}`}>{n}</button>
        )}
        <button className="btn-ghost px-2.5 py-1.5" disabled={page >= pages} onClick={() => onPage(page + 1)}>›</button>
      </div>
    </div>
  );
}

export function EmptyRow({ cols, text = "Нет данных" }: { cols: number; text?: string }) {
  return <tr><td colSpan={cols} className="td text-center text-slate-500 py-10">{text}</td></tr>;
}
