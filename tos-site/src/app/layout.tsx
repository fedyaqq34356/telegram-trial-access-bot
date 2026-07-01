import type { Metadata } from "next";
import "./globals.css";
import { I18nProvider } from "@/i18n";
import { SiteContentProvider } from "@/components/SiteContent";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { VisitTracker } from "@/components/VisitTracker";

export const metadata: Metadata = {
  title: "TOS Agency — работа стрим-моделью в HALO",
  description: "Зарабатывай на общении онлайн из любой точки мира. Приватные звонки, эфиры, подарки. Свободный график, бесплатное обучение, быстрые выплаты.",
  openGraph: {
    title: "TOS Agency — работа стрим-моделью в HALO",
    description: "Зарабатывай на общении онлайн из любой точки мира.",
    type: "website",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <I18nProvider>
          <SiteContentProvider>
            <VisitTracker />
            <Header />
            <main>{children}</main>
            <Footer />
          </SiteContentProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
