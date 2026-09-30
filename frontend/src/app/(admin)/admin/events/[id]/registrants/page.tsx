import { AdminEventRegistrants } from "@/components/admin/admin-event-registrants";

export const metadata = { title: "Event registrants" };

type Props = { params: Promise<{ id: string }> };

export default async function AdminEventRegistrantsPage({ params }: Props) {
  const { id } = await params;
  return <AdminEventRegistrants eventId={id} />;
}
