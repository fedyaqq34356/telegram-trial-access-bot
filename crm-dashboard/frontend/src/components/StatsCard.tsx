"use client";

const TONE: Record<string, { ring: string; icon: string; glow: string }> = {
  purple: { ring: "from-brand-500/20", icon: "text-brand-300 bg-brand-500/15", glow: "shadow-glow" },
  blue: { ring: "from-sky-500/20", icon: "text-sky-300 bg-sky-500/15", glow: "" },
  green: { ring: "from-emerald-500/20", icon: "text-emerald-300 bg-emerald-500/15", glow: "" },
  orange: { ring: "from-orange-500/20", icon: "text-orange-300 bg-orange-500/15", glow: "" },
  red: { ring: "from-rose-500/20", icon: "text-rose-300 bg-rose-500/15", glow: "" },
};

export function StatsCard({ title, value, sub, icon, tone = "purple" }: {
  title: string; value: string; sub?: string; icon: React.ReactNode; tone?: keyof typeof TONE;
}) {
  const t = TONE[tone];
  return (
    <div className={`card relative overflow-hidden ${t.glow}`}>
      <div className={`absolute inset-0 bg-gradient-to-br ${t.ring} to-transparent opacity-60 pointer-events-none`} />
      <div className="relative flex items-start gap-3">
        <div className={`w-11 h-11 rounded-xl grid place-items-center ${t.icon}`}>{icon}</div>
        <div className="min-w-0">
          <div className="text-xs text-slate-400 mb-1">{title}</div>
          <div className="text-2xl font-extrabold tracking-tight truncate">{value}</div>
          {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
        </div>
      </div>
    </div>
  );
}
