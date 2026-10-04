"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, Loader2 } from "lucide-react";
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
import { formatAdminDate } from "@/components/admin/admin-format";
import {
  ApiError,
  getAdminClassroomCohorts,
  getAdminStudents,
  type AdminCohortOption,
  type AdminStudentList,
  type AdminStudentRow,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

type PaymentFilter = "all" | "paid" | "partial" | "unpaid";

function statusClass(status: string) {
  if (status === "paid") return "bg-success/10 text-success";
  if (status === "partial") return "bg-warning/10 text-warning";
  return "bg-destructive/10 text-destructive";
}

function money(amount: string, currency: string | null) {
  return formatPrice(Number(amount), currency || "USD");
}

export function AdminStudentsContent() {
  const [data, setData] = useState<AdminStudentList | null>(null);
  const [cohorts, setCohorts] = useState<AdminCohortOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [status, setStatus] = useState<PaymentFilter>("all");
  const [plan, setPlan] = useState<"all" | "full" | "installments">("all");
  const [cohortId, setCohortId] = useState("");
  const [outstandingOnly, setOutstandingOnly] = useState(false);
  const [query, setQuery] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getAdminStudents({
        paymentStatus: status,
        plan,
        cohortId: cohortId || undefined,
        hasOutstanding: outstandingOnly,
        q: query.trim() || undefined,
      });
      setData(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load students");
    } finally {
      setLoading(false);
    }
  }, [status, plan, cohortId, outstandingOnly, query]);

  useEffect(() => {
    getAdminClassroomCohorts().then(setCohorts).catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setTimeout(load, 200);
    return () => clearTimeout(timer);
  }, [load]);

  function exportCsv() {
    if (!data) return;
    const header = [
      "email",
      "name",
      "status",
      "plan",
      "amount_paid",
      "amount_outstanding",
      "next_due_date",
      "next_due_amount",
      "cohorts",
    ];
    const lines = data.rows.map((row) =>
      [
        row.email,
        row.full_name ?? "",
        row.payment_status,
        row.plan_name ?? "",
        row.amount_paid,
        row.amount_outstanding,
        row.next_due_date ?? "",
        row.next_due_amount ?? "",
        row.cohorts.join("; "),
      ]
        .map((value) => `"${String(value).replace(/"/g, '""')}"`)
        .join(",")
    );
    const csv = [header.join(","), ...lines].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = "students.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(href);
  }

  const field = "h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm";
  const filterButtons: { key: PaymentFilter; label: string; count: number }[] = [
    { key: "all", label: "All", count: data?.total ?? 0 },
    { key: "paid", label: "Paid", count: data?.paid ?? 0 },
    { key: "partial", label: "Partial", count: data?.partial ?? 0 },
    { key: "unpaid", label: "Unpaid", count: data?.unpaid ?? 0 },
  ];

  return (
    <div>
      <PageHeader
        title="Students"
        description="Filter who has paid, who is part-paid, and who still owes tuition."
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        {filterButtons.map((button) => (
          <Button
            key={button.key}
            size="sm"
            variant={status === button.key ? "default" : "outline"}
            onClick={() => setStatus(button.key)}
          >
            {button.label} ({button.count})
          </Button>
        ))}
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <Input
            placeholder="Search name or email"
            className="h-9 w-56"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <select
            className={cn(field, "w-44")}
            value={plan}
            onChange={(e) => setPlan(e.target.value as typeof plan)}
            aria-label="Plan filter"
          >
            <option value="all">All plans</option>
            <option value="full">Paid in full</option>
            <option value="installments">Installments</option>
          </select>
          <select
            className={cn(field, "w-52")}
            value={cohortId}
            onChange={(e) => setCohortId(e.target.value)}
            aria-label="Cohort filter"
          >
            <option value="">All cohorts</option>
            {cohorts.map((cohort) => (
              <option key={cohort.id} value={cohort.id}>
                {cohort.name}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={outstandingOnly}
              onChange={(e) => setOutstandingOnly(e.target.checked)}
            />
            Owing only
          </label>
          <Button variant="outline" size="sm" onClick={exportCsv} disabled={!data}>
            <Download className="size-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {error && (
        <p className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center gap-2 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Loading students…
        </div>
      ) : !data || data.rows.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No students match"
          description="Try a different filter, or clear the search."
        />
      ) : (
        <div className="rounded-xl border shadow-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student</TableHead>
                <TableHead>Enrollment</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead>Paid</TableHead>
                <TableHead>Outstanding</TableHead>
                <TableHead>Next due</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.rows.map((row: AdminStudentRow) => (
                <TableRow key={row.user_id}>
                  <TableCell>
                    <p className="font-medium">{row.full_name || "-"}</p>
                    <p className="text-xs text-muted-foreground">{row.email}</p>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {[...row.cohorts, ...row.courses].slice(0, 2).join(", ") || "-"}
                  </TableCell>
                  <TableCell className="text-sm">{row.plan_name || "-"}</TableCell>
                  <TableCell className="text-sm">{money(row.amount_paid, row.currency)}</TableCell>
                  <TableCell className="text-sm">
                    {money(row.amount_outstanding, row.currency)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {row.next_due_date
                      ? `${formatAdminDate(row.next_due_date)}${
                          row.next_due_amount
                            ? ` · ${money(row.next_due_amount, row.currency)}`
                            : ""
                        }`
                      : "-"}
                  </TableCell>
                  <TableCell>
                    <Badge className={statusClass(row.payment_status)}>{row.payment_status}</Badge>
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