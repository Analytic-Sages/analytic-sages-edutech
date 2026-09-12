import Script from "next/script";

/**
 * Google Tag Manager container for GA4 / Search Console (configured in GTM).
 * Default: GTM-W6M93GM9. Override with NEXT_PUBLIC_GTM_ID, or set empty to disable.
 */
export function getGtmId() {
  const raw = process.env.NEXT_PUBLIC_GTM_ID;
  if (raw === undefined) return "GTM-W6M93GM9";
  return raw.trim();
}

/** GTM snippet — afterInteractive is required in the App Router (beforeInteractive is pages-only). */
export function GoogleTagManager() {
  const gtmId = getGtmId();
  if (!gtmId) return null;

  return (
    <Script
      id="google-tag-manager"
      strategy="afterInteractive"
      dangerouslySetInnerHTML={{
        __html: `(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','${gtmId}');`,
      }}
    />
  );
}

/** noscript fallback — place immediately after opening <body>. */
export function GoogleTagManagerNoscript() {
  const gtmId = getGtmId();
  if (!gtmId) return null;

  return (
    <noscript>
      <iframe
        src={`https://www.googletagmanager.com/ns.html?id=${encodeURIComponent(gtmId)}`}
        height={0}
        width={0}
        style={{ display: "none", visibility: "hidden" }}
        title="Google Tag Manager"
      />
    </noscript>
  );
}
