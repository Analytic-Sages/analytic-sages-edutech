"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAccessToken } from "@/hooks/use-access-token";
import { ensureSession } from "@/lib/api";

/**
 * Client-side guard for protected layouts.
 * Waits for session bootstrap (local token or silent refresh) before redirecting.
 */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const token = useAccessToken();
  const [bootstrapped, setBootstrapped] = useState(false);

  useEffect(() => {
    let cancelled = false;
    ensureSession().then((session) => {
      if (cancelled) return;
      setBootstrapped(true);
      if (!session) {
        const next = pathname || "/dashboard";
        router.replace(`/login?next=${encodeURIComponent(next)}`);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [pathname, router]);

  if (!bootstrapped || !token) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Checking sign-in…
      </div>
    );
  }

  return <>{children}</>;
}
