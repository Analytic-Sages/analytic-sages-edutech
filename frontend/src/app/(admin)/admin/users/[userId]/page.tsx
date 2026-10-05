import { AdminUserDetailContent } from "@/components/admin/admin-user-detail-content";

export const metadata = { title: "User profile" };

export default async function AdminUserDetailPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = await params;
  return <AdminUserDetailContent userId={userId} />;
}
