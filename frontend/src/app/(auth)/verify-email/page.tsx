"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Loader2, Mail } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api";

function VerifyEmailInner() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const emailFromQuery = searchParams.get("email") || "";

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
        await apiFetch<{ message: string }>("/api/v1/auth/verify-email", {
          method: "POST",
          auth: false,
          body: JSON.stringify({ token }),
        });
        if (!cancelled) {
          setStatus("success");
          setMessage("Email verified. You can sign in now.");
        }
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
  }, [token]);

  async function handleResend() {
    setResending(true);
    setMessage(null);
    try {
      const result = await apiFetch<{ message: string }>("/api/v1/auth/resend-verification", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ email }),
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
        {status === "verifying" ? (
          <Loader2 className="size-8 animate-spin text-brand-navy" />
        ) : status === "success" ? (
          <CheckCircle2 className="size-8 text-success" />
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
            ? "Your account is ready. Sign in to continue."
            : status === "verifying"
              ? "Confirming your verification link."
              : "We sent a verification link to your inbox. Open it to activate your account, then sign in."}
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
        <ButtonLink
          href={`/login${searchParams.get("next") ? `?next=${encodeURIComponent(searchParams.get("next")!)}` : ""}`}
          className="bg-brand-navy text-white hover:bg-brand-navy/90"
        >
          Sign in
        </ButtonLink>
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
