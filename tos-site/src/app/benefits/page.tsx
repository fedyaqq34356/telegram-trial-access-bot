"use client";
import { useI18n } from "@/i18n";
import { Section, SectionHeading, Reveal, FeatureCard, CtaBand } from "@/components/ui";
import { IconClock, IconGlobe, IconGraduation, IconShield, IconChat, IconWallet, IconCoin, IconRocket } from "@/components/icons";

const ICONS = [IconClock, IconGlobe, IconGraduation, IconShield, IconChat, IconWallet, IconCoin, IconRocket];

export default function BenefitsPage() {
  const { t } = useI18n();
  return (
    <>
      <Section className="!pt-12">
        <SectionHeading title={t.benefits.title} lead={t.benefits.lead} center />
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {t.benefits.items.map((it, i) => {
            const Icon = ICONS[i % ICONS.length];
            return <Reveal key={i} delay={i * 50} className="h-full"><FeatureCard icon={<Icon className="w-5 h-5" />} title={it.title} text={it.text} /></Reveal>;
          })}
        </div>
      </Section>
      <CtaBand title={t.home.ctaTitle} text={t.home.ctaText} />
    </>
  );
}
