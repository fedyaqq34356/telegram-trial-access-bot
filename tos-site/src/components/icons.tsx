type P = { className?: string };
const S = ({ className = "w-5 h-5", d, fill }: P & { d: string; fill?: boolean }) => (
  <svg viewBox="0 0 24 24" className={className} fill={fill ? "currentColor" : "none"} stroke="currentColor"
       strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round"><path d={d} /></svg>
);

export const IconCheck = (p: P) => <S {...p} d="M20 6L9 17l-5-5" />;
export const IconChevron = (p: P) => <S {...p} d="M6 9l6 6 6-6" />;
export const IconArrow = (p: P) => <S {...p} d="M5 12h14M13 6l6 6-6 6" />;
export const IconSpark = (p: P) => <S {...p} d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z" fill />;
export const IconGift = (p: P) => <S {...p} d="M20 12v9H4v-9M2 7h20v5H2zM12 22V7M12 7H7.5a2.5 2.5 0 010-5C11 2 12 7 12 7zM12 7h4.5a2.5 2.5 0 000-5C13 2 12 7 12 7z" />;
export const IconCoin = (p: P) => <S {...p} d="M12 22c5.5 0 10-4.5 10-10S17.5 2 12 2 2 6.5 2 12s4.5 10 10 10zM12 7v10M9.5 9.5h3.5a1.5 1.5 0 010 3H10a1.5 1.5 0 000 3h4" />;
export const IconHeart = (p: P) => <S {...p} d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.6l-1-1a5.5 5.5 0 00-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 000-7.8z" fill />;
export const IconClock = (p: P) => <S {...p} d="M12 22a10 10 0 100-20 10 10 0 000 20zM12 6v6l4 2" />;
export const IconGlobe = (p: P) => <S {...p} d="M12 22a10 10 0 100-20 10 10 0 000 20zM2 12h20M12 2a15 15 0 014 10 15 15 0 01-4 10 15 15 0 01-4-10 15 15 0 014-10z" />;
export const IconShield = (p: P) => <S {...p} d="M12 2l8 4v6c0 5-3.8 9-8 10-4.2-1-8-5-8-10V6l8-4zM9 12l2 2 4-4" />;
export const IconChat = (p: P) => <S {...p} d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />;
export const IconWallet = (p: P) => <S {...p} d="M21 12V7H5a2 2 0 010-4h14v4M3 5v14a2 2 0 002 2h16v-5M18 12a2 2 0 000 4h4v-4z" />;
export const IconStar = (p: P) => <S {...p} d="M12 2l3 6.5 7 .9-5 4.8 1.3 7L12 18l-6.3 3.2L7 14 2 9.4l7-.9L12 2z" fill />;
export const IconCalendar = (p: P) => <S {...p} d="M3 8h18M7 3v4M17 3v4M5 5h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2z" />;
export const IconGraduation = (p: P) => <S {...p} d="M22 9L12 5 2 9l10 4 10-4zM6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5" />;
export const IconRocket = (p: P) => <S {...p} d="M5 15s-2 1-2 4c3 0 4-2 4-2M12 15l-3-3a12 12 0 016-9c3 0 4 1 4 1s1 1 1 4a12 12 0 01-9 6zM15 9a1 1 0 100-2 1 1 0 000 2z" />;
export const IconLock = (p: P) => <S {...p} d="M5 11h14v10H5zM8 11V7a4 4 0 018 0v4" />;
export const IconMenu = (p: P) => <S {...p} d="M3 12h18M3 6h18M3 18h18" />;
export const IconClose = (p: P) => <S {...p} d="M18 6L6 18M6 6l12 12" />;
export const IconTelegram = (p: P) => <S {...p} d="M22 3L2 10.5l6 2.2M22 3l-3 16-7-5-4 4v-5l11-10" />;
export const IconInstagram = (p: P) => <S {...p} d="M7 2h10a5 5 0 015 5v10a5 5 0 01-5 5H7a5 5 0 01-5-5V7a5 5 0 015-5zM12 8a4 4 0 100 8 4 4 0 000-8zM17.5 6.5h.01" />;
export const IconTiktok = (p: P) => <S {...p} d="M16 3c.5 2.5 2 4 4.5 4.3v3C18.7 10.2 17.2 9.6 16 8.7V15a5.5 5.5 0 11-5.5-5.5c.3 0 .7 0 1 .1v3.1a2.5 2.5 0 101.5 2.3V3H16z" />;
export const IconPlay = (p: P) => <S {...p} d="M6 4l14 8-14 8V4z" fill />;
export const IconVideo = (p: P) => <S {...p} d="M23 7l-7 5 7 5V7zM1 5h14a2 2 0 012 2v10a2 2 0 01-2 2H1z" />;
export const IconList = (p: P) => <S {...p} d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />;
export const IconText = (p: P) => <S {...p} d="M4 7V5h16v2M9 19h6M12 5v14" />;
export const IconDiamond = (p: P) => <S {...p} d="M6 3h12l3.5 5L12 21 2.5 8 6 3zM2.5 8h19M9 3l-2 5 5 13M15 3l2 5-5 13" />;
export const IconThumbUp = (p: P) => <S {...p} d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3zM7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3" />;
export const IconThumbDown = (p: P) => <S {...p} d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3zm7-13h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17" />;
export const IconMonitor = (p: P) => <S {...p} d="M3 4h18a1 1 0 011 1v11a1 1 0 01-1 1H3a1 1 0 01-1-1V5a1 1 0 011-1zM8 21h8M12 17v4" />;
export const IconDownload = (p: P) => <S {...p} d="M12 3v12M7 10l5 5 5-5M4 21h16" />;
export const IconAndroid = (p: P) => <S {...p} d="M6 9v8a1 1 0 001 1h10a1 1 0 001-1V9zM6 9a6 6 0 0112 0M9 5L7.5 3M15 5l1.5-2M9.5 7h.01M14.5 7h.01M3.5 10v5M20.5 10v5M9 18v2.5M15 18v2.5" />;
export const IconApple = (p: P) => <S {...p} d="M16 13c0 3 2.5 4 2.5 4-1 2-2 3-3.5 3-1 0-1.7-.6-3-.6s-2 .6-3 .6c-2 0-4.5-4-4.5-7.5C4 11 6 9.5 8 9.5c1.2 0 2 .7 3 .7s1.8-.8 3.2-.7c1.3.1 2.3.7 2.8 1.5-2.3 1.3-2 3.5-2 3.5zM13 6c.8-1 1-2.3.8-3-.9.1-2 .7-2.6 1.5-.6.7-1 1.9-.8 3 .9 0 1.8-.6 2.6-1.5z" fill />;
export const IconWhatsapp = (p: P) => <S {...p} d="M3 21l1.65-4.8A8 8 0 1112 20a8 8 0 01-4-1l-5 2zM9 8c-.3 0-.6.1-.8.4-.3.3-1 1-1 2.3s1 2.7 1.2 2.9c.1.2 2 3.1 4.9 4.2 2.4.9 2.9.8 3.4.7.5 0 1.6-.6 1.8-1.3.2-.6.2-1.2.2-1.3-.1-.1-.3-.2-.6-.4-.3-.1-1.6-.8-1.9-.9-.3-.1-.4-.1-.6.1-.2.3-.6.9-.8 1-.1.2-.3.2-.5.1-.3-.1-1.1-.4-2.1-1.3-.8-.7-1.3-1.5-1.5-1.8-.1-.3 0-.4.1-.5l.4-.5c.2-.2.2-.3.3-.5.1-.2 0-.4 0-.5 0-.1-.6-1.5-.8-2C9.7 8.1 9.5 8 9.3 8H9z" />;
