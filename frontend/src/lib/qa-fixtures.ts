/** Pytest leftovers that must never appear on public marketing pages. */

const QA_COURSE_TITLES = new Set(["Test Self-Paced Course", "Test Instructor Course"]);
const QA_EVENT_TITLES = new Set([
  "Ops Updated Event",
  "Coming Soon Workshop",
  "Ops Coming Soon",
  "Admin Created Workshop",
  "Test Dune Workshop",
]);

export function isQaCatalogCourse(item: { slug: string; title: string }) {
  return item.slug.startsWith("test-") || QA_COURSE_TITLES.has(item.title);
}

export function isQaPublicEvent(item: { slug: string; title: string }) {
  return (
    item.slug.startsWith("test-") ||
    item.slug.startsWith("ops-event-") ||
    QA_EVENT_TITLES.has(item.title)
  );
}
