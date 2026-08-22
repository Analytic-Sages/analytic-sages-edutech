"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, Loader2, Mail } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch, persistSession, setAccessToken, type AuthResponse } from "@/lib/api";
import { resolvePostLoginPath } from "@/lib/auth-redirect";

function VerifyEmailInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const emailFromQuery = searchParams.get("email") || "";
  const rawNext = searchParams.get("next") || "/dashboard";
  const nextPath =
    rawNext.startsWith("/") && !rawNext.startsWith("//") ? rawNext : "/dashboard";

  const [status, setStatus] = useState<"idle" | "verifying" | "success" | "error">(
    token ? "verifying" : "idle"
  );
  const [message, setMessage] = useState<string | null>(null);
  const [email, setEmail] = useState(emailFromQuery);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const result = await apiFetch<AuthResponse>("/api/v1/auth/verify-email", {
          method: "POST",
          auth: false,
          body: JSON.stringify({ token }),
        });
        if (cancelled) return;
        setAccessToken(result.access_token);
        await persistSession();
        if (cancelled) return;
        setStatus("success");
        setMessage("Email verified. Continuing…");
        router.replace(resolvePostLoginPath(result.user.role, nextPath));
      } catch (err) {
        if (!cancelled) {
          setStatus("error");
          setMessage(err instanceof ApiError ? err.detail : "Verification failed");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, nextPath, router]);

  async function handleResend() {
    setResending(true);
    setMessage(null);
    try {
      const result = await apiFetch<{ message: string }>("/api/v1/auth/resend-verification", {
        method: "POST",
        auth: false,
        body: JSON.stringify({
          email,
          next: nextPath !== "/dashboard" ? nextPath : null,
        }),
      });
      setMessage(result.message);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.detail : "Could not resend verification email");
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-sm space-y-8 text-center">
      <Logo size="md" href="/" className="mx-auto" />
      <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-brand-navy/10">
        {status === "verifying" || status === "success" ? (
          status === "success" ? (
            <CheckCircle2 className="size-8 text-success" />
          ) : (
            <Loader2 className="size-8 animate-spin text-brand-navy" />
          )
        ) : (
          <Mail className="size-8 text-brand-navy" />
        )}
      </div>
      <div>
        <h1 className="font-heading text-2xl font-bold">
          {status === "success"
            ? "Email verified"
            : status === "verifying"
              ? "Verifying…"
              : "Check your email"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {status === "success"
            ? "You're signed in. Taking you to your dashboard."
            : status === "verifying"
              ? "Confirming your verification link."
              : "We sent a verification link to your inbox. Open it in this browser to activate your account."}
        </p>
      </div>

      {message && (
        <p
          className={
            status === "error" ? "text-sm text-destructive" : "text-sm text-muted-foreground"
          }
        >
          {message}
        </p>
      )}

      {status === "success" ? (
        <p className="text-sm text-muted-foreground">Redirecting…</p>
      ) : (
        <div className="space-y-4 text-left">
          <div className="space-y-2">
            <Label htmlFor="email">Resend verification</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <Button
            type="button"
            variant="outline"
            className="h-11 w-full"
            disabled={resending || !email}
            onClick={handleResend}
          >
            {resending ? "Sending…" : "Resend verification email"}
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            <Link href="/login" className="font-medium text-brand-navy hover:underline dark:text-brand-orange">
              Back to sign in
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-muted-foreground">
          <Loader2 className="mx-auto size-6 animate-spin" />
        </div>
      }
    >
      <VerifyEmailInner />
    </Suspense>
  );
}
