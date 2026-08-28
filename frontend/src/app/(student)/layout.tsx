import { AppShell } from "@/components/layout/app-shell";
import { RequireAuth } from "@/components/auth/require-auth";
import { publicStudentNav } from "@/config/navigation";

export const metadata = { robots: { index: false, follow: false } };

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppShell nav={publicStudentNav()}>{children}</AppShell>
    </RequireAuth>
  );
}
