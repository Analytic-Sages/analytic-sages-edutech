import { AdminCourseCardsContent } from "@/components/admin/admin-course-cards-content";

export const metadata = { title: "Course Card Manager", robots: { index: false, follow: false } };

export default function AdminCourseCardsPage() {
  return <AdminCourseCardsContent />;
}
