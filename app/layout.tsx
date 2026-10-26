import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenAccess DNS — Свободный интернет без блокировок",
  description:
    "Децентрализованный DNS-резолвер для свободного интернета. Вернем ваш интернет как в 2020 году. Без блокировок. Бесплатно. Open Source. DoH, DoT, Plain DNS + профили для iOS/Android.",
  keywords: [
    "DNS",
    "DoH",
    "DoT",
    "обход блокировок",
    "свободный интернет",
    "AdGuard",
    "Technitium",
    "Open Source",
    "DNS over HTTPS",
  ],
  authors: [{ name: "OpenAccess DNS" }],
  openGraph: {
    title: "OpenAccess DNS — Вернем интернет как в 2020",
    description:
      "Без блокировок. Бесплатно. Open Source. Подключайся за 30 секунд.",
    type: "website",
    locale: "ru_RU",
    siteName: "OpenAccess DNS",
  },
  twitter: {
    card: "summary_large_image",
    title: "OpenAccess DNS — Свободный интернет",
    description: "DNS без блокировок. DoH / DoT / Plain. Open Source.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body className="antialiased">{children}</body>
    </html>
  );
}
