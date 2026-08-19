"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/auth/password-input";
import { ApiError, acceptStaffInvite, setAccessToken } from "@/lib/api";
import { resolvePostLoginPath } from "@/lib/auth-redirect";

const schema = z
  .object({
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm: z.string().min(8, "Confirm your password"),
  })
  .refine((data) => data.password === data.confirm, {
    message: "Passwords do not match",
    path: ["confirm"],
  });

type FormData = z.infer<typeof schema>;

function StaffInviteInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError(null);
    if (!token) {
      setError("Missing invite token. Open the link from your email again.");
      return;
    }
    try {
      const result = await acceptStaffInvite(token, data.password);
      setAccessToken(result.access_token);
      router.replace(resolvePostLoginPath(result.user.role, "/dashboard"));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not accept invite");
    }
  };

  return (
    <div className="mx-auto w-full max-w-sm space-y-8">
      <div className="flex flex-col items-center space-y-2 text-center">
        <Logo size="md" href="/" />
        <h1 className="font-heading text-2xl font-bold">Join Analytic Sages staff</h1>
        <p className="text-sm text-muted-foreground">
          Set a password to verify your email and open your staff workspace. This is invite-only.
        </p>
      </div>
      {!token ? (
        <p className="text-sm text-destructive">
          This invite link is missing a token. Ask an admin to send a new invite.
        </p>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <PasswordInput id="password" autoComplete="new-password" {...register("password")} />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm">Confirm password</Label>
            <PasswordInput id="confirm" autoComplete="new-password" {...register("confirm")} />
            {errors.confirm && (
              <p className="text-xs text-destructive">{errors.confirm.message}</p>
            )}
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button
            type="submit"
            disabled={isSubmitting}
            className="h-11 w-full bg-brand-navy text-white hover:bg-brand-navy/90"
          >
            {isSubmitting ? "Saving…" : "Set password and continue"}
          </Button>
        </form>
      )}
      <p className="text-center text-sm text-muted-foreground">
        Already set up?{" "}
        <Link href="/login" className="font-medium text-brand-navy hover:underline dark:text-brand-orange">
          Sign in
        </Link>
      </p>
    </div>
  );
}

export default function StaffInvitePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-muted-foreground">Loading…</div>}>
      <StaffInviteInner />
    </Suspense>
  );
}
