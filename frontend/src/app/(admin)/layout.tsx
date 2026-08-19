import { AdminPortal } from "@/components/auth/admin-portal";
import { RequireAuth } from "@/components/auth/require-auth";

export const metadata = { robots: { index: false, follow: false } };

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AdminPortal>{children}</AdminPortal>
    </RequireAuth>
  );
}
