import { Mail } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { ButtonLink } from "@/components/ui/button-link";

export const metadata = { title: "Verify Email" };

export default function VerifyEmailPage() {
  return (
    <div className="mx-auto w-full max-w-sm space-y-8 text-center">
      <Logo size="md" href="/" className="mx-auto" />
      <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-brand-navy/10">
        <Mail className="size-8 text-brand-navy" />
      </div>
      <div>
        <h1 className="font-heading text-2xl font-bold">Check your email</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          We sent a verification link to your email address. Click the link to
          activate your account.
        </p>
      </div>
      <ButtonLink href="/login" variant="outline">
        Back to sign in
      </ButtonLink>
    </div>
  );
}
