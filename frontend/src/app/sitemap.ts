import type { MetadataRoute } from "next";
import { FEATURED_EVENT_SLUG } from "@/lib/events";
import { SEEDED_INSIGHT_SLUGS } from "@/lib/insight-slugs";
import { listPublicProgramPaths, PUBLIC_SITE_ORIGIN } from "@/lib/program-pages";
import { FEATURED_FREE_COURSE_SLUG } from "@/lib/self-paced";

const HIGH_PRIORITY = new Set([
  "/",
  "/programs",
  "/instructor-led",
  "/courses",
  "/events",
  `/courses/${FEATURED_FREE_COURSE_SLUG}`,
  `/events/${FEATURED_EVENT_SLUG}`,
]);

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  const paths = [
    "/",
    "/programs",
    "/instructor-led",
    "/courses",
    `/courses/${FEATURED_FREE_COURSE_SLUG}`,
    "/events",
    `/events/${FEATURED_EVENT_SLUG}`,
    "/about",
    "/insights",
    "/faq",
    "/community",
    "/contact",
    "/privacy",
    "/terms",
    ...listPublicProgramPaths(),
    ...SEEDED_INSIGHT_SLUGS.map((slug) => `/insights/${slug}`),
  ];

  const unique = [...new Set(paths)];

  return unique.map((path) => ({
    url: path === "/" ? PUBLIC_SITE_ORIGIN : `${PUBLIC_SITE_ORIGIN}${path}`,
    lastModified,
    changeFrequency: path === "/" || HIGH_PRIORITY.has(path) ? "weekly" : "monthly",
    priority: path === "/" ? 1 : HIGH_PRIORITY.has(path) || path.startsWith("/programs/") ? 0.9 : 0.7,
  }));
}
