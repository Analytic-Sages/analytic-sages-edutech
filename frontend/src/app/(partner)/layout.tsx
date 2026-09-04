"use client";

import { RequireAuth } from "@/components/auth/require-auth";
import { RequirePartnersAccess } from "@/components/auth/require-partners-access";
import { AppShell } from "@/components/layout/app-shell";
import { partnerNav } from "@/config/navigation";

export default function PartnerLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <RequirePartnersAccess>
        <AppShell nav={partnerNav}>{children}</AppShell>
      </RequirePartnersAccess>
    </RequireAuth>
  );
}
