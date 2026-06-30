"use client";
import Link from "next/link";
import { useI18n } from "@/i18n";
import { useSiteContent } from "@/components/SiteContent";
import { Section, Reveal } from "@/components/ui";
import { socialHref } from "@/lib/social";
import { Callouts } from "@/components/Callouts";
import { Gallery } from "@/components/Gallery";
import { IconCheck, IconArrow, IconDownload, IconTelegram, IconWhatsapp, IconShield } from "@/components/icons";

export default function InstructionPage() {
  const { t, lang } = useI18n();
  const content = useSiteContent();
  const ins = t.instruction;
  const steps = content?.instruction?.[lang] ?? [];
  const important = content?.instruction_important?.[lang] ?? [];
  const social = content?.social;

  return (
    <Section className="!pt-12">
      {}
      <div className="text-center max-w-3xl mx-auto mb-8">
        <span className="eyebrow">{ins.eyebrow}</span>
        <h1 className="mt-3 text-3xl sm:text-5xl font-black leading-[1.15] pb-1 h-grad">{ins.title}</h1>
        <p className="mt-3 text-slate-300 sm:text-lg">{ins.lead}</p>
      </div>

      {}
      {steps.length === 0 ? (
        <div className="text-center text-slate-500">{ins.empty}</div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 grid-flow-row-dense">
          {steps.map((s, i) => {
            const galCount = (s.gallery || []).filter((g) => g?.image).length;
            const span = galCount >= 3 ? "sm:col-span-2 lg:col-span-2" : galCount === 2 ? "lg:col-span-2" : "";
            return (
            <Reveal key={i} delay={i * 50} className={`h-full ${span}`}>
              <div className="card p-5 h-full flex flex-col">
                <div className="flex items-center gap-3 mb-3">
                  <span className="w-8 h-8 rounded-full grid place-items-center text-sm font-black text-white bg-gradient-to-br from-neon-500 to-brand-600 shrink-0">{i + 1}</span>
                  <h3 className="font-bold leading-tight">{s.title || "—"}</h3>
                </div>
                {s.body && <p className="text-sm text-slate-300 whitespace-pre-line">{s.body}</p>}
                {s.image && (
                  
                  <img src={s.image} alt="" className="mt-3 mx-auto w-auto max-w-full max-h-80 rounded-xl border border-line" />
                )}
                <Gallery items={s.gallery} className="mt-3" />
                {s.items && s.items.length > 0 && (
                  <div className="mt-3">
                    <div className="text-[11px] font-bold uppercase tracking-wide text-neon-300 mb-1.5">{t.training.checklistLabel}</div>
                    <ul className="space-y-1.5">
                      {s.items.map((it, k) => (
                        <li key={k} className="flex items-start gap-2 text-sm text-slate-300">
                          <span className="mt-0.5 w-4 h-4 rounded-full grid place-items-center bg-neon-500/15 text-neon-400 shrink-0"><IconCheck className="w-3 h-3" /></span>{it}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <Callouts items={s.callouts} className="mt-3" />
              </div>
            </Reveal>
            );
          })}
        </div>
      )}

      {}
      {important.length > 0 && (
        <Reveal>
          <div className="mt-8 rounded-xl3 border border-neon-500/30 bg-gradient-to-br from-brand-700/20 to-neon-600/10 p-6">
            <div className="flex items-center gap-2.5 mb-4">
              <span className="w-8 h-8 rounded-lg grid place-items-center bg-neon-500/15 text-neon-300"><IconShield className="w-5 h-5" /></span>
              <h3 className="font-extrabold text-lg">{ins.importantTitle}</h3>
            </div>
            <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-2.5">
              {important.map((it, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-neon-400 shrink-0" />{it}
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      )}

      {}
      <div className="mt-8 text-center">
        <h3 className="font-extrabold text-lg mb-4">✦ {ins.linksTitle} ✦</h3>
        <div className="grid sm:grid-cols-3 gap-3 max-w-4xl mx-auto">
          <LinkCard href="/download" internal icon={<IconDownload className="w-5 h-5" />} title={ins.dlTitle} sub={ins.dlSub} />
          {social?.telegram && (
            <LinkCard href={socialHref("telegram", social.telegram)} icon={<IconTelegram className="w-5 h-5" />} title={ins.tgTitle} sub={ins.tgSub} />
          )}
          {social?.whatsapp && (
            <LinkCard href={socialHref("whatsapp", social.whatsapp)} icon={<IconWhatsapp className="w-5 h-5" />} title={ins.waTitle} sub={ins.waSub} />
          )}
        </div>
      </div>
    </Section>
  );
}

function LinkCard({ href, internal, icon, title, sub }: { href: string; internal?: boolean; icon: React.ReactNode; title: string; sub: string }) {
  const inner = (
    <>
      <span className="w-11 h-11 rounded-xl grid place-items-center bg-gradient-to-br from-brand-600/40 to-neon-500/30 text-neon-300 shrink-0">{icon}</span>
      <span className="text-left flex-1 min-w-0">
        <span className="block font-semibold truncate">{title}</span>
        <span className="block text-xs text-slate-400 truncate">{sub}</span>
      </span>
      <IconArrow className="w-4 h-4 text-slate-400 shrink-0" />
    </>
  );
  const cls = "card p-4 flex items-center gap-3 hover:border-neon-500/40 transition-colors";
  return internal
    ? <Link href={href} className={cls}>{inner}</Link>
    : <a href={href} target="_blank" rel="noreferrer" className={cls}>{inner}</a>;
}
