"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  hasDecidedCookieConsent,
  marketingPixelsConfigured,
  saveCookieConsent,
  subscribeCookieConsent,
} from "@/lib/cookie-consent";

export function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!marketingPixelsConfigured()) return;

    const sync = () => setVisible(!hasDecidedCookieConsent());
    sync();
    const unsubscribe = subscribeCookieConsent(sync);
    const onSettings = () => setVisible(true);
    window.addEventListener("as-cookie-settings", onSettings);
    return () => {
      unsubscribe();
      window.removeEventListener("as-cookie-settings", onSettings);
    };
  }, []);

  if (!visible) return null;

  function acceptMarketing() {
    saveCookieConsent(true);
    setVisible(false);
  }

  function necessaryOnly() {
    saveCookieConsent(false);
    setVisible(false);
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-[100000] p-4 sm:p-6">
      <div className="mx-auto max-w-3xl rounded-2xl border bg-card p-5 shadow-float">
        <p className="font-heading text-base font-bold">Cookies and ads</p>
        <p className="mt-2 text-sm text-muted-foreground">
          We use necessary cookies to keep you signed in. If you accept, we also use Meta Pixel and
          Google Ads to measure campaigns and show Analytic Sages ads to people who visited this
          site. Read the{" "}
          <Link href="/privacy" className="font-medium text-brand-navy underline dark:text-brand-orange">
            Privacy Policy
          </Link>
          .
        </p>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="outline" onClick={necessaryOnly}>
            Necessary only
          </Button>
          <Button
            type="button"
            onClick={acceptMarketing}
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            Accept marketing cookies
          </Button>
        </div>
      </div>
    </div>
  );
}
