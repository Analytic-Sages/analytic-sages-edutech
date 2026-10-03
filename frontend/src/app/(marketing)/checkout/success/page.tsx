"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button-link";
import { getAccessToken, getPayment, type PaymentPublic } from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

const TERMINAL_STATUSES = new Set(["confirmed", "failed", "expired", "refunded"]);
const POLL_INTERVAL_MS = 4000;
const MAX_POLL_ATTEMPTS = 150; // ~10 minutes
const AUTO_REDIRECT_DELAY_MS = 2500;

type StatusCopy = {
  title: string;
  description: string;
};

function statusCopy(payment: PaymentPublic | null): StatusCopy {
  const isCohort = Boolean(payment?.cohort_id);
  const destination = isCohort ? "your cohort classroom" : "your course";
  switch (payment?.status) {
    case "confirmed":
      return {
        title: "Payment confirmed",
        description: `Your payment is confirmed and ${destination} is unlocked. Taking you there now…`,
      };
    case "confirming":
      return {
        title: "Payment detected",
        description:
          "We've received your payment and are waiting for network confirmations. This can take a few minutes — keep this tab open.",
      };
    case "failed":
      return {
        title: "Payment didn't complete",
        description:
          "NOWPayments reported this payment as failed. You haven't been charged successfully — try checkout again or pick a different payment method.",
      };
    case "expired":
      return {
        title: "Payment window expired",
        description:
          "The payment invoice expired before funds arrived. Start checkout again to generate a fresh invoice.",
      };
    case "refunded":
      return {
        title: "Payment refunded",
        description: "This payment was refunded. If you still want access, start checkout again.",
      };
    default:
      return {
        title: "Waiting to detect your payment",
        description:
          "Complete the transfer in NOWPayments if you haven't yet. We'll confirm it automatically — keep this tab open.",
      };
  }
}

function SuccessInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const orderId = searchParams.get("order_id");
  const [payment, setPayment] = useState<PaymentPublic | null>(null);
  // True once polling has finished (terminal status reached, timed out, or
  // no pollable order — e.g. missing order_id or signed-out visitor).
  const [settled, setSettled] = useState(false);
  const canPoll = Boolean(orderId && typeof window !== "undefined" && getAccessToken());
  const loading = canPoll && !settled;

  useEffect(() => {
    if (!orderId || !getAccessToken()) {
      return;
    }
    let stopped = false;
    let attempts = 0;
    let timer: ReturnType<typeof setTimeout>;

    async function tick() {
      try {
        const current = await getPayment(orderId!);
        if (stopped) return;
        setPayment(current);
        if (TERMINAL_STATUSES.has(current.status)) {
          setSettled(true);
          if (current.status === "confirmed") {
            timer = setTimeout(() => {
              if (!stopped) {
                router.push(current.cohort_id ? "/classroom" : "/my-courses");
              }
            }, AUTO_REDIRECT_DELAY_MS);
          }
          return;
        }
      } catch {
        if (!stopped) setPayment(null);
      }
      if (!stopped && ++attempts < MAX_POLL_ATTEMPTS) {
        timer = setTimeout(tick, POLL_INTERVAL_MS);
      } else {
        setSettled(true);
      }
    }

    tick();
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [orderId, router]);

  const copy = statusCopy(payment);
  const confirmed = payment?.status === "confirmed";
  const failed = payment ? ["failed", "expired", "refunded"].includes(payment.status) : false;

  return (
    <div className="mx-auto max-w-lg px-4 py-16 text-center sm:px-6">
      <div className="mx-auto mb-6 flex size-16 items-center justify-center rounded-full bg-success/10">
        {loading ? (
          <Loader2 className="size-8 animate-spin text-brand-navy" />
        ) : confirmed ? (
          <CheckCircle2 className="size-8 text-success" />
        ) : failed ? (
          <XCircle className="size-8 text-destructive" />
        ) : (
          <Loader2 className="size-8 animate-spin text-brand-navy" />
        )}
      </div>
      <PageHeader
        title={copy.title}
        description={copy.description}
        className="items-center text-center [&_h1]:mx-auto [&_p]:mx-auto"
      />
      {payment && (
        <p className="mb-8 text-sm text-muted-foreground">
          Order {payment.order_id} · {formatPrice(payment.amount, payment.currency)} ·{" "}
          <span className="capitalize">{payment.status}</span>
        </p>
      )}
      <div className="flex flex-col justify-center gap-3 sm:flex-row">
        {confirmed ? (
          <ButtonLink
            href={payment?.cohort_id ? "/classroom" : "/my-courses"}
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            {payment?.cohort_id ? "Open Classroom" : "Go to my courses"}
          </ButtonLink>
        ) : failed ? (
          <ButtonLink
            href="/instructor-led"
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            Back to checkout
          </ButtonLink>
        ) : (
          <ButtonLink href="/dashboard" variant="outline">
            Open dashboard
          </ButtonLink>
        )}
      </div>
    </div>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center">Loading…</div>}>
      <SuccessInner />
    </Suspense>
  );
}
