"use client";
import { useState } from "react";
import { useI18n } from "@/i18n";
import { useSiteContent } from "@/components/SiteContent";
import { Section, SectionHeading, Reveal, CtaBand } from "@/components/ui";
import { IconChevron } from "@/components/icons";

export default function FaqPage() {
  const { t, lang } = useI18n();
  const content = useSiteContent();
  
  const adminFaq = content?.faq?.[lang] ?? [];
  const items = adminFaq.length > 0 ? adminFaq : t.faq.items;
  const [open, setOpen] = useState<number | null>(0);

  return (
    <>
      <Section className="!pt-12">
        <SectionHeading title={t.faq.title} lead={t.faq.lead} center />
        <div className="max-w-2xl mx-auto space-y-2.5">
          {items.map((item, i) => {
            const isOpen = open === i;
            return (
              <Reveal key={i} delay={i * 30}>
                <div className={`card overflow-hidden transition-colors ${isOpen ? "border-neon-500/30" : ""}`}>
                  <button onClick={() => setOpen(isOpen ? null : i)} className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left">
                    <span className="font-semibold text-slate-100">{item.q}</span>
                    <IconChevron className={`w-5 h-5 text-neon-400 shrink-0 transition-transform ${isOpen ? "rotate-180" : ""}`} />
                  </button>
                  <div className={`grid transition-all duration-300 ${isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}>
                    <div className="overflow-hidden">
                      <p className="px-5 pb-4 text-sm text-slate-400">{item.a}</p>
                    </div>
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>
      </Section>
      <CtaBand title={t.home.ctaTitle} text={t.home.ctaText} />
    </>
  );
}
