"use client";
import { useState } from "react";
import { useAgencies } from "@/lib/agency";
import { IconAgency, IconChevron } from "./icons";

export function AgencySelect() {
  const { agencies, selected, setSelected } = useAgencies();
  const [open, setOpen] = useState(false);
  const current = agencies.find((a) => a.id === selected);
  const label = selected === null ? "Все агентства" : current?.name || "Агентство";

  return (
    <div className="relative">
      <button onClick={() => setOpen((o) => !o)} onBlur={() => setTimeout(() => setOpen(false), 150)}
              className="btn-ghost min-w-[180px] justify-between">
        <span className="flex items-center gap-2"><IconAgency className="w-4 h-4 text-brand-300" /> {label}</span>
        <IconChevron className="w-4 h-4 text-slate-500" />
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-56 popover p-1.5 z-30">
          <button onClick={() => { setSelected(null); setOpen(false); }}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-white/5 ${selected === null ? "text-brand-300" : ""}`}>
            Все агентства
          </button>
          <div className="h-px bg-line my-1" />
          {agencies.map((a) => (
            <button key={a.id} onClick={() => { setSelected(a.id); setOpen(false); }}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-white/5 flex items-center justify-between ${selected === a.id ? "text-brand-300" : ""}`}>
              {a.name}
              {a.has_session && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
            </button>
          ))}
          {agencies.length === 0 && <div className="px-3 py-2 text-sm text-slate-500">Нет агентств</div>}
        </div>
      )}
    </div>
  );
}
