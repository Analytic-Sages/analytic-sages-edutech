"use client";

import { AdminInstructorEditor } from "@/components/admin/admin-instructor-editor";
import { AdminTutorAccessEditor } from "@/components/admin/admin-tutor-access-editor";

export function AdminCohortInstructorsContent({ slug, name }: { slug: string; name?: string }) {
  const title = name || slug;
  return (
    <div className="space-y-8">
      <AdminTutorAccessEditor kind="cohort" slug={slug} title={title} />
      <AdminInstructorEditor key={slug} kind="cohort" slug={slug} title={title} />
    </div>
  );
}
