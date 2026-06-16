"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { getSiteContent, type SiteContent } from "@/lib/api";

const Ctx = createContext<SiteContent | null>(null);

export function SiteContentProvider({ children }: { children: React.ReactNode }) {
  const [content, setContent] = useState<SiteContent | null>(null);
  useEffect(() => { getSiteContent().then(setContent); }, []);
  return <Ctx.Provider value={content}>{children}</Ctx.Provider>;
}

export const useSiteContent = () => useContext(Ctx);
