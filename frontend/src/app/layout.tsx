import type { Metadata } from "next";
import { inter, manrope } from "@/lib/fonts";
import { QueryProvider } from "@/components/providers/query-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { AuthSessionSync } from "@/components/providers/auth-session-sync";
import { TawkToChat } from "@/components/layout/tawk-to-chat";
import { VisitorAnalytics } from "@/components/layout/visitor-analytics";
import { siteConfig } from "@/config/site";
import { PUBLIC_SITE_ORIGIN } from "@/lib/program-pages";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(PUBLIC_SITE_ORIGIN),
  applicationName: siteConfig.name,
  title: {
    default: siteConfig.name,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: siteConfig.name,
    title: siteConfig.name,
    description: siteConfig.description,
    url: PUBLIC_SITE_ORIGIN,
  },
  twitter: {
    card: "summary_large_image",
    title: siteConfig.name,
    description: siteConfig.description,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${manrope.variable} min-h-screen font-sans antialiased`}>
        <ThemeProvider>
          <AuthSessionSync />
          <QueryProvider>{children}</QueryProvider>
        </ThemeProvider>
        <TawkToChat />
        <VisitorAnalytics />
      </body>
    </html>
  );
}
