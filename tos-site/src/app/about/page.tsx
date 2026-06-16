"use client";
import { useI18n } from "@/i18n";
import { Section, SectionHeading, Reveal, FeatureCard, CheckItem, CtaBand } from "@/components/ui";
import { IconVideo, IconGift, IconChat, IconPlay, IconHeart, IconRocket } from "@/components/icons";

const ICONS = [IconVideo, IconGift, IconChat, IconPlay, IconHeart, IconRocket];

export default function AboutPage() {
  const { t } = useI18n();
  return (
    <>
      <Section className="!pt-12">
        <SectionHeading title={t.about.title} lead={t.about.lead} center />
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {t.about.income.map((it, i) => {
            const Icon = ICONS[i % ICONS.length];
            return <Reveal key={i} delay={i * 60}><FeatureCard icon={<Icon className="w-5 h-5" />} title={it.title} text={it.text} /></Reveal>;
          })}
        </div>
      </Section>

      <Section className="!pt-0">
        <Reveal>
          <div className="card p-6 sm:p-8 max-w-2xl mx-auto text-center">
            <h3 className="section-title h-grad text-xl sm:text-2xl">{t.about.needTitle}</h3>
            <ul className="mt-4 space-y-2.5 inline-block text-left">
              {t.about.need.map((n, i) => <CheckItem key={i}>{n}</CheckItem>)}
            </ul>
          </div>
        </Reveal>
      </Section>

      <CtaBand title={t.home.ctaTitle} text={t.home.ctaText} />
    </>
  );
}
