"use client";
import { createContext, useContext, useEffect, useState } from "react";
import type { Dict } from "./types";
import { ru } from "./ru";
import { en } from "./en";
import { ua } from "./ua";

export type Lang = "ru" | "en" | "ua";
export const LANGS: Lang[] = ["ru", "en", "ua"];
const DICTS: Record<Lang, Dict> = { ru, en, ua };
const KEY = "tos_lang";

interface Ctx { lang: Lang; setLang: (l: Lang) => void; t: Dict }
const I18nCtx = createContext<Ctx>({ lang: "ru", setLang: () => {}, t: ru });

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("ru");

  useEffect(() => {
    const saved = (typeof window !== "undefined" && localStorage.getItem(KEY)) as Lang | null;
    if (saved && LANGS.includes(saved)) setLangState(saved);
  }, []);

  function setLang(l: Lang) {
    setLangState(l);
    if (typeof window !== "undefined") {
      localStorage.setItem(KEY, l);
      document.documentElement.lang = l === "ua" ? "uk" : l;
    }
  }

  return <I18nCtx.Provider value={{ lang, setLang, t: DICTS[lang] }}>{children}</I18nCtx.Provider>;
}

export const useI18n = () => useContext(I18nCtx);
