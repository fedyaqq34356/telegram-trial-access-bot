"use client";
import { useState, useEffect } from "react";
import { useI18n } from "@/i18n";
import { Section, SectionHeading } from "@/components/ui";
import { Callouts } from "@/components/Callouts";
import { Gallery } from "@/components/Gallery";
import { trainingLogin, checkCoefficient, reportProgress, type Lesson, type TrainingData, type CoefficientResult } from "@/lib/api";
import { IconLock, IconCheck, IconArrow, IconShield, IconGraduation, IconRocket, IconClock } from "@/components/icons";

type View = "menu" | "check" | "choose" | "lessons";

export default function TrainingPage() {
  const { t, lang } = useI18n();
  const [password, setPassword] = useState("");
  const [appId, setAppId] = useState("");
  const [data, setData] = useState<TrainingData | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [view, setView] = useState<View>("menu");
  const [kind, setKind] = useState<"quick" | "full">("quick");

  async function login(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      setData(await trainingLogin(password, appId));
      setView("menu");
    } catch (e) {
      setErr(e instanceof Error ? e.message : t.training.wrong);
    } finally { setBusy(false); }
  }

  if (!data) return (
    <Section className="!pt-14">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-6">
          <span className="w-14 h-14 rounded-2xl grid place-items-center bg-gradient-to-br from-neon-500 to-brand-600 text-white mx-auto shadow-neon"><IconLock className="w-7 h-7" /></span>
          <h1 className="section-title h-grad mt-4">{t.training.title}</h1>
          <p className="text-slate-400 mt-2 text-sm">{t.training.lead}</p>
        </div>
        <form onSubmit={login} className="card p-6 space-y-4">
          <div>
            <label className="label">{t.training.appId}</label>
            <input className="input" value={appId} onChange={(e) => setAppId(e.target.value)} placeholder="ID HALO" />
          </div>
          <div>
            <label className="label">{t.training.password}</label>
            <input type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••" />
          </div>
          {err && <div className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2">{err}</div>}
          <button className="btn-primary w-full justify-center" disabled={busy || !password}>
            {busy ? "…" : <>{t.training.login} <IconArrow className="w-4 h-4" /></>}
          </button>
          <p className="text-xs text-slate-500 text-center">{t.training.note}</p>
        </form>
      </div>
    </Section>
  );

  return (
    <Section className="!pt-12">
      <div className="max-w-4xl mx-auto">
        {view === "menu" && <Menu onCheck={() => setView("check")} onTrain={() => setView("choose")} />}
        {view === "check" && <CheckView password={password} appId={appId} onBack={() => setView("menu")} />}
        {view === "choose" && (
          <ChooseTraining
            onBack={() => setView("menu")}
            onPick={(k) => { setKind(k); setView("lessons"); }}
          />
        )}
        {view === "lessons" && (
          <LessonWizard
            steps={(kind === "quick" ? data.lessons_quick[lang] : data.lessons_full[lang]) || []}
            kind={kind} password={password} haloId={appId} onBack={() => setView("choose")}
          />
        )}
      </div>
    </Section>
  );
}

function Menu({ onCheck, onTrain }: { onCheck: () => void; onTrain: () => void }) {
  const { t } = useI18n();
  return (
    <div>
      <div className="text-center mb-8">
        <span className="w-14 h-14 rounded-2xl grid place-items-center bg-gradient-to-br from-neon-500 to-brand-600 text-white mx-auto shadow-neon"><IconGraduation className="w-7 h-7" /></span>
        <h1 className="section-title h-grad mt-4">{t.training.title}</h1>
        <p className="text-slate-400 mt-2 text-sm">{t.training.lead}</p>
      </div>
      <div className="grid sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
        <MenuCard icon={<IconShield className="w-6 h-6" />} title={t.training.menuCheck} desc={t.training.menuCheckDesc} btn={t.training.menuCheckBtn} onClick={onCheck} />
        <MenuCard icon={<IconGraduation className="w-6 h-6" />} title={t.training.menuTrain} desc={t.training.menuTrainDesc} btn={t.training.menuTrainBtn} onClick={onTrain} />
      </div>
    </div>
  );
}

function MenuCard({ icon, title, desc, btn, onClick }: { icon: React.ReactNode; title: string; desc: string; btn: string; onClick: () => void }) {
  return (
    <div className="card p-6 flex flex-col">
      <span className="w-12 h-12 rounded-xl grid place-items-center bg-gradient-to-br from-brand-600/40 to-neon-500/30 text-neon-300 mb-3">{icon}</span>
      <h3 className="font-bold text-lg">{title}</h3>
      <p className="text-sm text-slate-400 mt-1 flex-1">{desc}</p>
      <button onClick={onClick} className="btn-primary justify-center mt-4">{btn}</button>
    </div>
  );
}

function BackBtn({ onBack }: { onBack: () => void }) {
  const { t } = useI18n();
  return <button onClick={onBack} className="btn-ghost !py-2 !px-3 text-sm mb-4"><IconArrow className="w-4 h-4 rotate-180" /> {t.training.back}</button>;
}

function CheckView({ password, appId, onBack }: { password: string; appId: string; onBack: () => void }) {
  const { t } = useI18n();
  const [haloId, setHaloId] = useState(appId || "");
  const [res, setRes] = useState<CoefficientResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function run() {
    setBusy(true); setErr("");
    try { setRes(await checkCoefficient(password, haloId.trim())); }
    catch (e) { setErr(e instanceof Error ? e.message : "Ошибка"); setRes(null); }
    finally { setBusy(false); }
  }

  
  const profileRisk = res ? !res.profile_ok : false;
  const monthlyRisk = res ? !res.monthly_ok : false;
  const hasRisk = profileRisk || monthlyRisk;
  const color = hasRisk ? "rose" : "emerald";
  const statusLabel = hasRisk ? t.training.statusDanger : t.training.statusSafe;
  const punish = res ? (t.training.punishment[res.grade] || "") : "";

  return (
    <div>
      <BackBtn onBack={onBack} />
      <div className="text-center mb-6">
        <h1 className="section-title h-grad">{t.training.checkTitle}</h1>
        <p className="text-slate-400 mt-1 text-sm">{t.training.checkSub}</p>
      </div>

      <div className="card p-5 max-w-xl mx-auto flex flex-col sm:flex-row gap-3 sm:items-end">
        <div className="flex-1">
          <label className="label">{t.training.checkIdLabel}</label>
          <input className="input" value={haloId} onChange={(e) => setHaloId(e.target.value)} placeholder="123456789" inputMode="numeric" />
        </div>
        <button className="btn-primary justify-center sm:w-auto" disabled={busy || !haloId.trim()} onClick={run}>{busy ? "…" : t.training.checkBtn}</button>
      </div>
      {err && <div className="max-w-xl mx-auto mt-3 text-sm text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2">{err}</div>}

      {res && (
        <div className="grid lg:grid-cols-2 gap-4 mt-6">
          {}
          <div className="card p-6 flex flex-col items-center justify-center text-center">
            <Gauge value={res.real_down_rate} color={color} />
            <div className="font-bold mt-3">{t.training.coefLabel}</div>
            <span className={`chip mt-2 ${hasRisk ? "bg-rose-500/15 text-rose-300" : "bg-emerald-500/15 text-emerald-300"}`}>{statusLabel}</span>
          </div>
          {}
          <div className="card p-5">
            <DRow k={t.training.botId} v={res.id} />
            {res.ranking != null && <DRow k={t.training.dRank} v={`${res.ranking} ${t.training.rankUnit}`} />}
            {res.agency && <DRow k={t.training.dAgency} v={res.agency} />}
            <DRow k={t.training.dLevel} v={`${res.grade} — ${t.training.gradeDesc[res.grade] || ""}`} />
            <DRow k={t.training.dIncome} v={`${res.monthly_income.toLocaleString("ru-RU")} ${t.training.coins}`} />
            <DRow k={t.training.dProfile} v={res.down_rate.toFixed(2)} good={res.profile_ok} />
            <DRow k={t.training.dMonth} v={res.real_down_rate.toFixed(2)} good={res.monthly_ok} />
          </div>
        </div>
      )}

      {res && !hasRisk && (
        <div className="card p-5 mt-4 border border-emerald-500/30 bg-emerald-500/5 text-emerald-200 text-center font-semibold">
          ✅ {t.training.allGood}
        </div>
      )}

      {res && hasRisk && (
        <div className="card p-5 mt-4 border border-rose-500/40 bg-rose-500/5 space-y-3">
          <div className="font-extrabold text-rose-300">⚠️ {t.training.riskTitle}</div>
          <div className="text-sm text-slate-300">{t.training.riskReason}</div>
          {profileRisk && (
            <div className="text-sm text-slate-300 space-y-0.5">
              <div className="flex gap-1.5">🔸 <span>{t.training.riskProfile}</span></div>
              <div className="pl-5 text-slate-400">{t.training.riskLimit} <b className="text-slate-200">0.18</b></div>
              <div className="pl-5 text-slate-400">{t.training.riskYourCoef} <b className="text-rose-300">{res.down_rate.toFixed(2)}</b></div>
            </div>
          )}
          {monthlyRisk && (
            <div className="text-sm text-slate-300 space-y-0.5">
              <div className="flex gap-1.5">🔸 <span>{t.training.riskMonthly} <b>{res.grade}</b>.</span></div>
              {res.grade_limit != null && <div className="pl-5 text-slate-400">{t.training.riskLimit} <b className="text-slate-200">{Number(res.grade_limit).toFixed(2)}</b></div>}
              <div className="pl-5 text-slate-400">{t.training.riskYourCoef30} <b className="text-rose-300">{res.real_down_rate.toFixed(2)}</b></div>
            </div>
          )}
          {punish && (
            <div className="text-sm">
              <div className="font-semibold text-rose-300">⛔ {t.training.punishTitle}</div>
              <div className="text-slate-200">{punish}</div>
            </div>
          )}
          <div className="text-sm text-amber-200/90 bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2">📌 {t.training.riskRec}</div>
        </div>
      )}

      {res && (
        <div className="flex justify-center mt-5">
          <button className="btn-ghost !py-2.5 text-sm" disabled={busy} onClick={run}>{t.training.checkRefresh}</button>
        </div>
      )}
    </div>
  );
}

function DRow({ k, v, good }: { k: string; v: string; good?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-line last:border-0">
      <span className="text-sm text-slate-400">{k}</span>
      <span className={`font-bold ${good === undefined ? "text-slate-100" : good ? "text-emerald-300" : "text-rose-300"}`}>{v}{good !== undefined ? (good ? " ✓" : " ✕") : ""}</span>
    </div>
  );
}

function Gauge({ value, color }: { value: number; color: string }) {
  const stroke = color === "rose" ? "#fb7185" : color === "amber" ? "#fbbf24" : "#34d399";
  const r = 52, c = 2 * Math.PI * r;
  
  const frac = Math.max(0, Math.min(1, value / 0.4));
  return (
    <div className="relative w-36 h-36">
      <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
        <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
        <circle cx="60" cy="60" r={r} fill="none" stroke={stroke} strokeWidth="10" strokeLinecap="round"
                strokeDasharray={c} strokeDashoffset={c * (1 - frac)} />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <span className="text-3xl font-black" style={{ color: stroke }}>{value.toFixed(2)}</span>
      </div>
    </div>
  );
}

function ChooseTraining({ onBack, onPick }: { onBack: () => void; onPick: (s: "quick" | "full") => void }) {
  const { t } = useI18n();
  return (
    <div>
      <BackBtn onBack={onBack} />
      <div className="text-center mb-6">
        <h1 className="section-title h-grad">{t.training.trainTitle}</h1>
        <p className="text-slate-400 mt-1 text-sm">{t.training.trainSub}</p>
      </div>
      <div className="grid sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
        <FormatCard icon={<IconRocket className="w-6 h-6" />} title={t.training.quickTitle} badge={t.training.quickBadge}
                    desc={t.training.quickDesc} btn={t.training.quickBtn} onClick={() => onPick("quick")} />
        <FormatCard icon={<IconGraduation className="w-6 h-6" />} title={t.training.fullTitle} badge={t.training.fullBadge}
                    desc={t.training.fullDesc} btn={t.training.fullBtn} onClick={() => onPick("full")} recommended={t.training.recommended} />
      </div>
    </div>
  );
}

function FormatCard({ icon, title, badge, desc, btn, onClick, recommended }: { icon: React.ReactNode; title: string; badge: string; desc: string; btn: string; onClick: () => void; recommended?: string }) {
  return (
    <div className={`card p-6 flex flex-col relative ${recommended ? "border-neon-500/40 shadow-glow" : ""}`}>
      {recommended && <span className="absolute -top-2.5 right-4 chip bg-gradient-to-r from-neon-500 to-brand-600 text-white text-[11px]">★ {recommended}</span>}
      <span className="w-12 h-12 rounded-xl grid place-items-center bg-gradient-to-br from-brand-600/40 to-neon-500/30 text-neon-300 mb-3">{icon}</span>
      <div className="flex items-center gap-2 flex-wrap">
        <h3 className="font-bold text-lg">{title}</h3>
        <span className="chip bg-neon-500/15 text-neon-300 text-[11px]"><IconClock className="w-3 h-3" /> {badge}</span>
      </div>
      <p className="text-sm text-slate-400 mt-2 flex-1">{desc}</p>
      <button onClick={onClick} className="btn-primary justify-center mt-4">{btn}</button>
    </div>
  );
}

function LessonWizard({ steps, kind, password, haloId, onBack }: { steps: Lesson[]; kind: "quick" | "full"; password: string; haloId: string; onBack: () => void }) {
  const { t } = useI18n();
  const [i, setI] = useState(-1); 
  const total = steps.length;
  const introTitle = kind === "quick" ? t.training.quickTitle : t.training.fullTitle;
  const duration = kind === "quick" ? t.training.quickDuration : t.training.fullBadge;

  useEffect(() => { if (total) reportProgress(password, haloId, kind, 0, total, false); }, [total, password, haloId, kind]);

  if (total === 0) return (
    <div><BackBtn onBack={onBack} /><SectionHeading title={introTitle} /><div className="text-slate-500">{t.training.emptyLessons}</div></div>
  );

  function go(next: number) {
    const clamped = Math.max(0, Math.min(total - 1, next));
    setI(clamped);
    const done = clamped + 1;
    reportProgress(password, haloId, kind, done, total, done >= total);
  }

  
  if (i < 0) return (
    <div className="max-w-xl mx-auto">
      <BackBtn onBack={onBack} />
      <div className="card p-8 text-center bg-gradient-to-br from-brand-700/25 to-neon-600/15">
        <h1 className="text-3xl font-black tracking-tight uppercase h-grad">{introTitle}</h1>
        <p className="text-slate-300 mt-2">{total} {t.training.quickIntroSub}</p>
        <div className="mt-5 h-2 rounded-full bg-white/10 overflow-hidden">
          <div className="h-full bg-gradient-to-r from-neon-500 to-brand-500" style={{ width: `${Math.round(100 / total)}%` }} />
        </div>
        <button onClick={() => go(0)} className="btn-primary w-full justify-center mt-5 !py-3.5 text-base">{t.training.startBtn} <IconArrow className="w-4 h-4" /></button>
        <p className="text-xs text-slate-500 mt-3">{duration}</p>
      </div>
    </div>
  );

  const step = steps[i];
  const last = i === total - 1;
  const pct = Math.round(((i + 1) / total) * 100);

  return (
    <div className="max-w-4xl mx-auto">
      <BackBtn onBack={onBack} />
      <div className="flex items-center justify-between text-sm mb-2">
        <span className="text-slate-400">{t.apply.step} {i + 1} {t.apply.of} {total}</span>
        <span className="text-slate-400">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-white/10 overflow-hidden mb-5">
        <div className="h-full bg-gradient-to-r from-neon-500 to-brand-500 transition-all" style={{ width: `${pct}%` }} />
      </div>

      <div className="card p-6 grid md:grid-cols-2 gap-6 items-start">
        <div>
          <div className="flex items-center gap-3 mb-3">
            <span className="w-9 h-9 rounded-lg grid place-items-center font-black text-white bg-gradient-to-br from-neon-500 to-brand-600 shrink-0">{i + 1}</span>
            <h3 className="font-bold text-lg">{step.title || "—"}</h3>
          </div>
          {step.body && <p className="text-sm text-slate-300 whitespace-pre-line">{step.body}</p>}
          {step.items && step.items.length > 0 && (
            <div className="mt-3">
              <div className="text-[11px] font-bold uppercase tracking-wide text-neon-300 mb-1.5">{t.training.checklistLabel}</div>
              <ul className="space-y-2">
                {step.items.map((it, k) => (
                  <li key={k} className="flex items-start gap-2.5 text-sm text-slate-200">
                    <span className="mt-0.5 w-5 h-5 rounded-full grid place-items-center bg-neon-500/15 text-neon-400 shrink-0"><IconCheck className="w-3.5 h-3.5" /></span>
                    {it}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <Callouts items={step.callouts} className="mt-4" />
        </div>
        <div className="space-y-3">
          {step.video && (
            <video controls preload="metadata" className="w-full rounded-xl border border-line bg-black max-h-[460px]" src={step.video} />
          )}
          {step.image && (
            
            <img src={step.image} alt="" className="mx-auto w-auto max-w-full rounded-xl border border-line max-h-[460px]" />
          )}
          {!step.video && step.type === "video" && step.url && (
            <div className="aspect-video rounded-xl overflow-hidden border border-line bg-black">
              <iframe src={toEmbed(step.url)} className="w-full h-full" allowFullScreen title={step.title} />
            </div>
          )}
          <Gallery items={step.gallery} />
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 mt-5">
        <button onClick={() => setI(i - 1)} className="btn-ghost !py-2.5">{t.training.back}</button>
        {!last ? (
          <button onClick={() => go(i + 1)} className="btn-primary !py-2.5">{t.training.nextStep} <IconArrow className="w-4 h-4" /></button>
        ) : (
          <button onClick={onBack} className="btn-primary !py-2.5">{t.training.finish} <IconCheck className="w-4 h-4" /></button>
        )}
      </div>
    </div>
  );
}

function toEmbed(url: string): string {
  const yt = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/))([A-Za-z0-9_-]{11})/);
  if (yt) return `https://www.youtube.com/embed/${yt[1]}`;
  return url;
}
