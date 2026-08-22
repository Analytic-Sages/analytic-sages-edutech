"use client";

import { AdminInstructorEditor } from "@/components/admin/admin-instructor-editor";

export function AdminCohortInstructorsContent({ slug, name }: { slug: string; name?: string }) {
  return <AdminInstructorEditor key={slug} kind="cohort" slug={slug} title={name || slug} />;
}
