"use client";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Spinner } from "@/components/ui";

interface Progress {
  id: number; halo_id: string; kind: "quick" | "full";
  steps_done: number; steps_total: number; percent: number;
  completed: boolean; updated_at: string | null;
}

const KIND_LABEL: Record<string, string> = { quick: "Быстрый старт", full: "Полное обучение" };

export default function TrainingProgressPage() {
  const { data, isLoading } = useSWR<Progress[]>("/site-content/training-progress", fetcher, { refreshInterval: 30000 });

  return (
    <>
      <PageHeader title="Прогресс обучения" />
      {isLoading ? (
        <div className="grid place-items-center h-40 text-brand-300"><Spinner className="w-7 h-7" /></div>
      ) : !data?.length ? (
        <div className="card text-sm text-slate-500">Пока никто не проходил обучение.</div>
      ) : (
        <div className="card !p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-slate-400 border-b border-line">
              <tr className="text-left">
                <th className="px-4 py-3">Halo ID</th>
                <th className="px-4 py-3">Тип</th>
                <th className="px-4 py-3">Прогресс</th>
                <th className="px-4 py-3">Статус</th>
                <th className="px-4 py-3">Обновлено</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r) => (
                <tr key={r.id} className="border-b border-line/60 last:border-0">
                  <td className="px-4 py-3 font-medium">{r.halo_id}</td>
                  <td className="px-4 py-3">{KIND_LABEL[r.kind] || r.kind}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 min-w-[140px]">
                      <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                        <div className={`h-full ${r.completed ? "bg-emerald-500" : "bg-brand-500"}`} style={{ width: `${r.percent}%` }} />
                      </div>
                      <span className="text-xs text-slate-400 tabular-nums">{r.steps_done}/{r.steps_total || "?"} · {r.percent}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {r.completed
                      ? <span className="chip bg-emerald-500/15 text-emerald-300 text-[11px]">Завершено</span>
                      : <span className="chip bg-amber-500/15 text-amber-300 text-[11px]">В процессе</span>}
                  </td>
                  <td className="px-4 py-3 text-slate-400">{r.updated_at ? new Date(r.updated_at).toLocaleString("ru-RU") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
