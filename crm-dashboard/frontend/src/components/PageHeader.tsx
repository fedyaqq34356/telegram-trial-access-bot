"use client";
import { useState } from "react";
import { useSWRConfig } from "swr";
import { api, qs } from "@/lib/api";
import { useAgencies } from "@/lib/agency";
import { IconRefresh } from "./icons";
import { Spinner } from "./ui";

export function RefreshButton() {
  const { selected } = useAgencies();
  const { mutate } = useSWRConfig();
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      await api.post(`/sync${qs({ agency_id: selected ?? undefined })}`);
    } catch {}
    // ревалидируем все запросы
    await mutate(() => true, undefined, { revalidate: true });
    setLoading(false);
  }

  return (
    <button onClick={refresh} disabled={loading} className="btn-primary">
      {loading ? <Spinner className="w-4 h-4" /> : <IconRefresh className="w-4 h-4" />}
      Обновить данные
    </button>
  );
}

export function PageHeader({ title, children, showRefresh = true }: {
  title: string; children?: React.ReactNode; showRefresh?: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 mb-6">
      <h1 className="text-2xl font-extrabold tracking-tight mr-auto">{title}</h1>
      {children}
      {showRefresh && <RefreshButton />}
    </div>
  );
}
