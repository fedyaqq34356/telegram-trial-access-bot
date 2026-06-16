"use client";
import Link from "next/link";
import { useI18n } from "@/i18n";
import { useSiteContent } from "./SiteContent";
import { socialHref } from "@/lib/social";
import { IconTelegram, IconInstagram, IconTiktok, IconWhatsapp, IconDiamond } from "./icons";

export function Footer() {
  const { t } = useI18n();
  const content = useSiteContent();
  const s = content?.social;

  const links: [string, string][] = [
    ["/about", t.nav.about], ["/start", t.nav.start], ["/benefits", t.nav.benefits],
    ["/reviews", t.nav.reviews], ["/faq", t.nav.faq], ["/contacts", t.nav.contacts],
  ];

  return (
    <footer className="border-t border-line mt-10">
      <div className="container-x py-10 grid gap-8 sm:grid-cols-3">
        <div>
          <div className="flex items-center gap-2.5">
            <IconDiamond className="w-7 h-7 text-neon-400 shrink-0" />
            <span className="font-extrabold text-lg tracking-tight">TOS<span className="text-slate-300 font-bold"> AGENCY</span></span>
          </div>
          <p className="text-sm text-slate-400 mt-3">{t.common.tagline}</p>
          <span className="chip mt-3 bg-emerald-500/15 text-emerald-300">● {t.common.online247}</span>
        </div>
        <div className="grid grid-cols-2 gap-1 text-sm">
          {links.map(([href, label]) => (
            <Link key={href} href={href} className="text-slate-400 hover:text-white py-1">{label}</Link>
          ))}
        </div>
        <div>
          <div className="text-sm font-semibold mb-2">{t.nav.contacts}</div>
          <div className="flex gap-2">
            {s?.telegram && <a href={socialHref("telegram", s.telegram)} target="_blank" rel="noreferrer" className="btn-ghost !p-2.5"><IconTelegram className="w-5 h-5" /></a>}
            {s?.whatsapp && <a href={socialHref("whatsapp", s.whatsapp)} target="_blank" rel="noreferrer" className="btn-ghost !p-2.5"><IconWhatsapp className="w-5 h-5" /></a>}
            {s?.instagram && <a href={socialHref("instagram", s.instagram)} target="_blank" rel="noreferrer" className="btn-ghost !p-2.5"><IconInstagram className="w-5 h-5" /></a>}
            {s?.tiktok && <a href={socialHref("tiktok", s.tiktok)} target="_blank" rel="noreferrer" className="btn-ghost !p-2.5"><IconTiktok className="w-5 h-5" /></a>}
          </div>
        </div>
      </div>
      <div className="border-t border-line py-4 text-center text-xs text-slate-500">
        © {new Date().getFullYear()} TOS Agency. HALO recruiting.
      </div>
    </footer>
  );
}
