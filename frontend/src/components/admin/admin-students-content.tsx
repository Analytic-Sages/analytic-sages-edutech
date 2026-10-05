"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Download, Loader2, Lock, LockOpen, Pencil } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
  extendAdminNextDue,
  getAdminClassroomCohorts,
  getAdminCourses,
  getAdminStudents,
  setAdminAccountAccess,
  type AdminCohortOption,
  type AdminCourseRow,
  type AdminStudentList,
  type AdminStudentRow,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

type PaymentFilter = "all" | "paid" | "partial";

function programLabel(row: AdminStudentRow) {
  return row.cohorts[0] ?? row.courses[0] ?? "Other";
}

function toDateInput(iso: string | null) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString().slice(0, 10);
}

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
  const [courses, setCourses] = useState<AdminCourseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const [status, setStatus] = useState<PaymentFilter>("all");
  const [plan, setPlan] = useState<"all" | "full" | "installments">("all");
  const [cohortId, setCohortId] = useState("");
  const [courseId, setCourseId] = useState("");
  const [outstandingOnly, setOutstandingOnly] = useState(false);
  const [groupBy, setGroupBy] = useState(false);
  const [query, setQuery] = useState("");

  const [managing, setManaging] = useState<AdminStudentRow | null>(null);
  const [dueDate, setDueDate] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getAdminStudents({
        paymentStatus: status,
        plan,
        cohortId: cohortId || undefined,
        courseId: courseId || undefined,
        hasOutstanding: outstandingOnly,
        q: query.trim() || undefined,
      });
      setData(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load students");
    } finally {
      setLoading(false);
    }
  }, [status, plan, cohortId, courseId, outstandingOnly, query]);

  useEffect(() => {
    getAdminClassroomCohorts().then(setCohorts).catch(() => {});
    getAdminCourses()
      .then((rows) => setCourses(rows.filter((course) => course.delivery_type !== "self_paced")))
      .catch(() => {});
  }, []);

  const grouped = useMemo(() => {
    if (!data) return [];
    const map = new Map<string, AdminStudentRow[]>();
    for (const row of data.rows) {
      const label = programLabel(row);
      const bucket = map.get(label) ?? [];
      bucket.push(row);
      map.set(label, bucket);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [data]);

  function openManage(row: AdminStudentRow) {
    setManaging(row);
    setDueDate(toDateInput(row.next_due_date));
    setActionMessage(null);
  }

  async function saveDueDate() {
    if (!managing?.billing_account_id || !dueDate) return;
    setBusy(`due:${managing.user_id}`);
    setActionMessage(null);
    try {
      const iso = new Date(`${dueDate}T00:00:00.000Z`).toISOString();
      await extendAdminNextDue(managing.billing_account_id, iso, "Admin set due date");
      setActionMessage("Next due date updated.");
      setManaging(null);
      await load();
    } catch (err) {
      setActionMessage(err instanceof ApiError ? err.detail : "Could not update due date");
    } finally {
      setBusy(null);
    }
  }

  async function toggleAccess() {
    if (!managing?.billing_account_id) return;
    setBusy(`access:${managing.user_id}`);
    setActionMessage(null);
    try {
      await setAdminAccountAccess(
        managing.billing_account_id,
        !managing.access_blocked,
        managing.access_blocked ? "Admin restored access" : "Admin restricted access",
      );
      setActionMessage(
        managing.access_blocked ? "Live access restored." : "Live access restricted until paid.",
      );
      setManaging(null);
      await load();
    } catch (err) {
      setActionMessage(err instanceof ApiError ? err.detail : "Could not update access");
    } finally {
      setBusy(null);
    }
  }

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
      "courses",
      "cohorts",
      "access_blocked",
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
        row.courses.join("; "),
        row.cohorts.join("; "),
        row.access_blocked ? "yes" : "no",
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
  ];

  return (
    <div>
      <PageHeader
        title="Students"
        description="Paid students grouped by program. Only successful (full or installment) payments appear here."
      />

      <div className="mb-6 flex flex-wrap items-end gap-3">
        <Input
          className="w-64"
          placeholder="Search name or email"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
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
        <select
          className={cn(field, "w-52")}
          value={courseId}
          onChange={(e) => setCourseId(e.target.value)}
          aria-label="Course filter"
        >
          <option value="">All programs</option>
          {courses.map((course) => (
            <option key={course.id} value={course.id}>
              {course.title}
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
        <label className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={groupBy}
            onChange={(e) => setGroupBy(e.target.checked)}
          />
          Group by program
        </label>
        <Button variant="outline" size="sm" onClick={exportCsv} disabled={!data}>
          <Download className="size-4" />
          Export CSV
        </Button>
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
        <div className="space-y-6">
          {(groupBy ? grouped : [["All", data.rows] as [string, AdminStudentRow[]]]).map(
            ([label, rows]) => (
              <div key={label} className="rounded-xl border shadow-card">
                <div className="border-b px-4 py-2 text-sm font-medium text-muted-foreground">
                  {label} · {rows.length} student{rows.length === 1 ? "" : "s"}
                </div>
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
                      <TableHead className="text-right">Manage</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((row) => (
                <TableRow key={row.user_id}>
                  <TableCell>
                    <Link href={`/admin/users/${row.user_id}`} className="hover:underline">
                      <p className="font-medium">{row.full_name || "-"}</p>
                      <p className="text-xs text-muted-foreground">{row.email}</p>
                    </Link>
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
                    {row.access_blocked && (
                      <Badge className="ml-1 bg-destructive/10 text-destructive">
                        restricted
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Dialog
                      open={managing?.user_id === row.user_id}
                      onOpenChange={(open) => {
                        if (!open) setManaging(null);
                      }}
                    >
                      <Button variant="ghost" size="sm" onClick={() => openManage(row)}>
                        <Pencil className="size-4" />
                        Manage
                      </Button>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>{row.full_name || row.email}</DialogTitle>
                          <DialogDescription>
                            Set the next due date or restrict live-session access for this
                            student.
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div className="space-y-2">
                            <Label htmlFor="next-due">Next due date</Label>
                            <div className="flex gap-2">
                              <Input
                                id="next-due"
                                type="date"
                                value={dueDate}
                                onChange={(e) => setDueDate(e.target.value)}
                              />
                              <Button
                                size="sm"
                                disabled={!dueDate || busy === `due:${row.user_id}`}
                                onClick={saveDueDate}
                              >
                                {busy === `due:${row.user_id}` ? "Saving…" : "Save"}
                              </Button>
                            </div>
                          </div>
                          <div className="flex items-center justify-between rounded-md border p-3">
                            <div className="text-sm">
                              <p className="font-medium">Live session access</p>
                              <p className="text-muted-foreground">
                                {row.access_blocked
                                  ? "Restricted until tuition is paid."
                                  : "Access enabled."}
                              </p>
                            </div>
                            <Button
                              size="sm"
                              variant={row.access_blocked ? "default" : "outline"}
                              disabled={
                                !row.billing_account_id || busy === `access:${row.user_id}`
                              }
                              onClick={toggleAccess}
                            >
                              {row.access_blocked ? (
                                <LockOpen className="size-4" />
                              ) : (
                                <Lock className="size-4" />
                              )}
                              {busy === `access:${row.user_id}`
                                ? "…"
                                : row.access_blocked
                                  ? "Restore"
                                  : "Restrict"}
                            </Button>
                          </div>
                          {actionMessage && (
                            <p className="text-sm text-muted-foreground">{actionMessage}</p>
                          )}
                        </div>
                        <DialogFooter>
                          <Button variant="outline" size="sm" onClick={() => setManaging(null)}>
                            Close
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </TableCell>
                </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}