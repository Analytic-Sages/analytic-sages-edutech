"use client";

import { useEffect } from "react";
import { ensureSession } from "@/lib/api";

const REFRESH_INTERVAL_MS = 10 * 60 * 1000;

/** Renews the access token from the first-party refresh cookie. */
export function AuthSessionSync() {
  useEffect(() => {
    void ensureSession();

    const onVisible = () => {
      if (document.visibilityState === "visible") void ensureSession();
    };
    const onFocus = () => {
      void ensureSession();
    };

    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", onFocus);
    const timer = window.setInterval(() => {
      void ensureSession();
    }, REFRESH_INTERVAL_MS);

    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", onFocus);
      window.clearInterval(timer);
    };
  }, []);

  return null;
}
