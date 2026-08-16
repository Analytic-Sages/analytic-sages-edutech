"use client";

import { useEffect } from "react";
import { syncAuthSession } from "@/lib/api";

/** Aligns the middleware session cookie with localStorage on every page load. */
export function AuthSessionSync() {
  useEffect(() => {
    syncAuthSession();
  }, []);

  return null;
}
