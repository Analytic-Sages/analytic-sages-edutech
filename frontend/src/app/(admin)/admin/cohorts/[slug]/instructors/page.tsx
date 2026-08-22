import { AdminCohortInstructorsContent } from "@/components/admin/admin-cohort-instructors-content";

export const metadata = { title: "Cohort instructors" };

type Props = { params: Promise<{ slug: string }> };

export default async function AdminCohortInstructorsPage({ params }: Props) {
  const { slug } = await params;
  return <AdminCohortInstructorsContent slug={slug} />;
}
