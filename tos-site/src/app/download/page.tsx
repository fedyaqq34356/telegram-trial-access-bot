"use client";
import { useI18n } from "@/i18n";
import { useSiteContent } from "@/components/SiteContent";
import { Section, SectionHeading, Reveal } from "@/components/ui";
import { IconAndroid, IconApple, IconDownload, IconArrow } from "@/components/icons";

type Slot = { key: string; label: string; gender: string; platform: "android" | "iphone" };

export default function DownloadPage() {
  const { t } = useI18n();
  const content = useSiteContent();
  const dl = content?.app_downloads ?? {};
  const d = t.download;

  const slots: Slot[] = [
    { key: "android_female", label: d.androidFemale, gender: d.female, platform: "android" },
    { key: "android_male", label: d.androidMale, gender: d.male, platform: "android" },
    { key: "iphone_female", label: d.iphoneFemale, gender: d.female, platform: "iphone" },
    { key: "iphone_male", label: d.iphoneMale, gender: d.male, platform: "iphone" },
  ];

  return (
    <Section className="!pt-12">
      <SectionHeading title={d.title} lead={d.lead} center />
      <div className="grid sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
        {slots.map((s, i) => {
          const item = dl[s.key] || { type: "link", href: "" };
          const href = item.href || "";
          const isApk = item.type === "apk";
          const Icon = s.platform === "android" ? IconAndroid : IconApple;
          return (
            <Reveal key={s.key} delay={i * 60}>
              <div className="card p-6 h-full flex flex-col items-center text-center">
                <span className="w-14 h-14 rounded-2xl grid place-items-center bg-gradient-to-br from-brand-600/40 to-neon-500/30 text-neon-300 mb-3">
                  <Icon className="w-7 h-7" />
                </span>
                <span className="chip bg-white/5 border border-line text-slate-300 text-[11px] mb-2">{s.gender}</span>
                <h3 className="font-bold">{s.label}</h3>
                <div className="mt-4 w-full">
                  {href ? (
                    isApk ? (
                      <a href={href} download className="btn-primary w-full justify-center">
                        {d.btnDownload} <IconDownload className="w-4 h-4" />
                      </a>
                    ) : (
                      <a href={href} target="_blank" rel="noreferrer" className="btn-primary w-full justify-center">
                        {d.btnOpen} <IconArrow className="w-4 h-4" />
                      </a>
                    )
                  ) : (
                    <span className="btn-ghost w-full justify-center opacity-50 cursor-default">{d.soon}</span>
                  )}
                </div>
              </div>
            </Reveal>
          );
        })}
      </div>
    </Section>
  );
}
