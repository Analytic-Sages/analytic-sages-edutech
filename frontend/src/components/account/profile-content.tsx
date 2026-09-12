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
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getMe()
      .then((me) => {
        if (cancelled) return;
        setUser(me);
        setPhone(me.phone_number || "");
        setPhoneCountry((me.phone_country_code as Country | null) || "NG");
        setResidence(me.country_of_residence || "");
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

    if (phone && !isValidPhoneNumber(phone)) {
      setPhoneError("Enter a valid phone number");
      return;
    }

    setSaving(true);
    try {
      const clearPhone = !phone;
      const clearResidence = !residence;
      const updated = await updateMyProfile({
        phone_number: clearPhone ? null : phone,
        phone_country_code: clearPhone ? null : phoneCountry || null,
        country_of_residence: clearResidence ? null : residence,
        clear_phone: clearPhone,
        clear_country_of_residence: clearResidence,
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
            Optional phone and residence fields. Phone country and country of residence are stored
            separately.
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
          <CountrySelectField value={residence} onChange={setResidence} />
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
    </div>
  );
}
