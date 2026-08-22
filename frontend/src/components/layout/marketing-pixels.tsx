"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import {
  hasMarketingConsent,
  marketingPixelsConfigured,
  subscribeCookieConsent,
} from "@/lib/cookie-consent";
import {
  loadMarketingPixels,
  revokeMarketingPixels,
  trackMarketingPageView,
  trackViewContent,
} from "@/lib/marketing-pixels";

function contentFromPath(path: string): { name: string; category: string } | null {
  if (path === "/instructor-led") return { name: "Instructor-led training", category: "program" };
  if (path === "/courses") return { name: "Self-paced courses", category: "catalog" };
  if (path === "/programs") return { name: "Programs", category: "program" };
  if (path === "/events") return { name: "Events", category: "event" };
  if (path === "/blog") return { name: "Blog", category: "blog" };

  const course = path.match(/^\/courses\/([^/]+)$/);
  if (course) return { name: course[1], category: "course" };
  const program = path.match(/^\/programs\/([^/]+)$/);
  if (program) return { name: program[1], category: "program" };
  const event = path.match(/^\/events\/([^/]+)$/);
  if (event) return { name: event[1], category: "event" };
  const post = path.match(/^\/blog\/([^/]+)$/);
  if (post) return { name: post[1], category: "blog" };
  return null;
}

export function MarketingPixels() {
  const pathname = usePathname();
  const lastTracked = useRef<string | null>(null);

  useEffect(() => {
    if (!marketingPixelsConfigured()) return;

    const apply = () => {
      if (!hasMarketingConsent()) {
        revokeMarketingPixels();
        lastTracked.current = null;
        return;
      }
      loadMarketingPixels();
      const key = `view:${pathname}`;
      if (lastTracked.current === key) return;
      lastTracked.current = key;
      trackMarketingPageView(pathname);
      const content = contentFromPath(pathname);
      if (content) {
        trackViewContent({ name: content.name, category: content.category, ids: [content.name] });
      }
    };
    apply();
    return subscribeCookieConsent(apply);
  }, [pathname]);

  return null;
}
