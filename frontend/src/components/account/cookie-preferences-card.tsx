"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  hasMarketingConsent,
  marketingPixelsConfigured,
  saveCookieConsent,
  subscribeCookieConsent,
} from "@/lib/cookie-consent";
import { loadMarketingPixels, revokeMarketingPixels } from "@/lib/marketing-pixels";

export function CookiePreferencesCard() {
  const [marketing, setMarketing] = useState(false);
  const configured = marketingPixelsConfigured();

  useEffect(() => {
    const sync = () => setMarketing(hasMarketingConsent());
    sync();
    return subscribeCookieConsent(sync);
  }, []);

  if (!configured) return null;

  function setPreference(next: boolean) {
    saveCookieConsent(next);
    setMarketing(next);
    if (next) loadMarketingPixels();
    else revokeMarketingPixels();
  }

  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle>Cookie preferences</CardTitle>
        <CardDescription>
          Necessary cookies keep you signed in. Marketing cookies (Meta Pixel and Google Ads) are
          optional and used to measure campaigns and show relevant Analytic Sages ads.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 sm:flex-row">
        <Button
          type="button"
          variant={marketing ? "outline" : "default"}
          onClick={() => setPreference(false)}
        >
          Necessary only
        </Button>
        <Button
          type="button"
          className={
            marketing ? "bg-brand-orange text-white hover:bg-brand-orange/90" : undefined
          }
          variant={marketing ? "default" : "outline"}
          onClick={() => setPreference(true)}
        >
          Allow marketing cookies
        </Button>
      </CardContent>
    </Card>
  );
}
