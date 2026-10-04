import { AdminCourseEditor } from "@/components/admin/admin-course-editor";

export const metadata = { title: "Edit Course" };

export default async function EditCoursePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return <AdminCourseEditor slug={slug} />;
}