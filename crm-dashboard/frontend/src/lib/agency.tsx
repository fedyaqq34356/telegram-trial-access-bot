"use client";
import { createContext, useContext, useEffect, useState } from "react";
import useSWR from "swr";
import { fetcher } from "./api";
import type { Agency } from "./types";

interface AgencyCtx {
  agencies: Agency[];
  selected: number | null; // null = все доступные
  setSelected: (id: number | null) => void;
  loading: boolean;
  reload: () => void;
}

const Ctx = createContext<AgencyCtx>(null as any);
const KEY = "vio_agency";

export function AgencyProvider({ children }: { children: React.ReactNode }) {
  const { data, isLoading, mutate } = useSWR<Agency[]>("/agencies", fetcher);
  const [selected, setSelectedState] = useState<number | null>(null);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem(KEY) : null;
    if (saved && saved !== "all") setSelectedState(Number(saved));
  }, []);

  function setSelected(id: number | null) {
    setSelectedState(id);
    if (typeof window !== "undefined") localStorage.setItem(KEY, id === null ? "all" : String(id));
  }

  return (
    <Ctx.Provider value={{ agencies: data || [], selected, setSelected, loading: isLoading, reload: mutate }}>
      {children}
    </Ctx.Provider>
  );
}

export const useAgencies = () => useContext(Ctx);
