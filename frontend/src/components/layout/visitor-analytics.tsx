import Script from "next/script";

/** Cookieless Plausible script. No-ops unless NEXT_PUBLIC_PLAUSIBLE_DOMAIN is set. */
export function VisitorAnalytics() {
  const domain = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN?.trim();
  if (!domain) return null;

  return (
    <Script
      defer
      data-domain={domain}
      src="https://plausible.io/js/script.js"
      strategy="afterInteractive"
    />
  );
}
