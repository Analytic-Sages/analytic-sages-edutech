import { AdminEventForm } from "@/components/admin/admin-event-form";

export const metadata = { title: "Edit event" };

type Props = { params: Promise<{ id: string }> };

export default async function AdminEditEventPage({ params }: Props) {
  const { id } = await params;
  return <AdminEventForm eventId={id} />;
}
