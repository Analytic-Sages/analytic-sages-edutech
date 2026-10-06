"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { CheckCircle2, Loader2, Radio } from "lucide-react";
import type { Country } from "react-phone-number-input";
import { isValidPhoneNumber } from "react-phone-number-input";
import { CountrySelectField, PhoneField } from "@/components/forms/phone-country-fields";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getEngineeringProgramPage } from "@/lib/blockchain-data-engineering-program";
import { getProgramPage } from "@/lib/program-pages";
import {
  ApiError,
  getAccessToken,
  getMe,
  getMyWaitlistStatus,
  joinWaitlist,
  listPublicCohorts,
  updateMyProfile,
  type AuthUser,
  type PublicCohortCard,
  type WaitlistStatus,
} from "@/lib/api";

function resolveCohortSlug(slug: string): string {
  const engineering = getEngineeringProgramPage(slug);
  if (engineering) return engineering.cohortSlug;
  const page = getProgramPage(slug);
  if (page) return page.cohortSlug;
  return slug;
}

function displayName(user: AuthUser | null): string {
  return user?.full_name?.trim() || user?.email || "there";
}

type FieldDraft = {
  phone: string;
  phoneCountry: Country | undefined;
  discord: string;
  telegram: string;
  residence: string;
};

export function WaitlistContent({ slug }: { slug: string }) {
  const [cohort, setCohort] = useState<PublicCohortCard | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<WaitlistStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [draft, setDraft] = useState<FieldDraft>({
    phone: "",
    phoneCountry: "NG",
    discord: "",
    telegram: "",
    residence: "",
  });
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [joined, setJoined] = useState(false);

  const signedIn = Boolean(getAccessToken());
  const cohortSlug = useMemo(() => resolveCohortSlug(slug), [slug]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const cohorts = await listPublicCohorts().catch(() => [] as PublicCohortCard[]);
        const match = cohorts.find((item) => item.slug === cohortSlug) ?? null;
        if (!cancelled) setCohort(match);

        if (getAccessToken()) {
          const me = await getMe();
          if (cancelled) return;
          setUser(me);
          setDraft((prev) => ({
            ...prev,
            phone: me.phone_number || "",
            phoneCountry: (me.phone_country_code as Country | null) || "NG",
            discord: me.discord_username || "",
            telegram: me.telegram_username || "",
            residence: me.country_of_residence || "",
          }));
          if (match) {
            const current = await getMyWaitlistStatus(match.id).catch(() => null);
            if (!cancelled && current) {
              setStatus(current);
              setJoined(current.is_on_waitlist);
            }
          }
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load waitlist");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [cohortSlug]);

  async function saveMissingFieldsAndJoin() {
    if (!cohort) return;
    setSubmitting(true);
    setFieldError(null);
    setError(null);
    try {
      const missing = status?.missing_fields ?? [];
      const payload: Parameters<typeof updateMyProfile>[0] = {};
      if (missing.includes("phone_number")) {
        if (!draft.phone || !isValidPhoneNumber(draft.phone)) {
          setFieldError("Enter a valid phone / WhatsApp number.");
          return;
        }
        payload.phone_number = draft.phone;
        payload.phone_country_code = draft.phoneCountry || "NG";
      }
      if (missing.includes("discord_username")) {
        if (!draft.discord.trim()) {
          setFieldError("Discord username is required.");
          return;
        }
        payload.discord_username = draft.discord.trim();
      }
      if (missing.includes("telegram_username")) {
        if (!draft.telegram.trim()) {
          setFieldError("Telegram username is required.");
          return;
        }
        payload.telegram_username = draft.telegram.trim();
      }
      if (draft.residence) payload.country_of_residence = draft.residence;
      if (Object.keys(payload).length > 0) {
        const updated = await updateMyProfile(payload);
        setUser(updated);
      }
      await joinWaitlist(cohort.id);
      setJoined(true);
      setStatus((prev) => (prev ? { ...prev, is_on_waitlist: true, missing_fields: [] } : prev));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Could not join the waitlist. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function joinWithProfile() {
    if (!cohort) return;
    setSubmitting(true);
    setError(null);
    try {
      await joinWaitlist(cohort.id);
      setJoined(true);
      setStatus((prev) => (prev ? { ...prev, is_on_waitlist: true, missing_fields: [] } : prev));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Could not join the waitlist. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading waitlist…
      </div>
    );
  }

  const missing = status?.missing_fields ?? [];
  const missingLabels = missing.map((field) => {
    if (field === "phone_number") return "phone / WhatsApp number";
    if (field === "discord_username") return "Discord username";
    if (field === "telegram_username") return "Telegram username";
    return field;
  });
  const isOpen = cohort?.waitlist_open ?? status?.is_open ?? true;

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
      <PageHeader
        title="Join the Blockchain Data Engineering waitlist"
        description="Be first to know when the next cohort opens."
      />

      {!isOpen && (
        <p className="mb-6 rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
          This programme is not currently running a waitlist. Please check the programme page for the
          latest registration details.
        </p>
      )}

      {error && (
        <p className="mb-6 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      {!signedIn ? (
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle className="text-lg">Sign in to join</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              The waitlist uses your existing profile, so please sign in (or create an account) to
              join. It only takes a minute.
            </p>
            <div className="flex flex-wrap gap-3">
              <ButtonLink
                href={`/login?next=/waitlist/${slug}`}
                className="bg-brand-orange text-white hover:bg-brand-orange/90"
              >
                Log in
              </ButtonLink>
              <ButtonLink href={`/register?next=/waitlist/${slug}`} variant="outline">
                Create account
              </ButtonLink>
            </div>
          </CardContent>
        </Card>
      ) : joined ? (
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <CheckCircle2 className="size-5 text-success" />
              You are on the waitlist
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Thanks, {displayName(user)}. We have your details and will email you as soon as the
              next cohort opens.
            </p>
            <div className="flex flex-wrap gap-3">
              <ButtonLink href={`/programs/${slug}`} variant="outline">
                Back to the programme
              </ButtonLink>
              <ButtonLink href="/dashboard" variant="outline">
                Go to dashboard
              </ButtonLink>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="shadow-card">
          <CardHeader>
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-lg">Join with your profile</CardTitle>
              {missing.length > 0 && <Badge variant="outline">Profile incomplete</Badge>}
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <p className="text-sm text-muted-foreground">
              {missing.length === 0
                ? "Your profile is complete. Confirm below and we will add you to the waitlist."
                : `We just need your ${missingLabels.join(", ")} to add you to the waitlist.`}
            </p>

            {missing.length > 0 && (
              <div className="space-y-4">
                {missing.includes("phone_number") && (
                  <PhoneField
                    value={draft.phone}
                    country={draft.phoneCountry}
                    onChange={(phone, country) =>
                      setDraft((prev) => ({ ...prev, phone, phoneCountry: country }))
                    }
                  />
                )}
                {missing.includes("discord_username") && (
                  <div className="space-y-2">
                    <Label htmlFor="waitlist-discord">Discord username</Label>
                    <Input
                      id="waitlist-discord"
                      value={draft.discord}
                      onChange={(e) => setDraft((prev) => ({ ...prev, discord: e.target.value }))}
                      placeholder="name#0000"
                    />
                  </div>
                )}
                {missing.includes("telegram_username") && (
                  <div className="space-y-2">
                    <Label htmlFor="waitlist-telegram">Telegram username</Label>
                    <Input
                      id="waitlist-telegram"
                      value={draft.telegram}
                      onChange={(e) => setDraft((prev) => ({ ...prev, telegram: e.target.value }))}
                      placeholder="@username"
                    />
                  </div>
                )}
                {!draft.residence && (
                  <CountrySelectField
                    value={draft.residence}
                    onChange={(iso2) => setDraft((prev) => ({ ...prev, residence: iso2 }))}
                    hint="Optional, helps us tailor sessions to your time zone."
                  />
                )}
                {fieldError && <p className="text-sm text-destructive">{fieldError}</p>}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3">
              {missing.length > 0 ? (
                <Button
                  onClick={saveMissingFieldsAndJoin}
                  disabled={submitting}
                  className="bg-brand-orange text-white hover:bg-brand-orange/90"
                >
                  {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
                  Save &amp; join waitlist
                </Button>
              ) : (
                <Button
                  onClick={joinWithProfile}
                  disabled={submitting}
                  className="bg-brand-orange text-white hover:bg-brand-orange/90"
                >
                  {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
                  Join waitlist
                </Button>
              )}
              <Link
                href="/profile"
                className="inline-flex items-center text-sm font-medium text-brand-orange hover:underline"
              >
                Review full profile
              </Link>
            </div>
          </CardContent>
        </Card>
      )}

      {!cohort && (
        <div className="mt-8">
          <EmptyState
            icon={<Radio className="size-5" />}
            title="Programme not found"
            description="We could not find this programme. Please check the programme page."
            action={{ label: "View programmes", href: "/programs" }}
          />
        </div>
      )}
    </div>
  );
}