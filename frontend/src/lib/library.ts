/** Internal Learning Library content. Not a public nav destination; visitors use /courses. */

import { siteConfig } from "@/config/site";
import { FEATURED_FREE_COURSE, FEATURED_FREE_COURSE_SLUG } from "@/lib/self-paced";

export const LIBRARY_CATEGORIES = [
  "courses",
  "tutorials",
  "research",
  "career",
  "workshops",
  "webinars",
] as const;

export type LibraryCategory = (typeof LIBRARY_CATEGORIES)[number];

export const LIBRARY_CATEGORY_LABELS: Record<LibraryCategory, string> = {
  courses: "Courses",
  tutorials: "Tutorials",
  research: "Research",
  career: "Career",
  workshops: "Workshops",
  webinars: "Webinars",
};

export type LibraryItem = {
  id: string;
  category: LibraryCategory;
  title: string;
  description: string;
  href: string;
  cta: string;
  comingSoon?: boolean;
  videoId?: string | null;
  thumbnail?: string | null;
  duration?: string | null;
  badge?: string;
};

function lessonItem(
  slug: string,
  title: string,
  description: string,
  videoId: string,
  duration: string | null,
): LibraryItem {
  return {
    id: `tutorial:${slug}`,
    category: "tutorials",
    title,
    description,
    href: `/courses/${FEATURED_FREE_COURSE_SLUG}`,
    cta: "Open free course",
    videoId,
    thumbnail: `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
    duration,
    badge: "Free lesson",
  };
}

/** Structured free Dune lessons. Watch inside the course, not as extra catalog SKUs. */
export const LIBRARY_TUTORIALS: LibraryItem[] = [
  lessonItem(
    "introduction-to-external-api-calls-in-dune",
    "Introduction to External API Calls in Dune",
    "A short introduction to external API calls in Dune and where they fit in a dashboard workflow.",
    "shWx3DDveg0",
    "1 min",
  ),
  lessonItem(
    "how-to-use-external-api-calls-in-dune",
    "How to Use External API Calls in Dune",
    "A practical walkthrough of using external API calls in Dune.",
    "bhlISIxGpQo",
    "21 min",
  ),
  lessonItem(
    "how-to-add-use-dashboard-parameters-in-sql",
    "How to Add & Use Dashboard Parameters in SQL",
    "How dashboard parameters work in Dune and how they can make SQL queries interactive.",
    "Ya9ypRLKU5k",
    "16 min",
  ),
  lessonItem(
    "how-to-add-custom-images-to-dune-analytics-dashboard",
    "How to Add Custom Images to Your Dune Analytics Dashboard",
    "How custom images can support a clearer visual layout on a Dune dashboard.",
    "e3SyjYobvlo",
    "9 min",
  ),
  lessonItem(
    "how-to-add-dynamic-date-presets-in-dune-analytics",
    "How to Add Dynamic Date Presets in Dune Analytics",
    "How dynamic date presets can keep a Dune dashboard current.",
    "wPUXCf-FCAs",
    "21 min",
  ),
  lessonItem(
    "how-to-handle-null-values-in-dune-sql",
    "How to Handle NULL Values in Dune SQL",
    "How NULL handling patterns can keep Dune SQL queries more robust.",
    "YtR0k8YY2d4",
    null,
  ),
];

export const LIBRARY_COURSES: LibraryItem[] = [
  {
    id: `course:${FEATURED_FREE_COURSE_SLUG}`,
    category: "courses",
    title: FEATURED_FREE_COURSE.title,
    description: FEATURED_FREE_COURSE.description,
    href: `/courses/${FEATURED_FREE_COURSE_SLUG}`,
    cta: "Open course",
    thumbnail: FEATURED_FREE_COURSE.thumbnail,
    duration: FEATURED_FREE_COURSE.duration,
    badge: "Free course",
  },
];

export const LIBRARY_COMING_SOON: LibraryItem[] = [
  {
    id: "research:investor-ready-research-report",
    category: "research",
    title: "Investor Ready Research Report",
    description:
      "A walkthrough of how to structure research that is ready for investors. It will live here as a resource, not as another card in the course catalog.",
    href: siteConfig.links.youtube,
    cta: "YouTube channel",
    comingSoon: true,
    badge: "Coming soon",
  },
  {
    id: "career:career-acceleration",
    category: "career",
    title: "Career acceleration",
    description:
      "Sessions on building a data career, from query skills to presenting your work. Specific videos will be added here instead of mixing them into Courses.",
    href: siteConfig.links.youtube,
    cta: "YouTube channel",
    comingSoon: true,
    badge: "Coming soon",
  },
  {
    id: "webinars:recordings",
    category: "webinars",
    title: "Webinar recordings",
    description:
      "Past webinar recordings will appear here. Live sessions stay on Events so this page does not become a second calendar.",
    href: "/events",
    cta: "See events",
    comingSoon: true,
    badge: "Coming soon",
  },
];

export const STATIC_LIBRARY_ITEMS: LibraryItem[] = [
  ...LIBRARY_COURSES,
  ...LIBRARY_TUTORIALS,
  ...LIBRARY_COMING_SOON,
];

export function parseLibraryCategory(value: string | null): LibraryCategory | "all" {
  if (value && (LIBRARY_CATEGORIES as readonly string[]).includes(value)) {
    return value as LibraryCategory;
  }
  return "all";
}

export function libraryItemsForCategory(
  items: LibraryItem[],
  category: LibraryCategory | "all",
) {
  if (category === "all") return items;
  return items.filter((item) => item.category === category);
}
