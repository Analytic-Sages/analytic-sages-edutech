"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { confirmMockPayment } from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

function MockCheckoutInner() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const orderId = searchParams.get("order_id") ?? "";
  const provider = searchParams.get("provider") ?? "mock";
  const amount = Number(searchParams.get("amount") ?? "0");
  const currency = searchParams.get("currency") ?? "NGN";

  const [status, setStatus] = useState<"idle" | "loading" | "success" | "failed">("idle");
  const [error, setError] = useState<string | null>(null);

  async function confirm(next: "confirmed" | "failed") {
    if (!orderId) {
      setError("Missing order_id");
      return;
    }
    setStatus("loading");
    setError(null);
    try {
      await confirmMockPayment(orderId, next);
      if (next === "confirmed") {
        setStatus("success");
        router.push(`/checkout/success?order_id=${encodeURIComponent(orderId)}`);
      } else {
        setStatus("failed");
      }
    } catch (err) {
      setStatus("idle");
      setError(err instanceof Error ? err.message : "Confirmation failed");
    }
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="Mock payment gateway"
        description="Simulates Stripe, Paystack, or NOWPayments until live keys are configured."
      />

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle className="capitalize">{provider} checkout</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-xl bg-brand-surface p-4 text-sm">
            <p>
              <span className="text-muted-foreground">Order:</span> {orderId || "N/A"}
            </p>
            <p className="mt-2">
              <span className="text-muted-foreground">Amount:</span>{" "}
              {formatPrice(amount, currency)}
            </p>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          {status === "failed" ? (
            <div className="flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm">
              <XCircle className="mt-0.5 size-5 text-destructive" />
              Payment marked as failed. No enrollment was created.
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              <Button
                className="bg-brand-orange text-white hover:bg-brand-orange/90"
                disabled={status === "loading" || !orderId}
                onClick={() => confirm("confirmed")}
              >
                {status === "loading" ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="size-4" />
                )}
                Simulate success
              </Button>
              <Button
                variant="outline"
                disabled={status === "loading" || !orderId}
                onClick={() => confirm("failed")}
              >
                Simulate failure
              </Button>
            </div>
          )}

          <ButtonLink href="/courses" variant="ghost" className="w-full">
            Cancel and return to courses
          </ButtonLink>
        </CardContent>
      </Card>
    </div>
  );
}

export default function MockCheckoutPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-muted-foreground">Loading…</div>}>
      <MockCheckoutInner />
    </Suspense>
  );
}
