import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Honest relative time for last activity. Returns null if the timestamp is missing or invalid. */
export function formatRelativeTime(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return null;
  const deltaSeconds = Math.round((then - Date.now()) / 1000);
  const abs = Math.abs(deltaSeconds);
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
  if (abs < 45) return "just now";
  if (abs < 90 * 60) return rtf.format(Math.round(deltaSeconds / 60), "minute");
  if (abs < 36 * 60 * 60) return rtf.format(Math.round(deltaSeconds / 3600), "hour");
  if (abs < 10 * 24 * 60 * 60) return rtf.format(Math.round(deltaSeconds / 86400), "day");
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(then));
}
