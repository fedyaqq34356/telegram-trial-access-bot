"use client";
import { useI18n } from "@/i18n";
import { useSiteContent } from "@/components/SiteContent";
import { Section, SectionHeading, Reveal } from "@/components/ui";
import { socialHref } from "@/lib/social";
import { IconTelegram, IconInstagram, IconTiktok, IconWhatsapp, IconArrow } from "@/components/icons";

export default function ContactsPage() {
  const { t } = useI18n();
  const content = useSiteContent();
  const s = content?.social;

  const cards = [
    s?.telegram && { kind: "telegram" as const, label: t.contacts.telegram, value: s.telegram, icon: <IconTelegram className="w-6 h-6" /> },
    s?.whatsapp && { kind: "whatsapp" as const, label: t.contacts.whatsapp, value: s.whatsapp, icon: <IconWhatsapp className="w-6 h-6" /> },
    s?.instagram && { kind: "instagram" as const, label: t.contacts.instagram, value: s.instagram, icon: <IconInstagram className="w-6 h-6" /> },
    s?.tiktok && { kind: "tiktok" as const, label: t.contacts.tiktok, value: s.tiktok, icon: <IconTiktok className="w-6 h-6" /> },
  ].filter(Boolean) as { kind: "telegram" | "instagram" | "tiktok" | "whatsapp"; label: string; value: string; icon: React.ReactNode }[];

  return (
    <Section className="!pt-12">
      <SectionHeading title={t.contacts.title} lead={t.contacts.lead} center />

      <div className="max-w-2xl mx-auto">
        <div className="flex flex-wrap justify-center gap-3">
          {cards.length === 0 && <div className="text-center text-slate-500 w-full">—</div>}
          {cards.map((c) => (
            <a key={c.kind} href={socialHref(c.kind, c.value)} target="_blank" rel="noreferrer"
               className="card p-5 w-full sm:w-[calc(50%-0.375rem)] lg:w-44 flex flex-col items-center gap-2 hover:border-neon-500/40 transition-colors text-center">
              <span className="w-12 h-12 rounded-xl grid place-items-center bg-gradient-to-br from-brand-600/40 to-neon-500/30 text-neon-300">{c.icon}</span>
              <span className="font-semibold">{c.label}</span>
            </a>
          ))}
        </div>

        {(s?.telegram || s?.whatsapp) && (
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            {s?.telegram && (
              <a href={socialHref("telegram", s.telegram)} target="_blank" rel="noreferrer" className="btn-primary !px-7 !py-3.5 text-base">
                {t.contacts.writeTg} <IconArrow className="w-4 h-4" />
              </a>
            )}
            {s?.whatsapp && (
              <a href={socialHref("whatsapp", s.whatsapp)} target="_blank" rel="noreferrer"
                 className="btn-ghost !px-7 !py-3.5 text-base !border-emerald-500/40 text-emerald-300 hover:!bg-emerald-500/10">
                {t.contacts.writeWa} <IconWhatsapp className="w-4 h-4" />
              </a>
            )}
          </div>
        )}

        <Reveal>
          <div className="mt-8 rounded-xl3 border border-line p-6 text-center bg-gradient-to-br from-emerald-600/15 to-bg-card">
            <span className="chip bg-emerald-500/15 text-emerald-300 mb-2">● online</span>
            <div className="text-xl font-extrabold">{t.contacts.online247}</div>
          </div>
        </Reveal>
      </div>
    </Section>
  );
}
