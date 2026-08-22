import {
  getGoogleAdsId,
  getMetaPixelId,
  hasMarketingConsent,
} from "@/lib/cookie-consent";

declare global {
  interface Window {
    fbq?: ((...args: unknown[]) => void) & { queue?: unknown[] };
    _fbq?: unknown;
    dataLayer?: unknown[];
    gtag?: (...args: unknown[]) => void;
  }
}

let metaLoaded = false;
let googleLoaded = false;

function canTrack() {
  return typeof window !== "undefined" && hasMarketingConsent();
}

export function loadMarketingPixels() {
  if (!canTrack()) return;
  loadMetaPixel();
  loadGoogleAds();
}

function loadMetaPixel() {
  const pixelId = getMetaPixelId();
  if (!pixelId || metaLoaded || typeof window === "undefined") return;

  if (!window.fbq) {
    const fbq = ((...args: unknown[]) => {
      (fbq.queue = fbq.queue || []).push(args);
    }) as NonNullable<Window["fbq"]>;
    fbq.queue = [];
    window.fbq = fbq;
    window._fbq = fbq;
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://connect.facebook.net/en_US/fbevents.js";
    document.head.appendChild(script);
  }

  window.fbq?.("consent", "grant");
  window.fbq?.("init", pixelId);
  metaLoaded = true;
}

function loadGoogleAds() {
  const adsId = getGoogleAdsId();
  if (!adsId || googleLoaded || typeof window === "undefined") return;

  window.dataLayer = window.dataLayer || [];
  window.gtag =
    window.gtag ||
    function gtag(...args: unknown[]) {
      window.dataLayer?.push(args);
    };
  window.gtag("js", new Date());
  window.gtag("consent", "update", {
    ad_storage: "granted",
    ad_user_data: "granted",
    ad_personalization: "granted",
  });

  if (!document.getElementById("as-google-ads")) {
    const script = document.createElement("script");
    script.id = "as-google-ads";
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(adsId)}`;
    document.head.appendChild(script);
  }

  window.gtag("config", adsId, { allow_enhanced_conversions: false, send_page_view: false });
  googleLoaded = true;
}

export function revokeMarketingPixels() {
  if (typeof window === "undefined") return;
  window.fbq?.("consent", "revoke");
  window.gtag?.("consent", "update", {
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
  });
}

export function trackMarketingPageView(path: string) {
  if (!canTrack()) return;
  loadMarketingPixels();
  window.fbq?.("track", "PageView");
  window.gtag?.("event", "page_view", { page_path: path });
}

export function trackViewContent(content: {
  name: string;
  category?: string;
  ids?: string[];
}) {
  if (!canTrack()) return;
  loadMarketingPixels();
  window.fbq?.("track", "ViewContent", {
    content_name: content.name,
    content_category: content.category,
    content_ids: content.ids,
  });
  window.gtag?.("event", "view_item", {
    item_name: content.name,
    item_category: content.category,
  });
}

export function trackCompleteRegistration() {
  if (!canTrack()) return;
  loadMarketingPixels();
  window.fbq?.("track", "CompleteRegistration");
  window.gtag?.("event", "sign_up", { method: "email" });
}

export function trackLead() {
  if (!canTrack()) return;
  loadMarketingPixels();
  window.fbq?.("track", "Lead");
  window.gtag?.("event", "generate_lead");
}

export function trackContact() {
  if (!canTrack()) return;
  loadMarketingPixels();
  window.fbq?.("track", "Contact");
  window.gtag?.("event", "generate_lead", { event_category: "contact" });
}

export function trackStartTrial(contentName: string) {
  if (!canTrack()) return;
  loadMarketingPixels();
  window.fbq?.("track", "StartTrial", { content_name: contentName });
  window.gtag?.("event", "tutorial_begin", { item_name: contentName });
}

export function trackInitiateCheckout(contentName: string, value?: number, currency?: string) {
  if (!canTrack()) return;
  loadMarketingPixels();
  window.fbq?.("track", "InitiateCheckout", {
    content_name: contentName,
    value,
    currency,
  });
  window.gtag?.("event", "begin_checkout", {
    item_name: contentName,
    value,
    currency,
  });
}
