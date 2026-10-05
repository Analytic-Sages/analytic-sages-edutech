"use client";

import { AdminInstructorEditor } from "@/components/admin/admin-instructor-editor";
import { AdminTutorAccessEditor } from "@/components/admin/admin-tutor-access-editor";

export function AdminCourseInstructorsContent({ slug }: { slug: string }) {
  return (
    <div className="space-y-8">
      <AdminTutorAccessEditor kind="course" slug={slug} title={slug} />
      <AdminInstructorEditor key={slug} kind="course" slug={slug} title={slug} />
    </div>
  );
}
