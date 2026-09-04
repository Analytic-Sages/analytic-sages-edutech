"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { trackReferral } from "@/lib/api";

export function ReferralLanding() {
  const params = useParams<{ code: string }>();
  const router = useRouter();
  const [message, setMessage] = useState("Opening your referral link…");

  useEffect(() => {
    const code = String(params.code || "").trim();
    if (!code) {
      router.replace("/programs");
      return;
    }
    let cancelled = false;
    trackReferral(code, `/ref/${code}`, "/programs")
      .then((res) => {
        if (cancelled) return;
        router.replace(res.redirect_path || "/programs");
      })
      .catch(() => {
        if (cancelled) return;
        setMessage("This referral link is unavailable. Redirecting…");
        router.replace("/programs");
      });
    return () => {
      cancelled = true;
    };
  }, [params.code, router]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-muted-foreground">
      <Loader2 className="size-6 animate-spin text-brand-orange" />
      <p className="text-sm">{message}</p>
    </div>
  );
}
