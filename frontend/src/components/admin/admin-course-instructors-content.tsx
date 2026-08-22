"use client";

import { AdminInstructorEditor } from "@/components/admin/admin-instructor-editor";

export function AdminCourseInstructorsContent({ slug }: { slug: string }) {
  return <AdminInstructorEditor kind="course" slug={slug} title={slug} />;
}
