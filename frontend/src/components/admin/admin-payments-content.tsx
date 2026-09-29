"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatAdminDate, paymentStatusClass } from "@/components/admin/admin-format";
import {
  ApiError,
  getAdminPayments,
  reconcileAdminPayment,
  type AdminPaymentRow,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

const RECONCILABLE_STATUSES = new Set(["pending", "confirming"]);

export function AdminPaymentsContent() {
  const [payments, setPayments] = useState<AdminPaymentRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reconcilingId, setReconcilingId] = useState<string | null>(null);
  const [reconcileError, setReconcileError] = useState<string | null>(null);
  const [openRowId, setOpenRowId] = useState<string | null>(null);
  const [paymentIdDraft, setPaymentIdDraft] = useState("");

  function toggleReconcileForm(paymentRowId: string) {
    setReconcileError(null);
    setPaymentIdDraft("");
    setOpenRowId((current) => (current === paymentRowId ? null : paymentRowId));
  }

  async function handleReconcile(payment: AdminPaymentRow) {
    const paymentId = paymentIdDraft.trim();
    if (!paymentId) {
      setReconcileError("Enter the NOWPayments payment ID shown in their dashboard.");
      return;
    }
    setReconcileError(null);
    setReconcilingId(payment.id);
    try {
      const updated = await reconcileAdminPayment(payment.order_id, paymentId);
      setPayments((rows) => rows.map((row) => (row.id === updated.id ? updated : row)));
      setOpenRowId(null);
      setPaymentIdDraft("");
    } catch (err) {
      setReconcileError(
        err instanceof ApiError ? err.detail : "Failed to reconcile this payment"
      );
    } finally {
      setReconcilingId(null);
    }
  }

  useEffect(() => {
    let cancelled = false;
    getAdminPayments()
      .then((rows) => {
        if (!cancelled) setPayments(rows);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load payments");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading payments…
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn’t load payments"
        description={error}
        action={{ label: "Retry", href: "/admin/payments" }}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Payments"
        description="Live Paystack and NOWPayments checkouts. A seat unlocks only after status is confirmed."
      />
      {payments.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No payments yet"
          description="Checkout attempts for the featured cohort and courses will show here."
        />
      ) : (
        <div className="rounded-xl border shadow-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order</TableHead>
                <TableHead>Student</TableHead>
                <TableHead>Item</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {payments.map((payment) => (
                <TableRow key={payment.id}>
                  <TableCell className="font-mono text-xs">{payment.order_id}</TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{payment.user_name || "-"}</p>
                      <p className="text-xs text-muted-foreground">{payment.user_email}</p>
                    </div>
                  </TableCell>
                  <TableCell>{payment.cohort_name || payment.course_title || "-"}</TableCell>
                  <TableCell className="font-medium">
                    {formatPrice(payment.amount, payment.currency)}
                  </TableCell>
                  <TableCell className="capitalize">{payment.provider}</TableCell>
                  <TableCell>
                    <Badge className={paymentStatusClass(payment.status)}>{payment.status}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatAdminDate(payment.confirmed_at || payment.created_at)}
                  </TableCell>
                  <TableCell>
                    {payment.provider === "nowpayments" &&
                      RECONCILABLE_STATUSES.has(payment.status) && (
                        <div className="flex flex-col items-end gap-1">
                          {openRowId === payment.id ? (
                            <div className="flex items-center gap-1">
                              <Input
                                autoFocus
                                placeholder="NOWPayments payment ID"
                                value={paymentIdDraft}
                                onChange={(event) => setPaymentIdDraft(event.target.value)}
                                className="h-8 w-40 text-xs"
                              />
                              <Button
                                size="sm"
                                disabled={reconcilingId === payment.id}
                                onClick={() => handleReconcile(payment)}
                              >
                                {reconcilingId === payment.id ? (
                                  <Loader2 className="size-4 animate-spin" />
                                ) : (
                                  "Confirm"
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleReconcileForm(payment.id)}
                              >
                                Cancel
                              </Button>
                            </div>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => toggleReconcileForm(payment.id)}
                            >
                              Reconcile
                            </Button>
                          )}
                          {openRowId === payment.id && reconcileError && (
                            <p className="max-w-56 text-right text-xs text-destructive">
                              {reconcileError}
                            </p>
                          )}
                        </div>
                      )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
