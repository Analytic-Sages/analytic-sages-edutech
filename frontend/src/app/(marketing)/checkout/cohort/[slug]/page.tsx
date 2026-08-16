"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Bitcoin, CreditCard, Landmark, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  createCohortCheckout,
  getAccessToken,
  listPublicCohorts,
  type PaymentProvider,
  type PublicCohortCard,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

const providers: {
  id: PaymentProvider;
  name: string;
  description: string;
  icon: typeof CreditCard;
  recommended?: boolean;
}[] = [
  {
    id: "paystack",
    name: "Paystack",
    description: "Cards and bank transfer",
    icon: Landmark,
  },
  {
    id: "nowpayments",
    name: "Crypto (NOWPayments)",
    description: "BTC, ETH, USDT, and more",
    icon: Bitcoin,
  },
  {
    id: "stripe",
    name: "Stripe",
    description: "International cards",
    icon: CreditCard,
  },
];

function formatDate(iso: string | null) {
  if (!iso) return null;
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "long",
      day: "numeric",
      year: "numeric",
      timeZone: "UTC",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export default function CohortCheckoutPage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const slug = params.slug;

  const [cohort, setCohort] = useState<PublicCohortCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingProvider, setLoadingProvider] = useState<PaymentProvider | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listPublicCohorts()
      .then((cohorts) => {
        if (!cancelled) {
          setCohort(cohorts.find((c) => c.slug === slug) ?? null);
        }
      })
      .catch(() => {
        if (!cancelled) setCohort(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  async function handleCheckout(provider: PaymentProvider) {
    setError(null);
    if (!getAccessToken()) {
      router.push(`/login?next=/checkout/cohort/${slug}`);
      return;
    }
    if (!cohort) {
      setError("Cohort not found or not open for registration.");
      return;
    }
    if (cohort.price <= 0) {
      setError("This cohort is not open for online payment yet.");
      return;
    }

    setLoadingProvider(provider);
    try {
      const session = await createCohortCheckout(cohort.id, provider);
      window.location.assign(session.checkout_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checkout failed");
      setLoadingProvider(null);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto flex max-w-lg items-center justify-center gap-2 px-4 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading cohort…
      </div>
    );
  }

  if (!cohort) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center sm:px-6">
        <PageHeader
          title="Cohort not available"
          description="This instructor-led cohort isn’t open for registration right now."
        />
        <ButtonLink href="/instructor-led" variant="outline" className="mt-6">
          Back to Instructor-Led
        </ButtonLink>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-12 sm:px-6">
      <PageHeader
        title="Register for cohort"
        description="Complete payment to join the live classroom for this instructor-led program."
      />
      <Card className="mt-8 shadow-card">
        <CardHeader>
          <CardTitle className="font-heading text-xl">{cohort.name}</CardTitle>
          {cohort.description && (
            <p className="text-sm text-muted-foreground">{cohort.description}</p>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="font-heading text-3xl font-bold text-brand-navy dark:text-foreground">
            {formatPrice(cohort.price, cohort.currency)}
          </p>
          <div className="space-y-1 text-sm text-muted-foreground">
            {formatDate(cohort.registration_deadline) && (
              <p>Registration deadline: {formatDate(cohort.registration_deadline)}</p>
            )}
            {formatDate(cohort.starts_at) && (
              <p>Start date: {formatDate(cohort.starts_at)}</p>
            )}
          </div>

          {error && (
            <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          <div className="space-y-3 pt-2">
            {providers.map((provider) => {
              const Icon = provider.icon;
              const busy = loadingProvider === provider.id;
              return (
                <button
                  key={provider.id}
                  type="button"
                  disabled={Boolean(loadingProvider)}
                  onClick={() => handleCheckout(provider.id)}
                  className="flex w-full items-center gap-3 rounded-lg border bg-background px-4 py-3 text-left transition hover:border-brand-orange/50 hover:bg-muted/40 disabled:opacity-60"
                >
                  <Icon className="size-5 shrink-0 text-brand-orange" />
                  <span className="flex-1">
                    <span className="block font-medium">
                      {provider.name}
                      {provider.recommended ? " · Recommended" : ""}
                    </span>
                    <span className="block text-xs text-muted-foreground">
                      {provider.description}
                    </span>
                  </span>
                  {busy ? <Loader2 className="size-4 animate-spin" /> : null}
                </button>
              );
            })}
          </div>

          <p className="pt-2 text-xs text-muted-foreground">
            Enrollment unlocks after payment confirmation (webhook), not from the redirect alone.
            After confirmation, open Classroom to join live sessions.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
