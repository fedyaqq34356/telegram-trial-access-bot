export function nf(n: number | null | undefined): string {
  if (n === null || n === undefined) return "0";
  return Math.round(n).toLocaleString("ru-RU").replace(/,/g, " ");
}

export function usd(n: number | null | undefined): string {
  const v = n ?? 0;
  return "$" + v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function coins(n: number | null | undefined): string {
  return nf(n) + " coins";
}

export function pct(n: number | null | undefined): string {
  return (n ?? 0) + "%";
}

export function onlineLabel(o?: { hours: number; minutes: number } | null): string {
  if (!o) return "—";
  if (o.hours === 0 && o.minutes === 0) return "0 м";
  if (o.hours === 0) return `${o.minutes} м`;
  return `${nf(o.hours)} ч ${o.minutes} м`;
}

export function dt(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("ru-RU", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
    timeZone: "Europe/London",
  });
}

export function timeAgo(iso?: string | null): string {
  if (!iso) return "нет данных";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "только что";
  if (diff < 3600) return `${Math.floor(diff / 60)} мин. назад`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} ч. назад`;
  return dt(iso);
}
