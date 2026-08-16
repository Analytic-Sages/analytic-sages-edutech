"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { setAccessToken } from "@/lib/api";
import { setLastAuthMethod } from "@/lib/auth-method";

function AuthCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("access_token");
    const next = searchParams.get("next") || "/dashboard";
    const method = searchParams.get("method");

    if (!token) {
      queueMicrotask(() => setError("Missing access token from Google login."));
      return;
    }

    setAccessToken(token);
    if (method === "google") {
      setLastAuthMethod("google");
    }
    router.replace(next.startsWith("/") ? next : "/dashboard");
  }, [router, searchParams]);

  if (error) {
    return (
      <div className="mx-auto max-w-sm space-y-4 p-8 text-center">
        <p className="text-destructive">{error}</p>
        <a href="/login" className="text-sm font-medium text-brand-navy underline">
          Back to login
        </a>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3 p-12 text-muted-foreground">
      <Loader2 className="size-6 animate-spin" />
      Completing sign-in…
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-muted-foreground">Completing sign-in…</div>
      }
    >
      <AuthCallbackInner />
    </Suspense>
  );
}
