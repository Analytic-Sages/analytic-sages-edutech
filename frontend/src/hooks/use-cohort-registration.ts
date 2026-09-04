"use client";

import { useEffect, useState } from "react";
import {
  listBillingPlans,
  listPublicCohorts,
  type PublicCohortCard,
  type TuitionPlanPublic,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

export type CohortRegistrationOptions = {
  /** Short marketing tuition line (details live on checkout). */
  tuitionSummary?: string;
  /**
   * Treat Join CTAs as live for this programme even when the public API has not
   * returned the cohort yet. Checkout still validates availability.
   */
  registrationLive?: boolean;
};

export type CohortRegistrationState = {
  cohort: PublicCohortCard | null;
  plans: TuitionPlanPublic[];
  loading: boolean;
  /** API reports open/active */
  apiOpen: boolean;
  /** Marketing CTAs should offer checkout */
  open: boolean;
  checkoutHref: string;
  /** Live cohort price when available; otherwise marketing fallback */
  priceLabel: string;
  /** Short marketing line only — not plan schedule details */
  tuitionSummary: string | null;
};

const FALLBACK_PRICE = "$200";

/** Loads public cohort (+ plans) for register CTAs and date/price enrichment. */
export function useCohortRegistration(
  cohortSlug: string,
  options: CohortRegistrationOptions = {},
): CohortRegistrationState {
  const { tuitionSummary: marketingTuition, registrationLive = false } = options;
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

  const apiOpen = cohort?.status === "open" || cohort?.status === "active";
  const open = registrationLive || apiOpen;
  const priceLabel =
    cohort && cohort.price > 0 ? formatPrice(cohort.price, cohort.currency) : FALLBACK_PRICE;

  return {
    cohort,
    plans,
    loading,
    apiOpen,
    open,
    checkoutHref: `/checkout/cohort/${cohortSlug}`,
    priceLabel,
    tuitionSummary: open ? marketingTuition ?? null : null,
  };
}
