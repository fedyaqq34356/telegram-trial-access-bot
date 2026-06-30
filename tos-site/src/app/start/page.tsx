"use client";
import { useI18n } from "@/i18n";
import { Section, SectionHeading, Reveal, CheckItem, CtaBand } from "@/components/ui";
import { IconCalendar, IconStar, IconShield, IconWallet, IconChat, IconGlobe, IconText, IconGraduation, IconRocket, IconThumbUp, IconThumbDown, IconTelegram, IconMonitor } from "@/components/icons";

const WHERE_ICONS = [IconMonitor, IconTelegram];

const STEP_ICONS = [IconText, IconShield, IconCalendar, IconGraduation, IconRocket];

export default function StartPage() {
  const { t } = useI18n();
  const s = t.start;
  return (
    <>
      {}
      <Section className="!pt-12">
        <SectionHeading title={s.title} lead={s.lead} center />
        <div className="grid gap-3">
          {s.steps.map((st, i) => {
            const Icon = STEP_ICONS[i % STEP_ICONS.length];
            return (
            <Reveal key={i} delay={i * 60}>
              <div className="card p-5 flex gap-4 items-center">
                <div className="w-10 h-10 rounded-xl grid place-items-center font-black text-white bg-gradient-to-br from-neon-500 to-brand-600 shrink-0">{i + 1}</div>
                <div className="flex-1">
                  <h3 className="font-bold">{st.title}</h3>
                  <p className="text-sm text-slate-400 mt-0.5">{st.text}</p>
                </div>
                <Icon className="w-8 h-8 text-neon-400 shrink-0" />
              </div>
            </Reveal>
            );
          })}
        </div>
      </Section>

      {}
      <Section className="!py-8">
        <Reveal>
          <div className="rounded-xl3 border border-line p-6 sm:p-8 bg-gradient-to-br from-brand-700/30 to-neon-600/20 shadow-glow flex flex-col items-center text-center gap-3">
            <span className="w-12 h-12 rounded-xl grid place-items-center bg-white/10 text-neon-300"><IconCalendar className="w-6 h-6" /></span>
            <div>
              <h3 className="text-xl font-extrabold">{s.testWeekTitle}</h3>
              <p className="text-slate-300 text-sm mt-1">{s.testWeekText}</p>
            </div>
          </div>
        </Reveal>
      </Section>

      {}
      <Section className="!pt-0">
        <div className="grid lg:grid-cols-3 gap-4">
          <Reveal>
            <ResultCard color="emerald" icon={<IconStar className="w-5 h-5" />} title={s.successTitle}
                        condTitle="Условия" cond={s.successCond} resTitle="Результат" res={s.successResult} />
          </Reveal>
          <Reveal delay={80}>
            <ResultCard color="amber" icon={<IconWallet className="w-5 h-5" />} title={s.minimalTitle}
                        condTitle="Условия" cond={s.minimalCond} resTitle="Результат" res={s.minimalResult} />
          </Reveal>
          <Reveal delay={160}>
            <div className="card p-5 h-full border-rose-500/30">
              <div className="flex items-center gap-2.5 mb-3">
                <span className="w-9 h-9 rounded-lg grid place-items-center bg-rose-500/15 text-rose-300"><IconShield className="w-5 h-5" /></span>
                <h3 className="font-bold">{s.riskTitle}</h3>
              </div>
              <p className="text-sm text-slate-300">{s.riskText}</p>
              <ul className="mt-3 space-y-2 text-sm">
                {s.riskNotes.map((n, i) => <li key={i} className="text-slate-400">• {n}</li>)}
              </ul>
            </div>
          </Reveal>
        </div>
      </Section>

      {}
      <Section className="!pt-0">
        <Reveal>
          <div className="card p-6 sm:p-8 max-w-2xl mx-auto text-center">
            <div className="flex items-center justify-center gap-2.5 mb-3">
              <span className="w-9 h-9 rounded-lg grid place-items-center bg-neon-500/15 text-neon-300"><IconWallet className="w-5 h-5" /></span>
              <h3 className="font-bold text-lg">{s.withdrawTitle}</h3>
            </div>
            <p className="text-sm text-slate-300 mb-3">{s.withdrawText}</p>
            <ul className="space-y-2.5 inline-block text-left">{s.withdrawCond.map((c, i) => <CheckItem key={i}>{c}</CheckItem>)}</ul>
            <p className="mt-4 text-sm text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2">{s.withdrawDenied}</p>
          </div>
        </Reveal>
      </Section>

      {}
      <Section className="!pt-0">
        <div className="grid lg:grid-cols-2 gap-4">
          <Reveal>
            <div className="card p-6 h-full">
              <div className="flex items-center gap-2.5 mb-3">
                <span className="w-9 h-9 rounded-lg grid place-items-center bg-brand-600/30 text-brand-200"><IconChat className="w-5 h-5" /></span>
                <h3 className="font-bold text-lg">{s.coefTitle}</h3>
              </div>
              <div className="space-y-2 text-sm text-slate-300">
                {s.coefText.map((p, i) => <p key={i}>{p}</p>)}
              </div>
              <div className="mt-4 flex gap-3">
                <span className="grid place-items-center w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 shadow-[0_0_20px_-4px_rgba(16,185,129,0.7)]">
                  <IconThumbUp className="w-5 h-5" />
                </span>
                <span className="grid place-items-center w-11 h-11 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 shadow-[0_0_20px_-4px_rgba(244,63,94,0.7)]">
                  <IconThumbDown className="w-5 h-5" />
                </span>
              </div>
            </div>
          </Reveal>
          <Reveal delay={80}>
            <div className="card p-6 h-full">
              <div className="flex items-center gap-2.5 mb-3">
                <span className="w-9 h-9 rounded-lg grid place-items-center bg-neon-500/15 text-neon-300"><IconGlobe className="w-5 h-5" /></span>
                <h3 className="font-bold text-lg">{s.whereTitle}</h3>
              </div>
              <ul className="space-y-3">{s.where.map((w, i) => {
                const Icon = WHERE_ICONS[i % WHERE_ICONS.length];
                return (
                  <li key={i} className="flex items-center gap-3">
                    <span className="w-9 h-9 rounded-lg grid place-items-center bg-brand-600/25 text-neon-300 shrink-0"><Icon className="w-5 h-5" /></span>
                    <span className="text-slate-300">{w}</span>
                  </li>
                );
              })}</ul>
            </div>
          </Reveal>
        </div>
      </Section>

      <CtaBand title={t.home.ctaTitle} text={t.home.ctaText} />
    </>
  );
}

function ResultCard({ color, icon, title, condTitle, cond, resTitle, res }: {
  color: "emerald" | "amber"; icon: React.ReactNode; title: string;
  condTitle: string; cond: string[]; resTitle: string; res: string[];
}) {
  const ring = color === "emerald" ? "border-emerald-500/30" : "border-amber-500/30";
  const chip = color === "emerald" ? "bg-emerald-500/15 text-emerald-300" : "bg-amber-500/15 text-amber-300";
  return (
    <div className={`card p-5 h-full ${ring}`}>
      <div className="flex items-center gap-2.5 mb-3">
        <span className={`w-9 h-9 rounded-lg grid place-items-center ${chip}`}>{icon}</span>
        <h3 className="font-bold">{title}</h3>
      </div>
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">{condTitle}</div>
      <ul className="space-y-1.5 text-sm text-slate-300 mb-3">{cond.map((c, i) => <li key={i}>• {c}</li>)}</ul>
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">{resTitle}</div>
      <ul className="space-y-1.5 text-sm text-slate-300">{res.map((c, i) => <li key={i} className="flex gap-1.5"><span className={color === "emerald" ? "text-emerald-400" : "text-amber-400"}>✓</span> {c}</li>)}</ul>
    </div>
  );
}
