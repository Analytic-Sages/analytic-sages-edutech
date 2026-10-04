"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { BellRing, Loader2, Send } from "lucide-react";
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
import {
  ApiError,
  getAdminInstallments,
  remindAdminInstallments,
  remindAdminObligation,
  type AdminInstallmentRow,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";
import { formatAdminDate } from "@/components/admin/admin-format";

type Bucket = "all" | "overdue" | "due_soon" | "upcoming";

const BUCKET_LABELS: Record<Exclude<Bucket, "all">, string> = {
  overdue: "Overdue",
  due_soon: "Due soon",
  upcoming: "Upcoming",
};

function bucketClass(bucket: string) {
  if (bucket === "overdue") return "bg-destructive/10 text-destructive";
  if (bucket === "due_soon") return "bg-warning/10 text-warning";
  return "bg-muted text-muted-foreground";
}

export function AdminCollectionsContent() {
  const [rows, setRows] = useState<AdminInstallmentRow[]>([]);
  const [bucket, setBucket] = useState<Bucket>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [bulkBusy, setBulkBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAdminInstallments();
      setRows(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load installments");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    return () => clearTimeout(timer);
  }, [load]);

  const counts = useMemo(() => {
    const result = { all: 0, overdue: 0, due_soon: 0, upcoming: 0 };
    for (const row of rows) {
      result.all += 1;
      if (row.bucket in result) {
        result[row.bucket as "overdue" | "due_soon" | "upcoming"] += 1;
      }
    }
    return result;
  }, [rows]);

  const visible = useMemo(
    () => (bucket === "all" ? rows : rows.filter((row) => row.bucket === bucket)),
    [rows, bucket]
  );

  async function remindOne(row: AdminInstallmentRow) {
    setBusyId(row.obligation_id);
    setError(null);
    setMessage(null);
    try {
      const result = await remindAdminObligation(row.obligation_id);
      setMessage(
        result.sent ? `Reminder sent to ${row.email}.` : `${row.email} was skipped (already sent).`
      );
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not send reminder");
    } finally {
      setBusyId(null);
    }
  }

  async function remindAll(scope: "overdue" | "due_soon" | "all") {
    setBulkBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await remindAdminInstallments({ scope });
      setMessage(`Sent ${result.sent}, skipped ${result.skipped}, failed ${result.failed}.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not send reminders");
    } finally {
      setBulkBusy(false);
    }
  }

  const chip = (key: Bucket, label: string, count: number) => (
    <Button
      key={key}
      size="sm"
      variant={bucket === key ? "default" : "outline"}
      onClick={() => setBucket(key)}
    >
      {label} ({count})
    </Button>
  );

  return (
    <div>
      <PageHeader
        title="Collections"
        description="Installment deadlines and payment reminders for tuition plans."
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        {chip("all", "All", counts.all)}
        {chip("overdue", BUCKET_LABELS.overdue, counts.overdue)}
        {chip("due_soon", BUCKET_LABELS.due_soon, counts.due_soon)}
        {chip("upcoming", BUCKET_LABELS.upcoming, counts.upcoming)}
        <div className="ml-auto flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={bulkBusy}
            onClick={() => remindAll("overdue")}
          >
            {bulkBusy ? <Loader2 className="size-4 animate-spin" /> : <BellRing className="size-4" />}
            Remind overdue
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={bulkBusy}
            onClick={() => remindAll("due_soon")}
          >
            <BellRing className="size-4" />
            Remind due-soon
          </Button>
        </div>
      </div>

      {error && (
        <p className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}
      {message && (
        <p className="mb-4 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
          {message}
        </p>
      )}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center gap-2 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Loading installments…
        </div>
      ) : visible.length === 0 ? (
        <EmptyState
          icon={<BellRing className="size-6" />}
          title="Nothing here"
          description="No installments match this filter."
        />
      ) : (
        <div className="rounded-xl border shadow-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead>Installment</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Due</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visible.map((row) => (
                <TableRow key={row.obligation_id}>
                  <TableCell>
                    <p className="font-medium">{row.full_name || "-"}</p>
                    <p className="text-xs text-muted-foreground">{row.email}</p>
                  </TableCell>
                  <TableCell className="text-sm">{row.plan_name || "-"}</TableCell>
                  <TableCell className="text-sm">
                    {row.sequence_number} of {row.installments_total}
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatPrice(Number(row.amount_due), row.currency)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {row.due_date ? formatAdminDate(row.due_date) : "-"}
                    {row.days_until_due !== null && row.bucket !== "paid" ? (
                      <span className="ml-1 text-xs">
                        ({row.days_until_due < 0 ? `${Math.abs(row.days_until_due)}d late` : `in ${row.days_until_due}d`})
                      </span>
                    ) : null}
                  </TableCell>
                  <TableCell>
                    <Badge className={bucketClass(row.bucket)}>{row.bucket.replace("_", " ")}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end">
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={busyId === row.obligation_id || row.bucket === "paid"}
                        onClick={() => remindOne(row)}
                        title="Send reminder email"
                      >
                        {busyId === row.obligation_id ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : (
                          <Send className="size-4" />
                        )}
                        Remind
                      </Button>
                    </div>
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