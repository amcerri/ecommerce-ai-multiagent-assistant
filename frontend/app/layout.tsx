import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n/provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "E-Commerce AI Multi-Agent Assistant",
  description: "AI-powered multi-agent assistant for e-commerce operations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className={inter.className}>
        <I18nProvider>{children}</I18nProvider>
      </body>
    </html>
  );
}

