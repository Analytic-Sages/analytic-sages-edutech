import { AppShell } from "@/components/layout/app-shell";
import { RequireAuth } from "@/components/auth/require-auth";
import { studentNav } from "@/config/navigation";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppShell nav={studentNav}>{children}</AppShell>
    </RequireAuth>
  );
}
