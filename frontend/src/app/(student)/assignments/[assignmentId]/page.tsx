import { AssignmentDetailContent } from "@/components/student/assignment-detail-content";

export const metadata = { title: "Assignment" };

export default async function AssignmentPage({
  params,
}: {
  params: Promise<{ assignmentId: string }>;
}) {
  const { assignmentId } = await params;
  return <AssignmentDetailContent assignmentId={assignmentId} />;
}
