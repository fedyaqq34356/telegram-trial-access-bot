"use client";
import Link from "next/link";
import { useI18n } from "@/i18n";
import { Section, SectionHeading, Reveal, ApplyButton, FeatureCard, CtaBand } from "@/components/ui";
import { StreamerVisual } from "@/components/StreamerVisual";
import {
  IconVideo, IconGift, IconChat, IconPlay, IconHeart, IconRocket,
  IconClock, IconGlobe, IconGraduation, IconShield, IconWallet, IconArrow, IconCoin, IconCheck, IconCalendar,
} from "@/components/icons";

const INCOME_ICONS = [IconVideo, IconGift, IconChat, IconPlay, IconHeart, IconRocket];
const STAT_ICONS = [IconCoin, IconWallet, IconCalendar, IconHeart];
const WHY_ICONS = [IconClock, IconGlobe, IconGraduation, IconShield, IconChat, IconWallet, IconCoin];

export default function HomePage() {
  const { t } = useI18n();
  return (
    <>
      {/* HERO */}
      <Section className="!pt-12 sm:!pt-16">
        <div className="grid lg:grid-cols-2 gap-10 items-center">
          <Reveal>
            <span className="eyebrow">{t.common.tagline}</span>
            <h1 className="mt-3 text-3xl sm:text-5xl font-black leading-[1.12] pb-1 h-grad">{t.home.heroTitle}</h1>
            <p className="mt-4 text-slate-300 sm:text-lg max-w-xl">{t.home.heroSubtitle}</p>
            <div className="mt-7 flex flex-wrap gap-3">
              <ApplyButton className="!px-6 !py-3.5 text-base" />
              <Link href="/about" className="btn-ghost !px-6 !py-3.5 text-base">{t.common.learnMore} <IconArrow className="w-4 h-4" /></Link>
            </div>
            <div className="mt-6 flex flex-wrap gap-x-6 gap-y-3">
              {([[IconCheck, t.home.why[0]], [IconGlobe, t.home.why[1]], [IconClock, t.home.why[4]]] as const).map(([Icon, label]) => (
                <span key={label} className="flex items-center gap-2 text-sm font-medium text-slate-300">
                  <Icon className="w-5 h-5 text-neon-400 shrink-0" /> {label}
                </span>
              ))}
            </div>
            <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {t.home.stats.map((s, i) => {
                const Icon = STAT_ICONS[i];
                return <Stat key={i} icon={<Icon className="w-5 h-5" />} big={s.big} small={s.small} />;
              })}
            </div>
          </Reveal>
          <Reveal delay={150}>
            <StreamerVisual />
          </Reveal>
        </div>
      </Section>

      {/* INCOME */}
      <Section id="income">
        <SectionHeading title={t.home.incomeTitle} center />
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {t.home.income.map((it, i) => {
            const Icon = INCOME_ICONS[i % INCOME_ICONS.length];
            return <Reveal key={i} delay={i * 60} className="h-full"><FeatureCard icon={<Icon className="w-5 h-5" />} title={it.title} text={it.text} /></Reveal>;
          })}
        </div>
      </Section>

      {/* WHY */}
      <Section className="!py-10">
        <SectionHeading title={t.home.whyTitle} center />
        <div className="flex flex-wrap justify-center gap-3">
          {t.home.why.map((w, i) => {
            const Icon = WHY_ICONS[i % WHY_ICONS.length];
            return (
              <Reveal key={i} delay={i * 50} className="w-full sm:w-[calc(50%-0.375rem)] lg:w-[calc(25%-0.5625rem)]">
                <div className="card p-4 h-full flex items-center gap-3">
                  <span className="w-9 h-9 rounded-lg grid place-items-center bg-neon-500/15 text-neon-300 shrink-0"><Icon className="w-4 h-4" /></span>
                  <span className="text-sm font-medium text-slate-200">{w}</span>
                </div>
              </Reveal>
            );
          })}
        </div>
      </Section>

      {/* HOW */}
      <Section id="how">
        <SectionHeading title={t.home.howTitle} center />
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {t.home.how.map((step, i) => (
            <Reveal key={i} delay={i * 70}>
              <div className="card p-5 h-full relative">
                <div className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-br from-neon-400 to-brand-500">{i + 1}</div>
                <p className="mt-2 text-sm font-semibold text-slate-200">{step}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      <CtaBand title={t.home.ctaTitle} text={t.home.ctaText} />
    </>
  );
}

function Stat({ icon, big, small }: { icon: React.ReactNode; big: string; small: string }) {
  return (
    <div className="glass rounded-xl2 p-4 h-full flex flex-col items-center text-center gap-2">
      <span className="grid place-items-center w-10 h-10 rounded-xl bg-neon-500/10 text-neon-400 shrink-0">{icon}</span>
      <div className="text-xl font-extrabold text-neon-300 leading-none whitespace-nowrap">{big}</div>
      <div className="text-xs text-slate-400 leading-snug">{small}</div>
    </div>
  );
}
