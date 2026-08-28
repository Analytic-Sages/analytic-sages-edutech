import { siteConfig } from "@/config/site";
import type { EventCardPublic, PublicCohortCard, SelfPacedCourseCard } from "@/lib/api";
import type { InsightCard } from "@/lib/insights";
import type { OpportunityCard } from "@/lib/opportunities";
import { courses } from "@/lib/mock-data";
import {
  FEATURED_FREE_COURSE_PUBLIC,
  mergeFreeCatalog,
} from "@/lib/self-paced";
import { listPublicProgramPaths, getProgramPage, getProgramPageHref } from "@/lib/program-pages";

export type SearchKind = "course" | "program" | "event" | "lesson" | "blog" | "community" | "opportunity";

export type SearchHit = {
  id: string;
  kind: SearchKind;
  title: string;
  description: string;
  href: string;
  score: number;
};

const KIND_LABEL: Record<SearchKind, string> = {
  course: "Course",
  program: "Program",
  event: "Event",
  lesson: "Lesson",
  blog: "Insights",
  community: "Community",
  opportunity: "Opportunity",
};

export function searchKindLabel(kind: SearchKind) {
  return KIND_LABEL[kind];
}

function normalize(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function scoreMatch(query: string, fields: string[]) {
  const q = normalize(query);
  if (!q) return 0;
  const haystack = normalize(fields.filter(Boolean).join(" "));
  if (!haystack) return 0;
  if (haystack === q) return 100;
  if (haystack.startsWith(q)) return 80;
  if (haystack.includes(q)) return 60;
  const terms = q.split(" ").filter(Boolean);
  const hits = terms.filter((term) => haystack.includes(term)).length;
  if (hits === 0) return 0;
  return Math.round((hits / terms.length) * 50);
}

export function searchCatalog(query: string, sources: {
  courses: SelfPacedCourseCard[];
  cohorts: PublicCohortCard[];
  events: EventCardPublic[];
  insights?: InsightCard[];
  opportunities?: OpportunityCard[];
}): SearchHit[] {
  const q = query.trim();
  if (q.length < 2) return [];

  const hits: SearchHit[] = [];
  const seen = new Set<string>();

  function push(hit: Omit<SearchHit, "score"> & { fields: string[] }) {
    const score = scoreMatch(q, hit.fields);
    if (score <= 0) return;
    if (seen.has(hit.id)) return;
    seen.add(hit.id);
    hits.push({
      id: hit.id,
      kind: hit.kind,
      title: hit.title,
      description: hit.description,
      href: hit.href,
      score,
    });
  }

  for (const course of mergeFreeCatalog(sources.courses)) {
    push({
      id: `course:${course.slug}`,
      kind: "course",
      title: course.title,
      description: course.description,
      href: `/courses/${course.slug}`,
      fields: [course.title, course.description, course.slug, course.category],
    });
  }

  for (const course of courses) {
    push({
      id: `course:${course.slug}`,
      kind: "course",
      title: course.title,
      description: course.description,
      href: `/courses/${course.slug}`,
      fields: [course.title, course.description, course.longDescription, ...(course.skills ?? [])],
    });
    for (const courseModule of course.modules) {
      for (const lesson of courseModule.lessons) {
        push({
          id: `lesson:${course.slug}:${lesson.id}`,
          kind: "lesson",
          title: lesson.title,
          description: `${course.title} · ${courseModule.title}`,
          href: `/courses/${course.slug}`,
          fields: [lesson.title, courseModule.title, course.title],
        });
      }
    }
  }

  push({
    id: "program:instructor-led",
    kind: "program",
    title: "Instructor-Led Training",
    description: "Live cohort classes with Analytic Sages instructors.",
    href: "/instructor-led",
    fields: ["instructor led", "cohort", "live class", "sql blockchain", "classroom"],
  });

  for (const path of listPublicProgramPaths()) {
    const slug = path.replace(/^\/programs\//, "");
    const page = getProgramPage(slug);
    if (!page) continue;
    push({
      id: `program:${page.pageSlug}`,
      kind: "program",
      title: page.headline,
      description: page.support,
      href: page.canonicalPath,
      fields: [page.headline, page.support, page.eyebrow, page.pageSlug],
    });
  }

  for (const cohort of sources.cohorts) {
    push({
      id: `program:${cohort.slug}`,
      kind: "program",
      title: cohort.course_title || cohort.name,
      description: cohort.description,
      href: getProgramPageHref(cohort.slug) || "/instructor-led",
      fields: [cohort.name, cohort.description, cohort.course_title || "", cohort.slug],
    });
  }

  for (const event of sources.events) {
    push({
      id: `event:${event.slug}`,
      kind: "event",
      title: event.title,
      description: event.short_description,
      href: `/events/${event.slug}`,
      fields: [event.title, event.short_description, event.slug, String(event.event_type)],
    });
  }

  push({
    id: "opportunity:hub",
    kind: "opportunity",
    title: "Opportunities Hub",
    description: "Jobs, internships, fellowships, grants, and research mapped to Analytic Sages pathways.",
    href: "/opportunities",
    fields: ["opportunities", "jobs", "internships", "fellowships", "grants", "hackathons", "career"],
  });

  for (const opportunity of sources.opportunities || []) {
    push({
      id: `opportunity:${opportunity.slug}`,
      kind: "opportunity",
      title: opportunity.title,
      description: opportunity.organization_name,
      href: `/opportunities/${opportunity.slug}`,
      fields: [
        opportunity.title,
        opportunity.organization_name,
        opportunity.slug,
        opportunity.opportunity_type,
        opportunity.primary_career_path?.name || "",
      ],
    });
  }

  for (const courseModule of FEATURED_FREE_COURSE_PUBLIC.modules) {
    for (const lesson of courseModule.lessons) {
      push({
        id: `lesson:${lesson.slug}`,
        kind: "lesson",
        title: lesson.title,
        description: courseModule.title,
        href: `/courses/${FEATURED_FREE_COURSE_PUBLIC.slug}`,
        fields: [lesson.title, lesson.subtitle || "", courseModule.title, FEATURED_FREE_COURSE_PUBLIC.title],
      });
    }
  }

  for (const post of sources.insights || []) {
    push({
      id: `blog:${post.slug}`,
      kind: "blog",
      title: post.title,
      description: post.excerpt,
      href: `/insights/${post.slug}`,
      fields: [post.title, post.excerpt, post.category],
    });
  }

  push({
    id: "community:discord",
    kind: "community",
    title: "Discord community",
    description: "Join the Analytic Sages Discord.",
    href: siteConfig.links.discord,
    fields: ["discord", "community", "chat"],
  });
  push({
    id: "community:telegram",
    kind: "community",
    title: "Telegram community",
    description: "Join the Analytic Sages Telegram group.",
    href: siteConfig.links.telegram,
    fields: ["telegram", "community", "chat"],
  });
  push({
    id: "community:youtube",
    kind: "community",
    title: "YouTube channel",
    description: "Watch Analytic Sages on YouTube.",
    href: siteConfig.links.youtube,
    fields: ["youtube", "community", "videos"],
  });

  return hits.sort((a, b) => b.score - a.score || a.title.localeCompare(b.title)).slice(0, 8);
}
