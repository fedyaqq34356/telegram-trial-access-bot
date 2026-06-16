"use client";
import { useI18n, type Lang } from "@/i18n";
import { reviewsI18n, type SeedReview } from "@/data/reviews";
import { IconCheck } from "./icons";

function ageWord(lang: Lang, n: number): string {
  if (lang === "en") return `${n} years`;
  const m10 = n % 10, m100 = n % 100;
  const forms = lang === "ua" ? ["рік", "роки", "років"] : ["год", "года", "лет"];
  let w = forms[2];
  if (m10 === 1 && m100 !== 11) w = forms[0];
  else if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) w = forms[1];
  return `${n} ${w}`;
}

// Анонимный аватар-силуэт (никаких реальных фото/имён)
function AnonAvatar({ className = "w-7 h-7" }: { className?: string }) {
  return (
    <span className={`${className} rounded-full grid place-items-center bg-white/20 overflow-hidden shrink-0`}>
      <svg viewBox="0 0 24 24" className="w-full h-full text-white/70 blur-[0.5px]" fill="currentColor">
        <circle cx="12" cy="9" r="4" />
        <path d="M4 20c0-4 4-6 8-6s8 2 8 6v1H4z" />
      </svg>
    </span>
  );
}

export function ReviewCard({ review }: { review: SeedReview }) {
  const { t, lang } = useI18n();
  const loc = reviewsI18n[lang];
  const country = loc.countries[review.countryKey] || review.countryKey;

  return (
    <div className="card p-4 sm:p-5 h-full flex flex-col sm:flex-row gap-4">
      {/* META */}
      <div className="sm:w-40 shrink-0 flex flex-row sm:flex-col gap-x-4 gap-y-3 items-start">
        <div>
          <div className="font-bold leading-tight">{t.reviews.cardFrom} {country}</div>
          <div className="text-2xl mt-0.5">{review.flag}</div>
          <div className="text-sm text-slate-400 mt-1">{ageWord(lang, review.age)}</div>
        </div>
        <div className="space-y-2">
          {review.results.map((r, i) => (
            <div key={i}>
              <div className="text-[11px] uppercase tracking-wide text-slate-500">{loc.res[r.label] || r.label}</div>
              <div className="text-lg font-extrabold text-neon-300 leading-none">{r.amount}</div>
            </div>
          ))}
        </div>
        <span className="chip bg-neon-500/15 text-neon-300 text-[11px] mt-auto sm:self-start">
          <IconCheck className="w-3.5 h-3.5" /> {t.reviews.verified}
        </span>
      </div>

      {/* TELEGRAM CHAT */}
      <div className="flex-1 min-w-0 rounded-2xl overflow-hidden border border-white/10 bg-[#0e1621]">
        {/* header (telegram-blue) */}
        <div className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-[#2AABEE] to-[#1c93d6]">
          <svg viewBox="0 0 24 24" className="w-4 h-4 text-white/90" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
          <AnonAvatar className="w-7 h-7" />
          <div className="leading-tight min-w-0">
            <div className="h-2.5 w-20 rounded bg-white/40 mb-1" />
            <div className="text-[10px] text-white/80">{t.reviews.lastSeen}</div>
          </div>
          <span className="ml-auto text-white/70 text-lg leading-none">⋮</span>
        </div>

        {/* messages */}
        <div className="p-3 space-y-2 bg-[radial-gradient(circle_at_30%_10%,rgba(124,58,237,0.10),transparent_60%)]">
          <div className="flex justify-center">
            <span className="text-[10px] text-slate-400 bg-black/30 rounded-full px-2 py-0.5">{review.date}</span>
          </div>
          {review.messages.map((m, i) => (
            m.side === "in" ? (
              <div key={i} className="flex">
                <div className="max-w-[85%] rounded-2xl rounded-tl-md bg-[#1e2c3a] text-slate-100 text-sm px-3 py-2 shadow">
                  {m.text}
                  <span className="block text-right text-[10px] text-slate-500 mt-0.5">{m.time}</span>
                </div>
              </div>
            ) : (
              <div key={i} className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl rounded-tr-md bg-gradient-to-br from-emerald-700/70 to-emerald-600/60 text-emerald-50 text-sm px-3 py-2 shadow">
                  {m.text}
                  <span className="flex items-center justify-end gap-1 text-[10px] text-emerald-200/80 mt-0.5">
                    {m.time}
                    <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round"><path d="M1 13l4 4L13 7M11 15l1 1 8-10" /></svg>
                  </span>
                </div>
              </div>
            )
          ))}
        </div>
      </div>
    </div>
  );
}
