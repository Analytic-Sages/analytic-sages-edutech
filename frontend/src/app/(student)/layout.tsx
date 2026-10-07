import { RequireAuth } from "@/components/auth/require-auth";
import { LearningShell } from "@/components/layout/learning-shell";

export const metadata = { robots: { index: false, follow: false } };

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <LearningShell>{children}</LearningShell>
    </RequireAuth>
  );
}
