"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { siteConfig } from "@/config/site";
import {
  ApiError,
  apiFetch,
  getAccessToken,
  getApiBaseUrl,
  getAuthProviders,
  getMe,
  setAccessToken,
  syncAuthSession,
  type AuthProviders,
  type AuthUser,
} from "@/lib/api";
import { getLastAuthMethod, setLastAuthMethod, type AuthMethod } from "@/lib/auth-method";
import { resolvePostLoginPath } from "@/lib/auth-redirect";
import { cn } from "@/lib/utils";

const authSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  full_name: z.string().max(255).optional(),
});

type AuthFormData = z.infer<typeof authSchema>;

type AuthFormProps = {
  mode: "login" | "register";
};

type AuthResponse = {
  access_token: string;
  user: AuthUser;
};

function RecentlyUsedBadge() {
  return (
    <span className="absolute -top-2 right-3 rounded-full bg-brand-orange px-2 py-0.5 text-[10px] font-semibold tracking-wide text-white uppercase shadow-sm">
      Recently used
    </span>
  );
}

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawNext = searchParams.get("next") || "/dashboard";
  const nextPath =
    rawNext.startsWith("/") && !rawNext.startsWith("//") ? rawNext : "/dashboard";
  const oauthError = searchParams.get("error");

  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [lastMethod, setLastMethod] = useState<AuthMethod | null>(() =>
    typeof window !== "undefined" ? getLastAuthMethod() : null
  );
  const [providers, setProviders] = useState<AuthProviders | null>(null);
  const [googleLoading, setGoogleLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AuthFormData>({
    resolver: zodResolver(authSchema),
  });

  useEffect(() => {
    getAuthProviders()
      .then(setProviders)
      .catch(() => {
        setProviders({
          google: { enabled: true, mode: "mock", start_url: "/api/v1/auth/google" },
          email_password: true,
        });
      });
  }, []);

  // Restore session cookie for users who already have a token in localStorage.
  useEffect(() => {
    if (mode !== "login") return;
    if (!getAccessToken()) return;
    syncAuthSession();
    getMe()
      .then((me) => router.replace(resolvePostLoginPath(me.role, nextPath)))
      .catch(() => router.replace(nextPath));
  }, [mode, nextPath, router]);

  useEffect(() => {
    if (oauthError) {
      queueMicrotask(() => setFormError(`Google sign-in failed: ${oauthError}`));
    }
  }, [oauthError]);

  const onSubmit = async (data: AuthFormData) => {
    setFormError(null);
    setFormSuccess(null);
    try {
      if (mode === "register") {
        await apiFetch<{ message: string }>("/api/v1/auth/register", {
          method: "POST",
          auth: false,
          body: JSON.stringify({
            email: data.email,
            password: data.password,
            full_name: data.full_name || null,
          }),
        });
        setLastAuthMethod("email");
        setLastMethod("email");
        const q = new URLSearchParams({ email: data.email });
        if (nextPath && nextPath !== "/dashboard") {
          q.set("next", nextPath);
        }
        router.push(`/verify-email?${q.toString()}`);
        return;
      }

      const result = await apiFetch<AuthResponse>("/api/v1/auth/login", {
        method: "POST",
        auth: false,
        body: JSON.stringify({
          email: data.email,
          password: data.password,
        }),
      });
      setAccessToken(result.access_token);
      setLastAuthMethod("email");
      router.push(resolvePostLoginPath(result.user.role, nextPath));
    } catch (err) {
      setFormError(err instanceof ApiError ? err.detail : "Authentication failed");
    }
  };

  function handleGoogleLogin() {
    setFormError(null);
    setGoogleLoading(true);

    if (providers?.google.mode === "disabled") {
      setFormError("Google login is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.");
      setGoogleLoading(false);
      return;
    }

    const startUrl = `${getApiBaseUrl()}/api/v1/auth/google?next=${encodeURIComponent(nextPath)}`;
    window.location.assign(startUrl);
  }

  const googleEnabled = providers?.google.enabled !== false;

  return (
    <div className="mx-auto w-full max-w-sm space-y-8">
      <div className="flex flex-col items-center space-y-2 text-center">
        <Logo size="md" href="/" />
        <h1 className="font-heading text-2xl font-bold">
          {mode === "login" ? "Welcome back" : "Create your account"}
        </h1>
        <p className="text-sm text-muted-foreground">
          {mode === "login"
            ? "Sign in to continue your learning journey"
            : `Join ${siteConfig.name} and start building`}
        </p>
      </div>

      <div className="relative">
        {lastMethod === "google" && <RecentlyUsedBadge />}
        <Button
          variant="outline"
          className={cn(
            "h-11 w-full gap-2",
            lastMethod === "google" && "border-brand-orange ring-1 ring-brand-orange/40"
          )}
          type="button"
          disabled={!googleEnabled || googleLoading}
          onClick={handleGoogleLogin}
        >
          <svg className="size-4" viewBox="0 0 24 24" aria-hidden>
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          {googleLoading
            ? "Redirecting..."
            : providers?.google.mode === "mock"
              ? "Continue with Google (dev)"
              : "Continue with Google"}
        </Button>
      </div>

      <div className="relative">
        <Separator />
        <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-background px-2 text-xs text-muted-foreground">
          or continue with email
        </span>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="relative space-y-4">
        {lastMethod === "email" && <RecentlyUsedBadge />}
        <div
          className={cn(
            "space-y-4 rounded-xl p-1",
            lastMethod === "email" && "ring-1 ring-brand-orange/30"
          )}
        >
          {mode === "register" && (
            <div className="space-y-2">
              <Label htmlFor="full_name">Full name</Label>
              <Input id="full_name" placeholder="Ada Okonkwo" {...register("full_name")} />
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              {...register("email")}
              aria-invalid={!!errors.email}
            />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
              {mode === "login" && (
                <Link
                  href="/forgot-password"
                  className="text-xs text-brand-navy hover:underline dark:text-brand-orange"
                >
                  Forgot password?
                </Link>
              )}
            </div>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              {...register("password")}
              aria-invalid={!!errors.password}
            />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>
          {formError && <p className="text-sm text-destructive">{formError}</p>}
          {formSuccess && <p className="text-sm text-success">{formSuccess}</p>}
          <Button
            type="submit"
            disabled={isSubmitting}
            className="h-11 w-full bg-brand-navy text-white hover:bg-brand-navy/90"
          >
            {isSubmitting
              ? "Please wait..."
              : mode === "login"
                ? "Sign in with email"
                : "Create account"}
          </Button>
        </div>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        {mode === "login" ? (
          <>
            Don&apos;t have an account?{" "}
            <Link
              href={`/register${nextPath !== "/dashboard" ? `?next=${encodeURIComponent(nextPath)}` : ""}`}
              className="font-medium text-brand-navy hover:underline dark:text-brand-orange"
            >
              Sign up
            </Link>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-brand-navy hover:underline dark:text-brand-orange"
            >
              Sign in
            </Link>
          </>
        )}
      </p>
    </div>
  );
}
