"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button-link";
import { getAccessToken, getPayment, type PaymentPublic } from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

function SuccessInner() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order_id");
  const [payment, setPayment] = useState<PaymentPublic | null>(null);
  const [loading, setLoading] = useState(() => Boolean(orderId && typeof window !== "undefined" && getAccessToken()));

  useEffect(() => {
    if (!orderId || !getAccessToken()) {
      return;
    }
    getPayment(orderId)
      .then(setPayment)
      .catch(() => setPayment(null))
      .finally(() => setLoading(false));
  }, [orderId]);

  return (
    <div className="mx-auto max-w-lg px-4 py-16 text-center sm:px-6">
      <div className="mx-auto mb-6 flex size-16 items-center justify-center rounded-full bg-success/10">
        {loading ? (
          <Loader2 className="size-8 animate-spin text-brand-navy" />
        ) : (
          <CheckCircle2 className="size-8 text-success" />
        )}
      </div>
      <PageHeader
        title="Payment received"
        description={
          payment?.cohort_id
            ? "Once payment is confirmed, your cohort seat is unlocked. Open Classroom when sessions go live."
            : "Once payment is confirmed, your course is unlocked. That can take a moment after you leave checkout."
        }
        className="items-center text-center [&_h1]:mx-auto [&_p]:mx-auto"
      />
      {payment && (
        <p className="mb-8 text-sm text-muted-foreground">
          Order {payment.order_id} · {formatPrice(payment.amount, payment.currency)} ·{" "}
          <span className="capitalize">{payment.status}</span>
        </p>
      )}
      <div className="flex flex-col justify-center gap-3 sm:flex-row">
        {payment?.cohort_id ? (
          <ButtonLink href="/classroom" className="bg-brand-orange text-white hover:bg-brand-orange/90">
            Open Classroom
          </ButtonLink>
        ) : (
          <ButtonLink href="/my-courses" className="bg-brand-orange text-white hover:bg-brand-orange/90">
            Go to my courses
          </ButtonLink>
        )}
        <ButtonLink href="/dashboard" variant="outline">
          Open dashboard
        </ButtonLink>
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
