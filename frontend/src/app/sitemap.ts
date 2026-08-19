import type { MetadataRoute } from "next";
import { blogPosts } from "@/lib/mock-blog-data";
import { FEATURED_EVENT_SLUG } from "@/lib/events";
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
    "/blog",
    "/faq",
    "/community",
    "/contact",
    "/privacy",
    "/terms",
    ...listPublicProgramPaths(),
    ...blogPosts.map((post) => `/blog/${post.slug}`),
  ];

  const unique = [...new Set(paths)];

  return unique.map((path) => ({
    url: path === "/" ? PUBLIC_SITE_ORIGIN : `${PUBLIC_SITE_ORIGIN}${path}`,
    lastModified,
    changeFrequency: path === "/" || HIGH_PRIORITY.has(path) ? "weekly" : "monthly",
    priority: path === "/" ? 1 : HIGH_PRIORITY.has(path) || path.startsWith("/programs/") ? 0.9 : 0.7,
  }));
}
