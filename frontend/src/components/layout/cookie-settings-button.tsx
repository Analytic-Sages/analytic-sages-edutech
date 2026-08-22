"use client";

import { openCookieSettings, marketingPixelsConfigured } from "@/lib/cookie-consent";

export function CookieSettingsButton() {
  if (!marketingPixelsConfigured()) return null;

  return (
    <button
      type="button"
      onClick={() => openCookieSettings()}
      className="text-sm text-muted-foreground hover:text-foreground"
    >
      Cookie settings
    </button>
  );
}
