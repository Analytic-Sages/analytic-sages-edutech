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

export function AdminBillingContent() {
  const [accounts, setAccounts] = useState<BillingAccountPublic[]>([]);
  const [selected, setSelected] = useState<BillingAccountPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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
      {error ? (
        <p className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {accounts.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No billing accounts"
          description="Accounts appear when students select a tuition plan at checkout."
        />
      ) : (
        <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          <div className="rounded-xl border shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Outstanding</TableHead>
                  <TableHead>Paid</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.map((row) => (
                  <TableRow
                    key={row.id}
                    className="cursor-pointer"
                    onClick={() => setSelected(row)}
                  >
                    <TableCell>
                      <Badge variant="outline">{row.billing_status}</Badge>
                    </TableCell>
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
