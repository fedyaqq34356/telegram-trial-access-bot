"use client";
import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { useI18n } from "@/i18n";
import { trackVisit } from "@/lib/api";

/** Пишет посещение в свой backend-трекер при каждом переходе (без внешних сервисов). */
export function VisitTracker() {
  const pathname = usePathname();
  const { lang } = useI18n();
  const last = useRef<string>("");

  useEffect(() => {
    if (!pathname || last.current === pathname) return;
    last.current = pathname;
    trackVisit(pathname, lang);
  }, [pathname, lang]);

  return null;
}
