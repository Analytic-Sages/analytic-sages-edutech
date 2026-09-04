"use client";

import { useEffect, useState } from "react";
import {
  listBillingPlans,
  listPublicCohorts,
  type PublicCohortCard,
  type TuitionPlanPublic,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

export type CohortRegistrationState = {
  cohort: PublicCohortCard | null;
  plans: TuitionPlanPublic[];
  loading: boolean;
  open: boolean;
  checkoutHref: string;
  /** Live cohort price when available; otherwise marketing fallback */
  priceLabel: string;
  tuitionSummary: string | null;
};

const FALLBACK_PRICE = "$200";

function summarizePlans(plans: TuitionPlanPublic[]): string | null {
  if (plans.length === 0) return null;
  return plans
    .map((plan) => {
      const amount = formatPrice(Number(plan.base_amount), plan.base_currency);
      if (plan.number_of_installments > 1) {
        const first = plan.schedules.find((s) => s.sequence_number === 1);
        const due = first
          ? formatPrice(Number(first.amount), plan.base_currency)
          : null;
        return due ? `${plan.name} (${due} due today)` : `${plan.name} (${amount})`;
      }
      return `${plan.name} (${amount})`;
    })
    .join(" · ");
}

/** Loads public cohort + tuition plans for register CTAs. */
export function useCohortRegistration(
  cohortSlug: string,
  fallbackTuitionSummary?: string,
): CohortRegistrationState {
  const [cohort, setCohort] = useState<PublicCohortCard | null>(null);
  const [plans, setPlans] = useState<TuitionPlanPublic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    listPublicCohorts()
      .then(async (rows) => {
        const found = rows.find((row) => row.slug === cohortSlug) ?? null;
        if (cancelled) return;
        setCohort(found);
        if (!found) {
          setPlans([]);
          return;
        }
        try {
          const available = await listBillingPlans(found.id);
          if (!cancelled) setPlans(available);
        } catch {
          if (!cancelled) setPlans([]);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCohort(null);
          setPlans([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [cohortSlug]);

  const open = cohort?.status === "open" || cohort?.status === "active";
  const priceLabel =
    cohort && cohort.price > 0 ? formatPrice(cohort.price, cohort.currency) : FALLBACK_PRICE;
  const liveSummary = summarizePlans(plans);
  const tuitionSummary = liveSummary ?? (open ? fallbackTuitionSummary ?? null : null);

  return {
    cohort,
    plans,
    loading,
    open,
    checkoutHref: `/checkout/cohort/${cohortSlug}`,
    priceLabel,
    tuitionSummary,
  };
}
