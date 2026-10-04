"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatAdminDate } from "@/components/admin/admin-format";
import {
  ApiError,
  extendAdminObligation,
  getAccessToken,
  getAdminBillingAccounts,
  patchAdminBillingAccount,
  waiveAdminObligation,
  type BillingAccountPublic,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

type PlanFilter = "all" | "installments" | "paid" | "due";

function matchesPlanFilter(row: BillingAccountPublic, filter: PlanFilter): boolean {
  if (filter === "installments") return !row.is_paid_in_full;
  if (filter === "paid") return Boolean(row.is_paid_in_full);
  if (filter === "due") {
    return row.next_due_status === "past_due" || row.billing_status === "past_due";
  }
  return true;
}

function planLabel(row: BillingAccountPublic): string {
  if (row.plan_name) return row.plan_name;
  if (row.plan_type === "installment") return "Installments";
  if (row.plan_type === "one_time") return "One-time";
  return "-";
}

// Plans that were closed out (abandoned / refunded) are not collectable and do not
// belong on the billing board.
const CLOSED_STATUSES = new Set(["cancelled", "refunded"]);

/**
 * Ordering for the board: installment plans that still owe money come first (they
 * are the priority for follow-up), then payments captured in full, then the rest.
 */
function accountPriority(row: BillingAccountPublic): number {
  const isInstallment = row.plan_type === "installment" || row.plan_type === "monthly";
  if (isInstallment && !row.is_paid_in_full) return 0;
  if (row.is_paid_in_full) return 1;
  return 2;
}

export function AdminBillingContent() {
  const [accounts, setAccounts] = useState<BillingAccountPublic[]>([]);
  const [selected, setSelected] = useState<BillingAccountPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [planFilter, setPlanFilter] = useState<PlanFilter>("all");

  async function reload() {
    const rows = await getAdminBillingAccounts();
    setAccounts(rows);
    if (selected) {
      const next = rows.find((r) => r.id === selected.id) ?? null;
      setSelected(next);
    }
  }

  useEffect(() => {
    let cancelled = false;
    getAdminBillingAccounts()
      .then((rows) => {
        if (!cancelled) setAccounts(rows);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load billing");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function runAction(fn: () => Promise<BillingAccountPublic>) {
    setBusy(true);
    setError(null);
    try {
      const updated = await fn();
      setSelected(updated);
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  const openAccounts = accounts.filter((row) => !CLOSED_STATUSES.has(row.billing_status));
  const paidCount = openAccounts.filter((row) => row.is_paid_in_full).length;
  const installmentCount = openAccounts.filter((row) => !row.is_paid_in_full).length;
  const dueCount = openAccounts.filter((row) => matchesPlanFilter(row, "due")).length;
  // Installments are the priority: they carry money still owed (including partial
  // payers), so they sort above fully-settled accounts.
  const visibleAccounts = openAccounts
    .filter((row) => matchesPlanFilter(row, planFilter))
    .sort(
      (a, b) =>
        accountPriority(a) - accountPriority(b) ||
        Number(b.amount_outstanding) - Number(a.amount_outstanding)
    );

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading billing…
      </div>
    );
  }

  if (error && accounts.length === 0) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn’t load billing"
        description={error}
        action={{ label: "Retry", href: "/admin/billing" }}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Billing"
        description="Student tuition accounts, installments, and admin adjustments. Provider attempts stay under Payments."
      />
      <div className="mt-4 flex flex-wrap gap-3 text-sm">
        <Link href="/admin/payments" className="text-brand-orange hover:underline">
          Provider payments
        </Link>
        <button
          type="button"
          className="text-brand-orange hover:underline"
          onClick={async () => {
            try {
              const token = getAccessToken();
              const res = await fetch("/api/v1/admin/billing/export.csv", {
                credentials: "include",
                headers: token ? { Authorization: `Bearer ${token}` } : {},
              });
              if (!res.ok) throw new Error("Export failed");
              const blob = await res.blob();
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "billing-accounts.csv";
              a.click();
              URL.revokeObjectURL(url);
            } catch {
              setError("CSV export failed");
            }
          }}
        >
          Export CSV
        </button>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          size="sm"
          variant={planFilter === "installments" ? "default" : "outline"}
          onClick={() => setPlanFilter("installments")}
        >
          Installments ({installmentCount})
        </Button>
        <Button
          size="sm"
          variant={planFilter === "paid" ? "default" : "outline"}
          onClick={() => setPlanFilter("paid")}
        >
          Paid in full ({paidCount})
        </Button>
        <Button
          size="sm"
          variant={planFilter === "due" ? "default" : "outline"}
          onClick={() => setPlanFilter("due")}
        >
          Past due ({dueCount})
        </Button>
        <Button
          size="sm"
          variant={planFilter === "all" ? "default" : "outline"}
          onClick={() => setPlanFilter("all")}
        >
          All ({openAccounts.length})
        </Button>
        <span className="self-center text-xs text-muted-foreground">
          Installment plans shown first.
        </span>
      </div>
      {error ? (
        <p className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {openAccounts.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No billing accounts"
          description="Accounts appear when students select a tuition plan at checkout."
        />
      ) : visibleAccounts.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No accounts match this filter"
          description="Try a different billing status filter."
        />
      ) : (
        <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          <div className="rounded-xl border shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Outstanding</TableHead>
                  <TableHead>Paid</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visibleAccounts.map((row) => (
                  <TableRow
                    key={row.id}
                    className="cursor-pointer"
                    onClick={() => setSelected(row)}
                  >
                    <TableCell>
                      <Badge variant="outline">{row.billing_status}</Badge>
                    </TableCell>
                    <TableCell>{planLabel(row)}</TableCell>
                    <TableCell>
                      {formatPrice(Number(row.amount_outstanding), row.currency)}
                    </TableCell>
                    <TableCell>
                      {formatPrice(Number(row.amount_paid), row.currency)}
                    </TableCell>
                    <TableCell>{formatAdminDate(row.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="rounded-xl border p-4 shadow-card">
            {selected ? (
              <div className="space-y-4">
                <div>
                  <h2 className="font-heading text-lg font-semibold">Account detail</h2>
                  <p className="text-xs text-muted-foreground break-all">{selected.id}</p>
                </div>
                <p className="text-sm">
                  Due {formatPrice(Number(selected.final_amount_due), selected.currency)} ·
                  Outstanding{" "}
                  {formatPrice(Number(selected.amount_outstanding), selected.currency)}
                </p>
                <ul className="space-y-2 text-sm">
                  {selected.obligations.map((o) => (
                    <li key={o.id} className="rounded-md border p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span>{o.description}</span>
                        <Badge variant="secondary">{o.status}</Badge>
                      </div>
                      <p className="mt-1 text-muted-foreground">
                        {formatPrice(Number(o.amount_due), o.currency)} · due{" "}
                        {o.due_date ? formatAdminDate(o.due_date) : "—"}
                      </p>
                      {["open", "past_due", "upcoming", "processing"].includes(o.status) ? (
                        <div className="mt-2 flex flex-wrap gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={busy}
                            onClick={() =>
                              runAction(() => waiveAdminObligation(o.id, "Admin waive"))
                            }
                          >
                            Waive
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={busy}
                            onClick={() => {
                              const next = new Date();
                              next.setDate(next.getDate() + 14);
                              return runAction(() =>
                                extendAdminObligation(
                                  o.id,
                                  next.toISOString(),
                                  "Admin extend +14d",
                                ),
                              );
                            }}
                          >
                            Extend +14d
                          </Button>
                        </div>
                      ) : null}
                    </li>
                  ))}
                </ul>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy}
                    onClick={() =>
                      runAction(() =>
                        patchAdminBillingAccount(selected.id, {
                          billing_status: "payment_hold",
                          note: "Admin hold",
                        }),
                      )
                    }
                  >
                    Set payment hold
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy}
                    onClick={() =>
                      runAction(() =>
                        patchAdminBillingAccount(selected.id, {
                          billing_status: "current",
                          note: "Admin clear hold",
                        }),
                      )
                    }
                  >
                    Mark current
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Select an account to manage.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
