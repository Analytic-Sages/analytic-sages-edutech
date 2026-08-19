import { AppShell } from "@/components/layout/app-shell";
import { RequireAdmin } from "@/components/auth/require-admin";
import { RequireAuth } from "@/components/auth/require-auth";
import { adminNav } from "@/config/navigation";

export const metadata = { robots: { index: false, follow: false } };

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <RequireAdmin>
        <AppShell nav={adminNav}>{children}</AppShell>
      </RequireAdmin>
    </RequireAuth>
  );
}
