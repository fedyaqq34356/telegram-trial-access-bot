"use client";
import { useState } from "react";
import { useI18n } from "@/i18n";
import { IconGift, IconCoin, IconVideo } from "./icons";

/**
 * Hero-визуал «девушка ведёт стрим».
 * Если в public/ есть hero.jpg (реалистичное фото модели) — показываем его в рамке телефона.
 * Иначе рисуем стилизованный premium-мок стрима (плейсхолдер-слот).
 */
export function StreamerVisual() {
  const { t } = useI18n();
  const [hasPhoto, setHasPhoto] = useState(true);

  return (
    <div className="relative mx-auto w-[300px] sm:w-[340px] select-none">
      {/* свечение кольцевой лампы */}
      <div className="absolute -inset-10 rounded-full bg-neon-500/20 blur-3xl animate-pulseGlow" />
      <div className="absolute -inset-2 rounded-[2.6rem] bg-gradient-to-b from-neon-400/30 to-brand-600/20 blur-md" />

      {/* рамка телефона */}
      <div className="relative rounded-[2.4rem] border border-white/15 bg-black/70 p-2.5 shadow-neon backdrop-blur overflow-hidden">
        <div className="relative aspect-[9/19] overflow-hidden rounded-[1.9rem] bg-gradient-to-b from-brand-700/40 via-bg-card to-black">
          {/* фото модели (если есть) — кадрируем на лицо, чтобы не торчали края исходника */}
          {hasPhoto && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src="/hero.png" alt="" onError={() => setHasPhoto(false)}
                 className="absolute inset-0 w-full h-full object-cover scale-110"
                 style={{ objectPosition: "50% 28%" }} />
          )}
          {!hasPhoto && <StreamMockBackground />}

          {/* затемнение снизу для читаемости UI */}
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/70" />

          {/* верхняя плашка LIVE + зрители */}
          <div className="absolute top-3 left-3 right-3 flex items-center justify-between text-[11px]">
            <span className="chip bg-neon-500 text-white px-2 py-0.5 font-bold tracking-wide">● LIVE</span>
            <span className="chip bg-black/50 text-white px-2 py-0.5"><IconVideo className="w-3 h-3" /> 1.2k</span>
          </div>

          {/* нижняя панель «подарок» */}
          <div className="absolute bottom-3 left-3 right-3">
            <div className="glass rounded-xl2 px-3 py-2 flex items-center gap-2 text-xs">
              <span className="w-7 h-7 rounded-full grid place-items-center bg-neon-500/25 text-neon-300"><IconGift className="w-4 h-4" /></span>
              <span className="text-slate-200 font-medium">{t.home.visualGift}</span>
              <span className="ml-auto chip bg-brand-600/40 text-brand-100"><IconCoin className="w-3.5 h-3.5" /> +120</span>
            </div>
          </div>
        </div>
      </div>

      {/* плавающие карточки дохода */}
      <div className="absolute left-1 sm:-left-8 top-14 sm:top-16 animate-floaty block z-10" style={{ animationDelay: "0.4s" }}>
        <div className="glass rounded-xl2 px-3 py-2 text-xs shadow-card">
          <div className="text-slate-400">{t.home.visualPerMinute}</div>
          <div className="font-extrabold text-neon-300">$0.80+</div>
        </div>
      </div>
      <div className="absolute right-1 sm:-right-6 bottom-20 sm:bottom-24 animate-floaty block z-10" style={{ animationDelay: "1s" }}>
        <div className="glass rounded-xl2 px-3 py-2 text-xs shadow-card">
          <div className="text-slate-400">{t.home.visualPayouts}</div>
          <div className="font-extrabold text-brand-200">{t.home.visualPayoutDays}</div>
        </div>
      </div>
    </div>
  );
}

function StreamMockBackground() {
  return (
    <div className="absolute inset-0">
      <div className="absolute inset-0 bg-[radial-gradient(120px_120px_at_50%_38%,rgba(255,95,182,0.5),transparent_70%)]" />
      {/* силуэт «девушки» */}
      <div className="absolute left-1/2 -translate-x-1/2 top-[26%] w-24 h-24 rounded-full bg-gradient-to-b from-neon-300/70 to-neon-500/40 blur-[2px]" />
      <div className="absolute left-1/2 -translate-x-1/2 top-[46%] w-40 h-48 rounded-t-[5rem] bg-gradient-to-b from-brand-400/50 to-brand-700/30 blur-[1px]" />
      {/* кольцевая лампа */}
      <div className="absolute left-1/2 -translate-x-1/2 top-[22%] w-32 h-32 rounded-full border-[6px] border-white/30" />
    </div>
  );
}
