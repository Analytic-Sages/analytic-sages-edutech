import type { Course } from "@/types/course";

export function getFirstLesson(course: Course) {
  return course.modules.flatMap((module) => module.lessons)[0];
}

/** Enrolled CTA: open first lesson when curriculum exists, otherwise course detail. */
export function getContinueHref(course: Course): string {
  if (course.resumeLessonSlug) {
    return `/courses/${course.slug}/learn/${course.resumeLessonSlug}`;
  }
  const firstLesson = getFirstLesson(course);
  if (firstLesson) {
    return `/courses/${course.slug}/learn/${firstLesson.id}`;
  }
  return `/courses/${course.slug}`;
}
