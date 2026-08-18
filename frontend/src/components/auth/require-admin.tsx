"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { ApiError, getMe } from "@/lib/api";

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    getMe()
      .then((user) => {
        if (cancelled) return;
        if (user.role !== "admin") {
          router.replace(user.role === "instructor" ? "/staff" : "/dashboard");
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
        router.replace("/login?next=/admin");
      });

    return () => {
      cancelled = true;
    };
  }, [router]);

  if (!ready) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Checking admin access…
      </div>
    );
  }

  return <>{children}</>;
}
