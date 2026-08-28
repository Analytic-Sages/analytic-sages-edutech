import { AdminOpportunityForm } from "@/components/admin/admin-opportunity-form";

export const metadata = { title: "Edit opportunity" };

type Props = { params: Promise<{ id: string }> };

export default async function AdminEditOpportunityPage({ params }: Props) {
  const { id } = await params;
  return <AdminOpportunityForm opportunityId={id} />;
}
