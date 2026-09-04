"use client";

import { useEffect, useState } from "react";
import { Bitcoin, Landmark, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiError,
  getAccessToken,
  getMyBillingAccounts,
  payBillingObligation,
  type BillingAccountPublic,
  type PaymentProvider,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

const providers: { id: PaymentProvider; label: string; icon: typeof Landmark }[] = [
  { id: "paystack", label: "Pay with Paystack", icon: Landmark },
  { id: "nowpayments", label: "Pay with crypto", icon: Bitcoin },
];

function formatDate(iso: string | null) {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function statusLabel(status: string) {
  return status.replaceAll("_", " ");
}

export function StudentBillingContent() {
  const [accounts, setAccounts] = useState<BillingAccountPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authed, setAuthed] = useState(true);
  const [paying, setPaying] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!getAccessToken()) {
        if (!cancelled) {
          setAuthed(false);
          setLoading(false);
        }
        return;
      }
      try {
        const rows = await getMyBillingAccounts();
        if (!cancelled) {
          setAccounts(rows);
          setAuthed(true);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load billing");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handlePay(obligationId: string, provider: PaymentProvider) {
    setPaying(`${obligationId}:${provider}`);
    setError(null);
    try {
      const session = await payBillingObligation(obligationId, provider);
      window.location.assign(session.checkout_url);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Payment failed");
      setPaying(null);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading billing…
      </div>
    );
  }

  if (!authed) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Sign in to view billing"
        description="Tuition plans and installment history appear here after you register."
        action={{ label: "Sign in", href: "/login?next=/dashboard/billing" }}
      />
    );
  }

  if (error && accounts.length === 0) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn’t load billing"
        description={error}
        action={{ label: "Retry", href: "/dashboard/billing" }}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Billing"
        description="Track tuition plans, installments, and pay any open balance."
      />
      {error ? (
        <p className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}
      {accounts.length === 0 ? (
        <EmptyState
          icon={<Landmark className="size-6" />}
          title="No tuition accounts yet"
          description="When you choose a tuition plan at cohort checkout, it will show here."
          action={{ label: "Browse programs", href: "/instructor-led" }}
        />
      ) : (
        <div className="mt-8 space-y-6">
          {accounts.map((account) => {
            const payable = account.obligations.find((o) =>
              ["open", "past_due", "processing"].includes(o.status),
            );
            return (
              <Card key={account.id} className="shadow-card">
                <CardHeader className="flex flex-row items-start justify-between gap-4">
                  <div>
                    <CardTitle className="font-heading text-lg">
                      {account.tuition_plan?.name || "Tuition plan"}
                    </CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Paid {formatPrice(Number(account.amount_paid), account.currency)} of{" "}
                      {formatPrice(Number(account.final_amount_due), account.currency)}
                    </p>
                  </div>
                  <Badge variant="outline">{statusLabel(account.billing_status)}</Badge>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm">
                    Outstanding:{" "}
                    <span className="font-medium">
                      {formatPrice(Number(account.amount_outstanding), account.currency)}
                    </span>
                  </p>
                  <ul className="space-y-2 text-sm">
                    {account.obligations.map((o) => (
                      <li
                        key={o.id}
                        className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 py-2 last:border-0"
                      >
                        <span>
                          {o.description || `Installment ${o.sequence_number}`}
                          <span className="ml-2 text-muted-foreground">
                            due {formatDate(o.due_date)}
                          </span>
                        </span>
                        <span className="flex items-center gap-2">
                          {formatPrice(Number(o.amount_due), o.currency)}
                          <Badge variant="secondary">{statusLabel(o.status)}</Badge>
                        </span>
                      </li>
                    ))}
                  </ul>
                  {payable ? (
                    <div className="flex flex-wrap gap-2 pt-2">
                      {providers.map((p) => {
                        const Icon = p.icon;
                        const busy = paying === `${payable.id}:${p.id}`;
                        return (
                          <Button
                            key={p.id}
                            type="button"
                            variant="outline"
                            disabled={Boolean(paying)}
                            onClick={() => handlePay(payable.id, p.id)}
                          >
                            <Icon className="mr-2 size-4" />
                            {busy ? "Redirecting…" : p.label}
                          </Button>
                        );
                      })}
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
