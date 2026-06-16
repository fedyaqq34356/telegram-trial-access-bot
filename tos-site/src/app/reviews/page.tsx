"use client";
import { useI18n } from "@/i18n";
import { useSiteContent } from "@/components/SiteContent";
import { Section, SectionHeading, Reveal, CtaBand } from "@/components/ui";
import { ReviewCard } from "@/components/ReviewCard";
import { REVIEWS, type SeedReview, type ChatMsg } from "@/data/reviews";
import { IconShield } from "@/components/icons";

export default function ReviewsPage() {
  const { t, lang } = useI18n();
  const content = useSiteContent();
  const seed = REVIEWS[lang];
  const admin = content?.reviews ?? [];

  // отзывы из админки → формат карточки ReviewCard (на текущем языке)
  const adminCards: SeedReview[] = admin.map((r) => {
    const pick = (m: Record<string, string>) => m?.[lang] || m?.ru || "";
    const messages: ChatMsg[] = [];
    if (pick(r.msg_in)) messages.push({ side: "in", text: pick(r.msg_in), time: r.time_in || "20:15" });
    if (pick(r.msg_reply)) messages.push({ side: "out", text: pick(r.msg_reply), time: r.time_reply || "20:16" });
    return {
      id: `a${r.id}`,
      flag: r.flag || "🌍",
      countryKey: pick(r.country),
      age: r.age,
      date: pick(r.date),
      results: [
        { label: "week", amount: r.week },
        { label: "month", amount: r.month },
      ].filter((x) => x.amount),
      messages,
    };
  });

  const all = [...adminCards, ...seed];

  return (
    <>
      <Section className="!pt-12">
        <SectionHeading title={t.reviews.title} lead={t.reviews.subtitle} center />
        <div className="flex justify-center -mt-4 mb-10">
          <span className="chip bg-white/5 border border-line text-slate-300"><IconShield className="w-4 h-4 text-neon-400" /> {t.reviews.safetyNote}</span>
        </div>

        <div className="grid lg:grid-cols-2 gap-4">
          {all.map((r, i) => (
            <Reveal key={r.id} delay={i * 60}><ReviewCard review={r} /></Reveal>
          ))}
        </div>
      </Section>
      <CtaBand title={t.home.ctaTitle} text={t.home.ctaText} />
    </>
  );
}
