"use client";

import { useSyncExternalStore } from "react";
import { getAccessToken, subscribeAccessToken } from "@/lib/api";

export function useAccessToken() {
  return useSyncExternalStore(subscribeAccessToken, getAccessToken, () => null);
}

export function useIsSignedIn() {
  return Boolean(useAccessToken());
}
