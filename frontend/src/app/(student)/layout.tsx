import { AppShell } from "@/components/layout/app-shell";
import { studentNav } from "@/config/navigation";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return <AppShell nav={studentNav}>{children}</AppShell>;
}
