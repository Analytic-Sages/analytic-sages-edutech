import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthForm } from "@/components/auth/auth-form";

export const metadata: Metadata = {
  title: "Sign In",
  robots: {
    index: false,
    follow: false,
  },
};

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-muted-foreground">Loading…</div>}>
      <AuthForm mode="login" />
    </Suspense>
  );
}
