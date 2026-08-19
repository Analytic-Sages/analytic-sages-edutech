import type { SelfPacedCourseCard, SelfPacedCoursePublic, SelfPacedEnrollment } from "@/lib/api";
import type { Course } from "@/types/course";

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
