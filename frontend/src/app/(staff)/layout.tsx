import { AppShell } from "@/components/layout/app-shell";
import { RequireAuth } from "@/components/auth/require-auth";
import { RequireStaff } from "@/components/auth/require-staff";
import { staffNav } from "@/config/navigation";

export const metadata = { robots: { index: false, follow: false } };

export default function StaffLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <RequireStaff>
        <AppShell nav={staffNav}>{children}</AppShell>
      </RequireStaff>
    </RequireAuth>
  );
}
