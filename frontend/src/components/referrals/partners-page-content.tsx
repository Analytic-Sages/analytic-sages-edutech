"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ApiError,
  applyReferralPartner,
  ensureSession,
  getMyPartnerProfile,
  type PartnerPublic,
} from "@/lib/api";
import { cn } from "@/lib/utils";

export function PartnersPageContent() {
  const [session, setSession] = useState(false);
  const [profile, setProfile] = useState<PartnerPublic | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [social, setSocial] = useState("");
  const [channels, setChannels] = useState("");
  const [terms, setTerms] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showApply, setShowApply] = useState(false);

  useEffect(() => {
    ensureSession().then((ok) => {
      setSession(!!ok);
      if (ok) {
        getMyPartnerProfile()
          .then(setProfile)
          .catch(() => setProfile(null));
      }
    });
  }, []);

  async function onApply(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);
    try {
      const partner = await applyReferralPartner({
        display_name: displayName.trim(),
        social_handle: social.trim() || undefined,
        promotion_channels: channels.trim() || undefined,
        terms_accepted: terms,
      });
      setProfile(partner);
      setSuccess("Application submitted. An admin will review it shortly.");
      setShowApply(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not submit application");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <p className="text-sm font-medium uppercase tracking-wide text-brand-orange">
        Referral Partner Programme
      </p>
      <h1 className="mt-3 font-[family-name:var(--font-display)] text-4xl font-semibold tracking-tight text-[#0B1F3A]">
        Earn 7% when learners enroll through your link
      </h1>
      <p className="mt-4 text-lg text-muted-foreground">
        Analytic Sages Referral Partners share paid courses and programmes. You earn a 7%
        commission on each successful eligible payment — including installments — after a
        short holding period.
      </p>

      <div className="mt-10 space-y-6 text-sm leading-relaxed text-muted-foreground">
        <section>
          <h2 className="text-base font-semibold text-foreground">How it works</h2>
          <ol className="mt-2 list-decimal space-y-1 pl-5">
            <li>Apply and get approved by Analytic Sages.</li>
            <li>Share your unique referral link.</li>
            <li>New learners who join through your link are attributed for 30 days.</li>
            <li>When they pay for an eligible programme, you earn 7% of that payment.</li>
            <li>Commissions become available after 14 days, then you can request a payout.</li>
          </ol>
        </section>
        <section>
          <h2 className="text-base font-semibold text-foreground">Commission example</h2>
          <p className="mt-2">
            A ₦300,000 programme paid in three ₦100,000 installments earns ₦7,000 on each
            successful installment — ₦21,000 total if all three are paid.
          </p>
        </section>
        <p>
          <Link href="/partners/leaderboard" className="text-brand-orange underline-offset-4 hover:underline">
            View partner leaderboard
          </Link>
        </p>
      </div>

      <div className="mt-12 border-t pt-8">
        {profile ? (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Your application status:{" "}
              <span className="font-medium capitalize text-foreground">{profile.status}</span>
            </p>
            {profile.status === "active" ? (
              <Link
                href="/partner"
                className={cn(buttonVariants(), "bg-brand-orange text-white hover:bg-brand-orange/90")}
              >
                Open partner dashboard
              </Link>
            ) : (
              <p className="text-sm text-muted-foreground">
                We’ll email you when your application is reviewed.
              </p>
            )}
          </div>
        ) : !session ? (
          <div className="flex flex-wrap gap-3">
            <Link
              href="/login?next=/partners"
              className={cn(buttonVariants(), "bg-brand-orange text-white hover:bg-brand-orange/90")}
            >
              Sign in to apply
            </Link>
            <Link href="/register?next=/partners" className={cn(buttonVariants({ variant: "outline" }))}>
              Create account
            </Link>
          </div>
        ) : showApply ? (
          <form onSubmit={onApply} className="max-w-md space-y-4">
            <div className="space-y-2">
              <Label htmlFor="display_name">Display name</Label>
              <Input
                id="display_name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                minLength={2}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="social">Public / social handle (optional)</Label>
              <Input id="social" value={social} onChange={(e) => setSocial(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="channels">Promotion channels</Label>
              <Input
                id="channels"
                value={channels}
                onChange={(e) => setChannels(e.target.value)}
                placeholder="WhatsApp, X, community, etc."
              />
            </div>
            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                checked={terms}
                onChange={(e) => setTerms(e.target.checked)}
                className="mt-1"
                required
              />
              I agree to the Referral Partner programme terms and will promote Analytic Sages
              honestly.
            </label>
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            {success ? <p className="text-sm text-green-700">{success}</p> : null}
            <Button
              type="submit"
              disabled={submitting || !terms}
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
            >
              {submitting ? "Submitting…" : "Submit application"}
            </Button>
          </form>
        ) : (
          <div className="space-y-3">
            {success ? <p className="text-sm text-green-700">{success}</p> : null}
            <Button
              onClick={() => setShowApply(true)}
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
            >
              Become a Referral Partner
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
