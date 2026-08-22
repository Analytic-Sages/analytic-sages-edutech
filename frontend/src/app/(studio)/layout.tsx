import { RequireAuth } from "@/components/auth/require-auth";
import { AppShell } from "@/components/layout/app-shell";
import { studioNav } from "@/config/navigation";

export const metadata = { robots: { index: false, follow: false }, title: "Studio" };

export default function StudioLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppShell nav={studioNav}>{children}</AppShell>
    </RequireAuth>
  );
}
