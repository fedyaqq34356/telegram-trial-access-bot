"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n, LANGS, type Lang } from "@/i18n";
import { IconMenu, IconClose, IconArrow, IconDiamond } from "./icons";

export function Header() {
  const { t, lang, setLang } = useI18n();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const nav: [string, string][] = [
    ["/", t.nav.home], ["/about", t.nav.about], ["/start", t.nav.start],
    ["/benefits", t.nav.benefits], ["/reviews", t.nav.reviews],
    ["/training", t.nav.training], ["/download", t.nav.download], ["/faq", t.nav.faq], ["/contacts", t.nav.contacts],
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-bg/70 backdrop-blur-xl">
      <div className="container-x flex items-center gap-4 h-16">
        <Link href="/" className="flex items-center gap-2.5">
          <IconDiamond className="w-8 h-8 text-neon-400 shrink-0" />
          <span className="text-lg font-extrabold tracking-tight">TOS<span className="text-slate-300 font-bold"> AGENCY</span></span>
        </Link>

        <nav className="hidden lg:flex items-center gap-1 ml-4">
          {nav.map(([href, label]) => {
            const active = pathname === href;
            return (
              <Link key={href} href={href}
                    className={`px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${active ? "text-white bg-white/5" : "text-slate-400 hover:text-white"}`}>
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <LangSwitcher lang={lang} setLang={setLang} />
          <Link href="/apply" className="btn-primary hidden sm:inline-flex !px-3.5 !py-1.5 text-xs">
            {t.common.apply} <IconArrow className="w-3.5 h-3.5" />
          </Link>
          <button className="lg:hidden text-slate-300" onClick={() => setOpen((o) => !o)} aria-label="menu">
            {open ? <IconClose /> : <IconMenu />}
          </button>
        </div>
      </div>

      {open && (
        <div className="lg:hidden border-t border-line bg-bg-soft/95 backdrop-blur-xl">
          <div className="container-x py-3 grid gap-1">
            {nav.map(([href, label]) => (
              <Link key={href} href={href} onClick={() => setOpen(false)}
                    className="px-3 py-2.5 rounded-lg text-sm font-medium text-slate-300 hover:bg-white/5">{label}</Link>
            ))}
            <Link href="/apply" onClick={() => setOpen(false)} className="btn-primary mt-2 justify-center">{t.common.apply}</Link>
          </div>
        </div>
      )}
    </header>
  );
}

function LangSwitcher({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  return (
    <div className="flex items-center rounded-lg border border-line bg-black/30 p-0.5 text-xs font-bold">
      {LANGS.map((l) => (
        <button key={l} onClick={() => setLang(l)}
                className={`px-2 py-1 rounded-md uppercase transition-colors ${lang === l ? "bg-gradient-to-r from-neon-500 to-brand-600 text-white" : "text-slate-400 hover:text-white"}`}>
          {l}
        </button>
      ))}
    </div>
  );
}
