"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import type { Country } from "react-phone-number-input";
import { isValidPhoneNumber } from "react-phone-number-input";
import {
  CountrySelectField,
  PhoneField,
} from "@/components/forms/phone-country-fields";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { ApiError, getMe, updateMyProfile, type AuthUser } from "@/lib/api";
import { displayName, initialsFor } from "@/lib/user-display";

function formatJoined(iso: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "long",
      day: "numeric",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function ProfileContent() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [phone, setPhone] = useState("");
  const [phoneCountry, setPhoneCountry] = useState<Country | undefined>("NG");
  const [residence, setResidence] = useState("");
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [residenceError, setResidenceError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [discord, setDiscord] = useState("");
  const [telegram, setTelegram] = useState("");
  const [github, setGithub] = useState("");
  const [xUrl, setXUrl] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [portfolio, setPortfolio] = useState("");
  const [socialSaving, setSocialSaving] = useState(false);
  const [socialMessage, setSocialMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getMe()
      .then((me) => {
        if (cancelled) return;
        setUser(me);
        setPhone(me.phone_number || "");
        setPhoneCountry((me.phone_country_code as Country | null) || "NG");
        setResidence(me.country_of_residence || "");
        setDiscord(me.discord_username || "");
        setTelegram(me.telegram_username || "");
        setGithub(me.github_url || "");
        setXUrl(me.x_url || "");
        setLinkedin(me.linkedin_url || "");
        setPortfolio(me.portfolio_url || "");
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load profile");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function saveContact() {
    if (!user) return;
    setSaveError(null);
    setSaveSuccess(null);
    setPhoneError(null);
    setResidenceError(null);

    if (!phone || !isValidPhoneNumber(phone)) {
      setPhoneError("Enter a valid phone number");
      return;
    }
    if (!phoneCountry) {
      setPhoneError("Select a phone country");
      return;
    }
    if (!residence) {
      setResidenceError("Select your country of residence");
      return;
    }

    setSaving(true);
    try {
      const updated = await updateMyProfile({
        phone_number: phone,
        phone_country_code: phoneCountry,
        country_of_residence: residence,
      });
      setUser(updated);
      setPhone(updated.phone_number || "");
      setPhoneCountry((updated.phone_country_code as Country | null) || "NG");
      setResidence(updated.country_of_residence || "");
      setSaveSuccess("Contact details saved.");
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.detail : "Could not save profile");
    } finally {
      setSaving(false);
    }
  }

  async function saveSocial() {
    setSocialSaving(true);
    setSocialMessage(null);
    try {
      const updated = await updateMyProfile({
        discord_username: discord,
        telegram_username: telegram,
        github_url: github,
        x_url: xUrl,
        linkedin_url: linkedin,
        portfolio_url: portfolio,
      });
      setUser(updated);
      setSocialMessage("Community links saved.");
    } catch (err) {
      setSocialMessage(err instanceof ApiError ? err.detail : "Could not save links");
    } finally {
      setSocialSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading profile…
      </div>
    );
  }

  if (error || !user) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn’t load profile"
        description={error || "Sign in again to view your account."}
        action={{ label: "Sign in", href: "/login?next=/profile" }}
      />
    );
  }

  const name = displayName(user.full_name, user.email);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        title="Profile"
        description="Account details for the user you are signed in as. You can update phone and country of residence below."
      />
      <Card className="shadow-card">
        <CardHeader className="flex flex-row items-center gap-4">
          <Avatar className="size-16">
            <AvatarFallback className="bg-brand-navy text-lg text-white">
              {initialsFor(user.full_name, user.email)}
            </AvatarFallback>
          </Avatar>
          <div>
            <CardTitle>{name}</CardTitle>
            <p className="text-sm text-muted-foreground">{user.email}</p>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Separator />
          <dl className="grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Name
              </dt>
              <dd className="mt-1 font-medium">{user.full_name || "-"}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Role
              </dt>
              <dd className="mt-1">
                <Badge variant="outline" className="capitalize">
                  {user.role}
                </Badge>
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Email
              </dt>
              <dd className="mt-1 font-medium">{user.email}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Email verified
              </dt>
              <dd className="mt-1">{user.email_verified ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Member since
              </dt>
              <dd className="mt-1">{formatJoined(user.created_at)}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle className="text-lg">Contact details</CardTitle>
          <p className="text-sm text-muted-foreground">
            Phone country and country of residence are stored separately.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <PhoneField
            value={phone}
            country={phoneCountry}
            onChange={(nextPhone, nextCountry) => {
              setPhone(nextPhone);
              setPhoneCountry(nextCountry);
              setPhoneError(null);
            }}
            error={phoneError || undefined}
          />
          <CountrySelectField
            value={residence}
            onChange={(next) => {
              setResidence(next);
              setResidenceError(null);
            }}
            error={residenceError || undefined}
          />
          {saveError ? <p className="text-sm text-destructive">{saveError}</p> : null}
          {saveSuccess ? <p className="text-sm text-success">{saveSuccess}</p> : null}
          <Button
            type="button"
            disabled={saving}
            onClick={saveContact}
            className="bg-brand-navy text-white hover:bg-brand-navy/90"
          >
            {saving ? "Saving…" : "Save contact details"}
          </Button>
        </CardContent>
      </Card>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle className="text-lg">Community & professional links</CardTitle>
          <p className="text-sm text-muted-foreground">
            Kept private. Visible only to you and authorized staff.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="discord">Discord username</Label>
              <Input id="discord" value={discord} onChange={(e) => setDiscord(e.target.value)} placeholder="name#0000" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="telegram">Telegram username</Label>
              <Input id="telegram" value={telegram} onChange={(e) => setTelegram(e.target.value)} placeholder="@username" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="github">GitHub URL</Label>
              <Input id="github" value={github} onChange={(e) => setGithub(e.target.value)} placeholder="https://github.com/you" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="xurl">X (Twitter) URL</Label>
              <Input id="xurl" value={xUrl} onChange={(e) => setXUrl(e.target.value)} placeholder="https://x.com/you" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="linkedin">LinkedIn URL</Label>
              <Input id="linkedin" value={linkedin} onChange={(e) => setLinkedin(e.target.value)} placeholder="https://linkedin.com/in/you" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="portfolio">Portfolio URL</Label>
              <Input id="portfolio" value={portfolio} onChange={(e) => setPortfolio(e.target.value)} placeholder="https://you.com" />
            </div>
          </div>
          {socialMessage ? <p className="text-sm text-muted-foreground">{socialMessage}</p> : null}
          <Button type="button" disabled={socialSaving} onClick={saveSocial} variant="outline">
            {socialSaving ? "Saving…" : "Save links"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
