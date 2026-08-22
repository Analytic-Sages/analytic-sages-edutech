import { AdminCourseInstructorsContent } from "@/components/admin/admin-course-instructors-content";

export const metadata = { title: "Course instructors" };

type Props = { params: Promise<{ slug: string }> };

export default async function AdminCourseInstructorsPage({ params }: Props) {
  const { slug } = await params;
  return <AdminCourseInstructorsContent slug={slug} />;
}
