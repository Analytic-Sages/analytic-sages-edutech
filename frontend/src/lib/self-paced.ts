import type { SelfPacedCourseCard, SelfPacedCoursePublic, SelfPacedEnrollment } from "@/lib/api";
import type { Course } from "@/types/course";

export const FEATURED_FREE_COURSE_SLUG = "dune-analytics-practical-sql-dashboard-techniques";

export const FEATURED_FREE_COURSE: SelfPacedCourseCard = {
  id: "featured-dune-analytics",
  slug: FEATURED_FREE_COURSE_SLUG,
  title: "Dune Analytics: Practical SQL & Dashboard Techniques",
  description:
    "Learn practical techniques for building more powerful blockchain analytics dashboards with Dune. This free self-paced course covers external API calls, dashboard parameters, dynamic date filters, custom dashboard images, and handling NULL values in Dune SQL.",
  thumbnail: "/dune-analytics-practical-sql-dashboard-techniques.png",
  category: "Blockchain",
  difficulty: "Beginner to Intermediate",
  duration: "~70 minutes",
  estimated_minutes: 70,
  lessons_count: 6,
  price: 0,
  currency: "USD",
  is_free: true,
  delivery_type: "self_paced",
  certificate_enabled: false,
};

export function mergeFreeCatalog(rows: SelfPacedCourseCard[]): SelfPacedCourseCard[] {
  const free = rows.filter((course) => course.is_free);
  if (free.some((course) => course.slug === FEATURED_FREE_COURSE_SLUG)) return free;
  return [FEATURED_FREE_COURSE, ...free];
}

function featuredLesson(
  slug: string,
  title: string,
  order_index: number,
  duration_seconds: number | null,
  subtitle: string | null = null,
): SelfPacedCoursePublic["modules"][number]["lessons"][number] {
  return {
    id: slug,
    slug,
    title,
    subtitle,
    duration_seconds,
    order_index,
    video_provider: "youtube",
    video_id: null,
    completed: false,
  };
}

export const FEATURED_FREE_COURSE_PUBLIC: SelfPacedCoursePublic = {
  ...FEATURED_FREE_COURSE,
  long_description:
    "Learn practical techniques for building more powerful blockchain analytics dashboards with Dune, from external API calls and dashboard parameters to dynamic date filters and robust SQL.",
  published: true,
  enrolled: false,
  completed: false,
  progress_percent: 0,
  lessons_completed: 0,
  resume_lesson_slug: null,
  modules: [
    {
      id: "m1",
      title: "Working With External APIs in Dune",
      description: "Call external APIs from Dune and use the results in your analytics workflow.",
      order_index: 1,
      lessons: [
        featuredLesson(
          "introduction-to-external-api-calls-in-dune",
          "Introduction to External API Calls in Dune",
          1,
          69,
        ),
        featuredLesson(
          "how-to-use-external-api-calls-in-dune",
          "How to Use External API Calls in Dune",
          2,
          1289,
        ),
      ],
    },
    {
      id: "m2",
      title: "Building Interactive Dune Dashboards",
      description: "Make dashboards interactive with parameters, images, and dynamic date filters.",
      order_index: 2,
      lessons: [
        featuredLesson(
          "how-to-add-use-dashboard-parameters-in-sql",
          "How to Add & Use Dashboard Parameters in SQL",
          1,
          944,
        ),
        featuredLesson(
          "how-to-add-custom-images-to-dune-analytics-dashboard",
          "How to Add Custom Images to Your Dune Analytics Dashboard",
          2,
          567,
        ),
        featuredLesson(
          "how-to-add-dynamic-date-presets-in-dune-analytics",
          "How to Add Dynamic Date Presets in Dune Analytics",
          3,
          1250,
          "Today / 7D / 30D",
        ),
      ],
    },
    {
      id: "m3",
      title: "Writing More Robust Dune SQL",
      description: "Keep Dune SQL reliable when values are missing or undefined.",
      order_index: 3,
      lessons: [
        featuredLesson(
          "how-to-handle-null-values-in-dune-sql",
          "How to Handle NULL Values in Dune SQL",
          1,
          null,
          "COALESCE, NULLIF & Safe Divide",
        ),
      ],
    },
  ],
};

export function featuredSelfPacedCourse(slug: string): SelfPacedCoursePublic | null {
  return slug === FEATURED_FREE_COURSE_SLUG ? FEATURED_FREE_COURSE_PUBLIC : null;
}

export function formatDurationSeconds(seconds: number | null | undefined) {
  if (!seconds || seconds <= 0) return null;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins >= 60) {
    const hours = Math.floor(mins / 60);
    const rest = mins % 60;
    return `${hours}:${String(rest).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

export function firstLessonSlug(course: SelfPacedCoursePublic) {
  return course.modules.flatMap((module) => module.lessons)[0]?.slug ?? null;
}

export function selfPacedLearnHref(course: {
  slug: string;
  resume_lesson_slug?: string | null;
  modules?: SelfPacedCoursePublic["modules"];
}) {
  const slug =
    course.resume_lesson_slug ||
    course.modules?.flatMap((module) => module.lessons)[0]?.slug;
  if (!slug) return `/courses/${course.slug}`;
  return `/courses/${course.slug}/learn/${slug}`;
}

export function mapSelfPacedEnrollmentToCourse(item: SelfPacedEnrollment): Course {
  const resume = item.resume_lesson_slug;
  return {
    id: item.course.id,
    slug: item.course.slug,
    title: item.course.title,
    description: item.course.description,
    longDescription: item.course.description,
    thumbnail: item.course.thumbnail || "/dune-analytics-practical-sql-dashboard-techniques.png",
    category: item.course.category,
    difficulty: "Beginner",
    duration: item.course.duration,
    lessonsCount: item.course.lessons_count,
    price: item.course.price,
    currency: item.course.currency,
    instructor: { name: "Analytic Sages", title: "Instructor", avatar: "AS" },
    rating: 0,
    studentsCount: 0,
    modules: resume
      ? [{ id: "resume", title: "Resume", lessons: [{ id: resume, title: "Continue", duration: "" }] }]
      : [],
    skills: [],
    requirements: [],
    enrolled: true,
    progress: item.progress_percent,
    comingSoon: false,
    isFree: item.course.is_free,
    resumeLessonSlug: resume ?? undefined,
    completed: Boolean(item.completed_at) || item.status === "completed",
    lessonsCompleted: item.lessons_completed,
    lessonsTotal: item.lessons_total,
  };
}

export function catalogCardFromApi(course: SelfPacedCourseCard): Course {
  return {
    id: course.id,
    slug: course.slug,
    title: course.title,
    description: course.description,
    longDescription: course.description,
    thumbnail: course.thumbnail || "/dune-analytics-practical-sql-dashboard-techniques.png",
    category: course.category,
    difficulty: "Beginner",
    duration: course.duration,
    lessonsCount: course.lessons_count,
    price: course.price,
    currency: course.currency,
    instructor: { name: "Analytic Sages", title: "Instructor", avatar: "AS" },
    rating: 0,
    studentsCount: 0,
    modules: [],
    skills: [],
    requirements: [],
    comingSoon: false,
    isFree: course.is_free,
  };
}
