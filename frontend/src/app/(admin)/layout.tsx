import { AppShell } from "@/components/layout/app-shell";
import { adminNav } from "@/config/navigation";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <AppShell nav={adminNav}>{children}</AppShell>;
}
