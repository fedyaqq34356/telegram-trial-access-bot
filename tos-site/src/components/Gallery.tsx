import type { GalleryItem } from "@/lib/api";

export function Gallery({ items, className = "" }: { items?: GalleryItem[]; className?: string }) {
  const list = (items || []).filter((g) => g?.image);
  if (list.length === 0) return null;
  const cols = list.length >= 4 ? "grid-cols-2 sm:grid-cols-4" : list.length === 3 ? "grid-cols-3" : "grid-cols-2";
  return (
    <div className={`grid ${cols} gap-2 ${className}`}>
      {list.map((g, i) => (
        <div key={i} className="text-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={g.image} alt="" className="w-full rounded-lg border border-line object-contain bg-black/20" />
          {g.caption && <div className="text-[11px] text-slate-400 mt-1 leading-snug">{g.caption}</div>}
        </div>
      ))}
    </div>
  );
}
