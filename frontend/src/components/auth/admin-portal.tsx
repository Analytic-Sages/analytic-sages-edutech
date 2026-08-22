"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { adminNav, editorNav, operationsNav } from "@/config/navigation";
import { ApiError, getMe } from "@/lib/api";

export function AdminPortal({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [nav, setNav] = useState(adminNav);

  useEffect(() => {
    let cancelled = false;

    getMe()
      .then((user) => {
        if (cancelled) return;
        if (user.role === "admin") {
          setNav(adminNav);
          setReady(true);
          return;
        }
        if (user.role === "editor") {
          if (!pathname.startsWith("/admin/insights")) {
            router.replace("/admin/insights");
            return;
          }
          setNav(editorNav);
          setReady(true);
          return;
        }
        if (user.role === "operations") {
          const allowed =
            pathname.startsWith("/admin/events") ||
            pathname.startsWith("/admin/courses") ||
            pathname.startsWith("/admin/cohorts/");
          if (!allowed) {
            router.replace("/admin/events");
            return;
          }
          setNav(operationsNav);
          setReady(true);
          return;
        }
        router.replace(
          user.role === "instructor" ? "/staff" : user.role === "author" ? "/studio" : "/dashboard"
        );
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
  }, [pathname, router]);

  if (!ready) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Checking access…
      </div>
    );
  }

  return <AppShell nav={nav}>{children}</AppShell>;
}
