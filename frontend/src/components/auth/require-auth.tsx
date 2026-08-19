"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAccessToken } from "@/hooks/use-access-token";
import { clearAccessToken } from "@/lib/api";

/**
 * Client-side guard for protected layouts.
 * Middleware checks the session cookie; this ensures a real access token exists.
 */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const token = useAccessToken();

  useEffect(() => {
    if (token) return;
    clearAccessToken();
    const next = pathname || "/dashboard";
    router.replace(`/login?next=${encodeURIComponent(next)}`);
  }, [token, pathname, router]);

  if (!token) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Checking sign-in…
      </div>
    );
  }

  return <>{children}</>;
}
