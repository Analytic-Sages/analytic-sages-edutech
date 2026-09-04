"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { ApiError, getMe } from "@/lib/api";
import { isPartnersPublic } from "@/lib/feature-flags";

/**
 * When partners are not public, only admins may open /partners and related marketing pages.
 * When public, anyone can view.
 */
export function RequirePartnersAccess({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(isPartnersPublic());

  useEffect(() => {
    if (isPartnersPublic()) {
      return;
    }

    let cancelled = false;
    getMe()
      .then((user) => {
        if (cancelled) return;
        if (user.role !== "admin") {
          router.replace("/dashboard");
          return;
        }
        setReady(true);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 403) {
          router.replace("/dashboard");
          return;
        }
        router.replace(`/login?next=${encodeURIComponent(pathname || "/partners")}`);
      });

    return () => {
      cancelled = true;
    };
  }, [pathname, router]);

  if (!ready) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Checking access…
      </div>
    );
  }

  return <>{children}</>;
}
