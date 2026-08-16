"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, mockGoogleLogin, setAccessToken } from "@/lib/api";
import { setLastAuthMethod } from "@/lib/auth-method";

function GoogleMockInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/dashboard";

  const [email, setEmail] = useState("learner@gmail.com");
  const [fullName, setFullName] = useState("Google Learner");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await mockGoogleLogin(email, fullName);
      setAccessToken(result.access_token);
      setLastAuthMethod("google");
      router.replace(nextPath.startsWith("/") ? nextPath : "/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Mock Google login failed");
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-sm space-y-6">
      <div className="flex flex-col items-center space-y-2 text-center">
        <Logo size="md" href="/" />
        <h1 className="font-heading text-2xl font-bold">Mock Google sign-in</h1>
        <p className="text-sm text-muted-foreground">
          Development only. Add Google OAuth keys later to use real Google login.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border bg-card p-6 shadow-card">
        <div className="space-y-2">
          <Label htmlFor="full_name">Name</Label>
          <Input
            id="full_name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Google email</Label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button
          type="submit"
          disabled={loading}
          className="h-11 w-full bg-brand-navy text-white hover:bg-brand-navy/90"
        >
          {loading ? "Signing in..." : "Continue as Google user"}
        </Button>
      </form>
    </div>
  );
}

export default function GoogleMockPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-muted-foreground">Loading…</div>}>
      <GoogleMockInner />
    </Suspense>
  );
}
