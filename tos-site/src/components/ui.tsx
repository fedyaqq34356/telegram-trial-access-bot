"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/i18n";
import { IconArrow, IconCheck } from "./icons";

export function Reveal({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setShown(true); io.disconnect(); } }, { threshold: 0.12 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div ref={ref} className={`transition-all duration-700 ease-out ${shown ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"} ${className}`}
         style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

export function Section({ id, children, className = "" }: { id?: string; children: React.ReactNode; className?: string }) {
  return <section id={id} className={`py-14 sm:py-20 ${className}`}><div className="container-x">{children}</div></section>;
}

export function SectionHeading({ eyebrow, title, lead, center }: { eyebrow?: string; title: string; lead?: string; center?: boolean }) {
  return (
    <div className={`max-w-2xl ${center ? "mx-auto text-center" : ""} mb-8 sm:mb-12`}>
      {eyebrow && <div className="eyebrow mb-2">{eyebrow}</div>}
      <h2 className="section-title h-grad">{title}</h2>
      {lead && <p className="mt-3 text-slate-400">{lead}</p>}
    </div>
  );
}

export function ApplyButton({ className = "", label }: { className?: string; label?: string }) {
  const { t } = useI18n();
  return (
    <Link href="/apply" className={`btn-primary ${className}`}>
      {label || t.common.apply} <IconArrow className="w-4 h-4" />
    </Link>
  );
}

export function FeatureCard({ icon, title, text }: { icon?: React.ReactNode; title: string; text: string }) {
  return (
    <div className="card p-5 h-full hover:border-neon-500/30 transition-colors group">
      {icon && (
        <div className="w-11 h-11 rounded-xl grid place-items-center bg-gradient-to-br from-brand-600/40 to-neon-500/30 text-neon-300 mb-3 group-hover:scale-105 transition-transform">
          {icon}
        </div>
      )}
      <h3 className="font-bold">{title}</h3>
      <p className="text-sm text-slate-400 mt-1">{text}</p>
    </div>
  );
}

export function CheckItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-2.5">
      <span className="mt-0.5 w-5 h-5 rounded-full grid place-items-center bg-neon-500/15 text-neon-400 shrink-0"><IconCheck className="w-3.5 h-3.5" /></span>
      <span className="text-slate-300">{children}</span>
    </li>
  );
}

export function CtaBand({ title, text }: { title: string; text: string }) {
  return (
    <Section>
      <Reveal>
        <div className="relative overflow-hidden rounded-xl3 border border-line p-8 sm:p-12 text-center bg-gradient-to-br from-brand-700/40 via-bg-card to-neon-600/25 shadow-glow">
          <div className="absolute -top-24 -right-16 w-72 h-72 bg-neon-500/20 blur-3xl rounded-full animate-pulseGlow" />
          <div className="relative">
            <h2 className="text-2xl sm:text-4xl font-extrabold h-grad">{title}</h2>
            <p className="mt-3 text-slate-300 max-w-xl mx-auto">{text}</p>
            <div className="mt-6 flex justify-center"><ApplyButton className="!px-7 !py-3.5 text-base" /></div>
          </div>
        </div>
      </Reveal>
    </Section>
  );
}
