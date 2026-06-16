"use client";
import { useI18n } from "@/i18n";
import type { Callout } from "@/lib/api";

const STYLE: Record<string, { box: string; label: string }> = {
  tip: { box: "bg-brand-600/15 border-brand-500/30 text-brand-50", label: "text-brand-200" },
  important: { box: "bg-neon-500/10 border-neon-500/30 text-neon-50", label: "text-neon-300" },
  forbidden: { box: "bg-rose-500/10 border-rose-500/30 text-rose-50", label: "text-rose-300" },
  example: { box: "bg-white/5 border-line text-slate-200", label: "text-slate-400" },
};

export function Callouts({ items, className = "" }: { items?: Callout[]; className?: string }) {
  const { t, lang } = useI18n();
  const list = (items || []).filter((c) => (c?.text || "").trim() && (!c.langs || c.langs.includes(lang)));
  if (list.length === 0) return null;
  const label = (k: string) =>
    k === "important" ? t.training.calloutImportant
      : k === "forbidden" ? t.training.calloutForbidden
        : k === "example" ? t.training.calloutExample
          : t.training.calloutTip;
  return (
    <div className={`space-y-2 ${className}`}>
      {list.map((c, i) => {
        const s = STYLE[c.kind] || STYLE.tip;
        return (
          <div key={i} className={`text-sm rounded-xl border px-3 py-2.5 whitespace-pre-line ${s.box}`}>
            <div className={`text-[11px] font-bold uppercase tracking-wide mb-1 ${s.label}`}>{label(c.kind)}</div>
            {c.text}
          </div>
        );
      })}
    </div>
  );
}
