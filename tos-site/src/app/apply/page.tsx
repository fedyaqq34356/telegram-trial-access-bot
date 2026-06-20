"use client";
import { useState } from "react";
import Link from "next/link";
import { useI18n } from "@/i18n";
import { useSiteContent } from "@/components/SiteContent";
import { Section } from "@/components/ui";
import { submitApplication } from "@/lib/api";
import { IconArrow, IconCheck, IconClose, IconPlay, IconText, IconTelegram, IconWhatsapp } from "@/components/icons";

interface FormState {
  age: string; country: string; contactMethod: "telegram" | "whatsapp"; telegram: string; whatsapp: string; email: string;
  experience: "" | "yes" | "no"; experienceApps: string;
  time: string; photos: File[]; previews: string[];
}

const EMPTY: FormState = { age: "", country: "", contactMethod: "telegram", telegram: "", whatsapp: "", email: "", experience: "", experienceApps: "", time: "", photos: [], previews: [] };

export default function ApplyPage() {
  const { t, lang } = useI18n();
  const a = t.apply;
  const content = useSiteContent();
  const exampleVideo = content?.apply_example_video?.[lang] || content?.apply_example_video?.ru || "";
  const [step, setStep] = useState(1);
  const [f, setF] = useState<FormState>(EMPTY);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [showExample, setShowExample] = useState(false);
  const [website, setWebsite] = useState(""); // honeypot

  const up = (k: keyof FormState, v: any) => setF((s) => ({ ...s, [k]: v }));
  const TOTAL = 5;

  function validate(s: number): string {
    if (s === 1) {
      if (!f.age || Number(f.age) < 16 || Number(f.age) > 40) return a.errAge;
      if (!f.country.trim()) return a.errCountry;
      const contactVal = f.contactMethod === "telegram" ? f.telegram : f.whatsapp;
      if (!contactVal.trim()) return a.errContact;
    }
    if (s === 4) {
      if (f.photos.length < 2 || f.photos.length > 3) return a.errPhotos;
    }
    return "";
  }

  function next() {
    const e = validate(step);
    if (e) { setErr(e); return; }
    setErr(""); setStep((s) => Math.min(TOTAL, s + 1));
  }
  function back() { setErr(""); setStep((s) => Math.max(1, s - 1)); }

  function addPhotos(files: FileList | null) {
    if (!files) return;
    const incoming = Array.from(files).filter((x) => x.type.startsWith("image/"));
    const newPreviews = incoming.map((f) => { try { return URL.createObjectURL(f); } catch { return ""; } });
    setF((s) => {
      const combined = [...s.photos, ...incoming].slice(0, 3);
      const combinedPrev = [...s.previews, ...newPreviews].slice(0, 3);
      return { ...s, photos: combined, previews: combinedPrev };
    });
  }
  function removePhoto(i: number) {
    setF((s) => {
      const prev = s.previews[i];
      if (prev) try { URL.revokeObjectURL(prev); } catch {}
      return { ...s, photos: s.photos.filter((_, j) => j !== i), previews: s.previews.filter((_, j) => j !== i) };
    });
  }

  async function submit() {
    for (const s of [1, 4]) { const e = validate(s); if (e) { setErr(e); setStep(s); return; } }
    setBusy(true); setErr("");
    try {
      const fd = new FormData();
      fd.set("age", f.age);
      fd.set("country", f.country);
      fd.set("contact_telegram", f.contactMethod === "telegram" ? f.telegram : "");
      fd.set("contact_whatsapp", f.contactMethod === "whatsapp" ? f.whatsapp : "");
      fd.set("email", f.email);
      fd.set("experience", f.experience === "yes" ? "true" : "false");
      fd.set("experience_apps", f.experience === "yes" ? f.experienceApps : "");
      fd.set("time_commitment", f.time);
      fd.set("website", website);
      f.photos.forEach((p) => fd.append("photos", p));
      await submitApplication(fd);
      setDone(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка отправки");
    } finally { setBusy(false); }
  }

  if (done) return (
    <Section className="!pt-16">
      <div className="max-w-md mx-auto text-center card p-8">
        <span className="w-16 h-16 rounded-full grid place-items-center bg-emerald-500/15 text-emerald-300 mx-auto mb-4"><IconCheck className="w-8 h-8" /></span>
        <h1 className="text-2xl font-extrabold h-grad">{a.successTitle}</h1>
        <p className="text-slate-300 mt-3">{a.successText}</p>
        <div className="mt-6 flex flex-col gap-2">
          <Link href="/" className="text-sm text-slate-500 hover:text-white">← {t.nav.home}</Link>
        </div>
      </div>
    </Section>
  );

  const titles = [a.s1Title, a.s2Title, a.s3Title, a.s4Title, a.s5Title];

  return (
    <Section className="!pt-12">
      <div className="max-w-xl mx-auto">
        <div className="mb-2 text-center"><span className="eyebrow">{a.title}</span></div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-center h-grad">{titles[step - 1]}</h1>
        <p className="text-center text-slate-500 text-sm mt-1">{a.step} {step} {a.of} {TOTAL}</p>

        {/* progress */}
        <div className="flex gap-1.5 mt-4 mb-6">
          {Array.from({ length: TOTAL }).map((_, i) => (
            <div key={i} className={`h-1.5 flex-1 rounded-full transition-colors ${i < step ? "bg-gradient-to-r from-neon-500 to-brand-500" : "bg-white/10"}`} />
          ))}
        </div>

        {/* honeypot (скрыт) */}
        <input type="text" value={website} onChange={(e) => setWebsite(e.target.value)} tabIndex={-1} autoComplete="off"
               className="absolute -left-[9999px] w-0 h-0" aria-hidden />

        <div className="card p-6 text-center">
          {step === 1 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Field label={a.age}><input className="input text-center" type="number" min={16} max={40} value={f.age} onChange={(e) => up("age", e.target.value)} /></Field>
                <Field label={a.country}><input className="input text-center" value={f.country} onChange={(e) => up("country", e.target.value)} /></Field>
              </div>

              <div>
                <label className="label">{a.chooseContact}</label>
                <div className="grid grid-cols-2 gap-3">
                  <ContactToggle active={f.contactMethod === "telegram"} onClick={() => { up("contactMethod", "telegram"); up("whatsapp", ""); }}
                                 icon={<IconTelegram className="w-5 h-5" />} label={a.contactTg} />
                  <ContactToggle active={f.contactMethod === "whatsapp"} onClick={() => { up("contactMethod", "whatsapp"); up("telegram", ""); }}
                                 icon={<IconWhatsapp className="w-5 h-5" />} label={a.contactWa} />
                </div>
              </div>

              {f.contactMethod === "telegram" ? (
                <Field label={a.contactTg}><input className="input text-center" placeholder="@username" value={f.telegram} onChange={(e) => up("telegram", e.target.value)} /></Field>
              ) : (
                <Field label={a.contactWa}><input className="input text-center" placeholder="+38…" value={f.whatsapp} onChange={(e) => up("whatsapp", e.target.value)} /></Field>
              )}

              <Field label={`${a.email} · ${a.optional}`}><input className="input text-center" type="email" placeholder="example@gmail.com" value={f.email} onChange={(e) => up("email", e.target.value)} /></Field>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <p className="font-medium">{a.expQ}</p>
              <div className="grid grid-cols-2 gap-3">
                <Choice active={f.experience === "yes"} onClick={() => up("experience", "yes")}>{a.expYes}</Choice>
                <Choice active={f.experience === "no"} onClick={() => up("experience", "no")}>{a.expNo}</Choice>
              </div>
              {f.experience === "yes" && (
                <Field label={a.expWhich}><input className="input" value={f.experienceApps} onChange={(e) => up("experienceApps", e.target.value)} /></Field>
              )}
              {f.experience === "no" && (
                <div className="rounded-xl border border-line bg-black/30 p-4">
                  <p className="text-sm text-slate-300">{a.noExpText}</p>
                  <button onClick={() => setShowExample(true)} className="btn-ghost mt-3 !py-2 text-sm"><IconPlay className="w-4 h-4" /> {a.seeExample}</button>
                </div>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3">
              <p className="font-medium">{a.timeQ}</p>
              <div className="chip bg-neon-500/15 text-neon-300">{a.timeHint}</div>
              <input className="input" placeholder={a.timePlaceholder} value={f.time} onChange={(e) => up("time", e.target.value)} />
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <p className="font-medium">{a.photoReqTitle}</p>
              <ul className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm text-slate-300">
                {a.photoReqs.map((r, i) => <li key={i} className="flex items-center justify-center gap-1.5"><IconCheck className="w-3.5 h-3.5 text-neon-400 shrink-0" /> {r}</li>)}
              </ul>
              <div className="flex flex-wrap justify-center gap-3">
                {f.photos.map((_, i) => (
                  <div key={i} className="relative w-24 h-24 rounded-xl overflow-hidden border border-line">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    {f.previews[i] && <img src={f.previews[i]} alt="" className="w-full h-full object-cover" />}
                    <button onClick={() => removePhoto(i)} className="absolute top-1 right-1 w-6 h-6 rounded-full bg-black/70 grid place-items-center text-white"><IconClose className="w-3.5 h-3.5" /></button>
                  </div>
                ))}
                {f.photos.length < 3 && (
                  <label className="w-24 h-24 rounded-xl border border-dashed border-line grid place-items-center cursor-pointer text-slate-400 hover:border-neon-500/50 hover:text-neon-300 text-center text-xs px-1">
                    + {a.addPhoto}
                    <input type="file" accept="image/*" multiple className="hidden" onChange={(e) => addPhotos(e.target.files)} />
                  </label>
                )}
              </div>
              <p className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2">{a.aiWarning}</p>
              <p className="text-xs text-slate-500">{a.photoCount}: {f.photos.length} / 3</p>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-400">{a.confirmHint}</p>
              <dl className="divide-y divide-line text-sm">
                <Row k={a.age} v={f.age} />
                <Row k={a.country} v={f.country} />
                {f.telegram && <Row k={a.contactTg} v={f.telegram} />}
                {f.whatsapp && <Row k={a.contactWa} v={f.whatsapp} />}
                {f.email && <Row k={a.email} v={f.email} />}
                <Row k={a.experience} v={f.experience === "yes" ? (f.experienceApps ? `${a.yes} (${f.experienceApps})` : a.yes) : a.no} />
                <Row k={a.time} v={f.time || "—"} />
                <Row k={a.photos} v={`${f.photos.length}`} />
              </dl>
            </div>
          )}

          {err && <div className="mt-4 text-sm text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2">{err}</div>}

          <div className="mt-6 flex items-center justify-between gap-3">
            <button onClick={back} disabled={step === 1} className="btn-ghost !py-2.5 disabled:opacity-40">{t.common.back}</button>
            {step < TOTAL ? (
              <button onClick={next} className="btn-primary !py-2.5">{t.common.next} <IconArrow className="w-4 h-4" /></button>
            ) : (
              <button onClick={submit} disabled={busy} className="btn-primary !py-2.5">{busy ? a.sending : a.submit}</button>
            )}
          </div>
        </div>
      </div>

      {showExample && (
        <div className="fixed inset-0 z-50 grid place-items-center p-4 bg-black/70 backdrop-blur-sm" onClick={() => setShowExample(false)}>
          <div className="card max-w-md w-full p-6 text-center" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold">{a.exampleTitle}</h3>
              <button onClick={() => setShowExample(false)} className="text-slate-400 hover:text-white"><IconClose /></button>
            </div>
            {exampleVideo ? (
              <video controls autoPlay preload="metadata" className="w-full rounded-xl border border-line bg-black max-h-[60vh]" src={exampleVideo} />
            ) : (
              <div className="rounded-xl border border-line bg-black/30 p-8 text-slate-400 grid place-items-center min-h-[200px]">
                <IconText className="w-10 h-10 mb-2 text-slate-600" />
                <p className="text-sm">{a.exampleSoon}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </Section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div><label className="label">{label}</label>{children}</div>;
}
function ContactToggle({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button type="button" onClick={onClick}
            className={`rounded-xl border px-4 py-3 flex items-center justify-center gap-2 text-sm font-semibold transition-colors ${active ? "border-neon-500 bg-neon-500/15 text-white" : "border-line bg-black/30 text-slate-300 hover:border-neon-500/40"}`}>
      <span className={active ? "text-neon-300" : "text-slate-400"}>{icon}</span> {label}
    </button>
  );
}
function Choice({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} className={`rounded-xl border px-4 py-3 text-sm font-medium transition-colors ${active ? "border-neon-500 bg-neon-500/15 text-white" : "border-line bg-black/30 text-slate-300 hover:border-neon-500/40"}`}>
      {children}
    </button>
  );
}
function Row({ k, v }: { k: string; v: string }) {
  return <div className="flex items-center justify-between py-2"><dt className="text-slate-500">{k}</dt><dd className="font-medium text-right">{v}</dd></div>;
}
