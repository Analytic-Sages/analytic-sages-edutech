"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Bitcoin, Landmark, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  createCohortCheckout,
  getAccessToken,
  listBillingPlans,
  listPublicCohorts,
  type PaymentProvider,
  type PublicCohortCard,
  type TuitionPlanPublic,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

const providers: {
  id: PaymentProvider;
  name: string;
  description: string;
  icon: typeof Landmark;
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

function planDueLabel(plan: TuitionPlanPublic) {
  const second = plan.schedules.find((s) => s.sequence_number === 2);
  if (!second) return "One payment unlocks your seat.";
  const when = formatDate(second.due_date);
  return when
    ? `Pay the first installment now; second due ${when}.`
    : "Pay the first installment now; second due later in the program.";
}

export default function CohortCheckoutPage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const slug = params.slug;

  const [cohort, setCohort] = useState<PublicCohortCard | null>(null);
  const [plans, setPlans] = useState<TuitionPlanPublic[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingProvider, setLoadingProvider] = useState<PaymentProvider | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listPublicCohorts()
      .then(async (cohorts) => {
        const found = cohorts.find((c) => c.slug === slug) ?? null;
        if (cancelled) return;
        setCohort(found);
        if (!found) return;
        try {
          const available = await listBillingPlans(found.id);
          if (!cancelled) {
            setPlans(available);
            setSelectedPlanId(available[0]?.id ?? null);
          }
        } catch {
          if (!cancelled) {
            setPlans([]);
            setSelectedPlanId(null);
          }
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

  const selectedPlan = plans.find((p) => p.id === selectedPlanId) ?? null;
  const displayAmount = selectedPlan
    ? Number(selectedPlan.schedules.find((s) => s.sequence_number === 1)?.amount ?? selectedPlan.base_amount)
    : cohort?.price ?? 0;
  const displayCurrency = selectedPlan?.base_currency ?? cohort?.currency ?? "USD";

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
    if (plans.length > 0 && !selectedPlanId) {
      setError("Select a tuition plan to continue.");
      return;
    }
    if (plans.length === 0 && cohort.price <= 0) {
      setError("This cohort is not open for online payment yet.");
      return;
    }

    setLoadingProvider(provider);
    try {
      const session = await createCohortCheckout(
        cohort.id,
        provider,
        selectedPlanId ?? undefined,
      );
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
          description="This instructor-led cohort isn’t open for registration right now. Check Instructor-Led programmes for what’s live, or return to the programme page."
        />
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <ButtonLink href="/instructor-led" variant="outline">
            Back to Instructor-Led
          </ButtonLink>
          <ButtonLink href={`/programs/${slug}`} variant="ghost">
            Programme overview
          </ButtonLink>
        </div>
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
          {plans.length > 0 ? (
            <div className="space-y-3">
              <p className="text-sm font-medium text-brand-navy dark:text-foreground">
                Choose a tuition plan
              </p>
              {plans.map((plan) => {
                const first = plan.schedules.find((s) => s.sequence_number === 1);
                const selected = plan.id === selectedPlanId;
                return (
                  <button
                    key={plan.id}
                    type="button"
                    onClick={() => setSelectedPlanId(plan.id)}
                    className={cn(
                      "w-full rounded-lg border px-4 py-3 text-left transition",
                      selected
                        ? "border-brand-orange bg-brand-orange/5"
                        : "hover:border-brand-orange/40",
                    )}
                  >
                    <span className="flex items-baseline justify-between gap-3">
                      <span className="font-medium">{plan.name}</span>
                      <span className="font-heading text-lg font-bold text-brand-navy dark:text-foreground">
                        {formatPrice(Number(plan.base_amount), plan.base_currency)}
                      </span>
                    </span>
                    <span className="mt-1 block text-xs text-muted-foreground">
                      {plan.description || planDueLabel(plan)}
                    </span>
                    {first && plan.number_of_installments > 1 ? (
                      <span className="mt-1 block text-xs text-muted-foreground">
                        Due today:{" "}
                        {formatPrice(Number(first.amount), plan.base_currency)}
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="font-heading text-3xl font-bold text-brand-navy dark:text-foreground">
              {formatPrice(cohort.price, cohort.currency)}
            </p>
          )}

          {plans.length > 0 ? (
            <p className="font-heading text-2xl font-bold text-brand-navy dark:text-foreground">
              Pay now: {formatPrice(displayAmount, displayCurrency)}
            </p>
          ) : null}

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
                    <span className="block font-medium">{provider.name}</span>
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
            Your seat unlocks after the first confirmed payment. Later installments
            stay on your Billing page. We do not auto-revoke access for missed
            later payments in this release.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
