import type { Metadata } from "next";
import { inter, manrope } from "@/lib/fonts";
import { QueryProvider } from "@/components/providers/query-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { AuthSessionSync } from "@/components/providers/auth-session-sync";
import { TawkToChat } from "@/components/layout/tawk-to-chat";
import { VisitorAnalytics } from "@/components/layout/visitor-analytics";
import { MarketingPixels } from "@/components/layout/marketing-pixels";
import { CookieConsentBanner } from "@/components/layout/cookie-consent-banner";
import { OrganizationJsonLd } from "@/components/seo/organization-json-ld";
import { siteConfig } from "@/config/site";
import { PUBLIC_SITE_ORIGIN } from "@/lib/program-pages";
import { DEFAULT_OG_IMAGE, absoluteAssetUrl } from "@/lib/seo";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(PUBLIC_SITE_ORIGIN),
  applicationName: siteConfig.name,
  title: {
    default: siteConfig.seoTitle,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: siteConfig.name,
    title: siteConfig.seoTitle,
    description: siteConfig.description,
    url: PUBLIC_SITE_ORIGIN,
    images: [{ url: absoluteAssetUrl(DEFAULT_OG_IMAGE), alt: siteConfig.seoTitle }],
  },
  twitter: {
    card: "summary_large_image",
    title: siteConfig.seoTitle,
    description: siteConfig.description,
    images: [absoluteAssetUrl(DEFAULT_OG_IMAGE)],
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
        <MarketingPixels />
        <CookieConsentBanner />
        <OrganizationJsonLd />
      </body>
    </html>
  );
}
