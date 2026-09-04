"use client";

import Image from "next/image";
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

  function scrollToApply() {
    if (profile?.status === "active") return;
    setShowApply(true);
    requestAnimationFrame(() => {
      document.getElementById("partner-apply")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  return (
    <div>
      <section className="relative overflow-hidden border-b border-[#0B1F3A]/10 bg-gradient-to-br from-white via-[#F7F9FC] to-[#EEF3F9]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(241,90,36,0.08),transparent_45%),radial-gradient(ellipse_at_bottom_right,rgba(11,31,58,0.06),transparent_50%)]" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] lg:gap-12 lg:py-20">
          <div className="max-w-xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-orange">
              Referral Partner Programme
            </p>
            <h1 className="mt-3 font-[family-name:var(--font-display)] text-4xl font-semibold tracking-tight text-[#0B1F3A] sm:text-5xl">
              Connect People to Opportunities That Matter.
            </h1>
            <p className="mt-4 text-lg text-[#0B1F3A]/80">
              Earn while helping others build the skills of the future.
            </p>
            <p className="mt-5 text-base leading-relaxed text-muted-foreground">
              Join the Analytic Sages Referral Partner Programme and share specialised programmes
              with your network. When someone you refer makes an eligible successful payment, you
              earn a 7% commission.
            </p>
            <p className="mt-4 text-base font-medium text-[#0B1F3A]">
              Share opportunity. Create impact. Earn together.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              {profile?.status === "active" ? (
                <Link
                  href="/partner"
                  className={cn(
                    buttonVariants(),
                    "bg-brand-orange text-white hover:bg-brand-orange/90"
                  )}
                >
                  Open partner dashboard →
                </Link>
              ) : !session ? (
                <>
                  <Link
                    href="/login?next=/partners"
                    className={cn(
                      buttonVariants(),
                      "bg-brand-orange text-white hover:bg-brand-orange/90"
                    )}
                  >
                    Become a Referral Partner →
                  </Link>
                  <Link
                    href="/register?next=/partners"
                    className={cn(buttonVariants({ variant: "outline" }))}
                  >
                    Create account
                  </Link>
                </>
              ) : (
                <Button
                  onClick={scrollToApply}
                  className="bg-brand-orange text-white hover:bg-brand-orange/90"
                >
                  Become a Referral Partner →
                </Button>
              )}
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-xl lg:max-w-none">
            <Image
              src="/partners/referral-partner-hero.jpg"
              alt="Diverse professionals connected around a global learning network"
              width={1200}
              height={750}
              priority
              className="h-auto w-full object-contain"
            />
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
        <div className="space-y-6 text-sm leading-relaxed text-muted-foreground">
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
              A $300 programme paid in three $100 installments earns $7 on each successful
              installment — $21 total if all three are paid. The same 7% applies in NGN, USDT, or
              other payment currencies; commissions stay in the currency of each payment.
            </p>
          </section>
          <p>
            <Link
              href="/partners/leaderboard"
              className="text-brand-orange underline-offset-4 hover:underline"
            >
              View partner leaderboard
            </Link>
          </p>
        </div>

        <div id="partner-apply" className="mt-12 scroll-mt-24 border-t pt-8">
          {profile ? (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Your application status:{" "}
                <span className="font-medium capitalize text-foreground">{profile.status}</span>
              </p>
              {profile.status === "active" ? (
                <Link
                  href="/partner"
                  className={cn(
                    buttonVariants(),
                    "bg-brand-orange text-white hover:bg-brand-orange/90"
                  )}
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
                className={cn(
                  buttonVariants(),
                  "bg-brand-orange text-white hover:bg-brand-orange/90"
                )}
              >
                Sign in to apply
              </Link>
              <Link
                href="/register?next=/partners"
                className={cn(buttonVariants({ variant: "outline" }))}
              >
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
                Become a Referral Partner →
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
