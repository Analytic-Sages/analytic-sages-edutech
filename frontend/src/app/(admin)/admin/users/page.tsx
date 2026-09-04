import { Suspense } from "react";
import { AdminUsersContent } from "@/components/admin/admin-users-content";

export const metadata = { title: "Users" };

export default function AdminUsersPage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-muted-foreground">Loading users…</div>}>
      <AdminUsersContent />
    </Suspense>
  );
}
