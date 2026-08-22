export const COOKIE_CONSENT_KEY = "as_cookie_consent";
export const COOKIE_CONSENT_VERSION = 1;

export type CookieConsent = {
  version: number;
  necessary: true;
  marketing: boolean;
  decidedAt: string;
};

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((listener) => listener());
}

export function subscribeCookieConsent(listener: () => void) {
  listeners.add(listener);
  if (typeof window !== "undefined") {
    window.addEventListener("storage", listener);
  }
  return () => {
    listeners.delete(listener);
    if (typeof window !== "undefined") {
      window.removeEventListener("storage", listener);
    }
  };
}

export function readCookieConsent(): CookieConsent | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(COOKIE_CONSENT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CookieConsent;
    if (parsed.version !== COOKIE_CONSENT_VERSION || typeof parsed.marketing !== "boolean") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function hasDecidedCookieConsent(): boolean {
  return readCookieConsent() !== null;
}

export function hasMarketingConsent(): boolean {
  return readCookieConsent()?.marketing === true;
}

export function saveCookieConsent(marketing: boolean) {
  if (typeof window === "undefined") return;
  const value: CookieConsent = {
    version: COOKIE_CONSENT_VERSION,
    necessary: true,
    marketing,
    decidedAt: new Date().toISOString(),
  };
  localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(value));
  notify();
}

export function openCookieSettings() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event("as-cookie-settings"));
}

export function marketingPixelsConfigured() {
  return Boolean(getMetaPixelId() || getGoogleAdsId());
}

export function getMetaPixelId() {
  return process.env.NEXT_PUBLIC_META_PIXEL_ID?.trim() || "";
}

export function getGoogleAdsId() {
  return process.env.NEXT_PUBLIC_GOOGLE_ADS_ID?.trim() || "";
}
