"use client";

import { RequireAuth } from "@/components/auth/require-auth";
import { AppShell } from "@/components/layout/app-shell";
import { partnerNav } from "@/config/navigation";

export default function PartnerLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppShell nav={partnerNav}>{children}</AppShell>
    </RequireAuth>
  );
}
