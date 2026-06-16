// Превращает username/ссылку в корректный URL для соцсетей.
export function socialHref(kind: "telegram" | "instagram" | "tiktok" | "whatsapp", value: string): string {
  const v = (value || "").trim();
  if (!v) return "#";
  if (v.startsWith("http://") || v.startsWith("https://")) return v;
  const handle = v.replace(/^@/, "");
  switch (kind) {
    case "telegram": return `https://t.me/${handle}`;
    case "instagram": return `https://instagram.com/${handle}`;
    case "tiktok": return `https://tiktok.com/@${handle}`;
    case "whatsapp": return `https://wa.me/${v.replace(/[^\d]/g, "")}`;
  }
}
