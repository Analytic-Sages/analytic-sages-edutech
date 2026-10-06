"use client";

import { useEffect, useState } from "react";
import { Download, Loader2 } from "lucide-react";
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
  getAdminCohortWaitlist,
  type AdminWaitlistResponse,
} from "@/lib/api";
import { formatAdminDate } from "@/components/admin/admin-format";

function toCsv(response: AdminWaitlistResponse): string {
  const header = [
    "full_name",
    "email",
    "phone",
    "phone_country_code",
    "country_of_residence",
    "discord_username",
    "telegram_username",
    "note",
    "joined_at",
  ];
  const escape = (value: string | null) => `"${(value ?? "").replace(/"/g, '""')}"`;
  const rows = response.entries.map((entry) =>
    [
      entry.full_name,
      entry.email,
      entry.phone_number,
      entry.phone_country_code,
      entry.country_of_residence,
      entry.discord_username,
      entry.telegram_username,
      entry.note,
      entry.created_at,
    ]
      .map((value) => escape(value))
      .join(","),
  );
  return [header.join(","), ...rows].join("\n");
}

export function AdminCohortWaitlistPanel({ slug }: { slug: string }) {
  const [data, setData] = useState<AdminWaitlistResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAdminCohortWaitlist(slug)
      .then((rows) => {
        if (!cancelled) setData(rows);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load waitlist");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  function downloadCsv() {
    if (!data) return;
    const blob = new Blob([toCsv(data)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${data.cohort_slug}-waitlist.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="mb-10">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-heading text-xl font-semibold">Waitlist</h2>
        {data && data.count > 0 && (
          <Button variant="outline" size="sm" onClick={downloadCsv}>
            <Download className="size-4" />
            Export CSV
          </Button>
        )}
      </div>

      {loading ? (
        <p className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading waitlist…
        </p>
      ) : error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : !data || data.count === 0 ? (
        <p className="text-sm text-muted-foreground">
          No waitlist entries yet. Interested students join from the programme page once
          registration closes.
        </p>
      ) : (
        <div className="rounded-xl border shadow-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Discord</TableHead>
                <TableHead>Telegram</TableHead>
                <TableHead>Joined</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.entries.map((entry) => (
                <TableRow key={entry.user_id}>
                  <TableCell>
                    <p className="font-medium">{entry.full_name || "-"}</p>
                    <p className="text-xs text-muted-foreground">{entry.email}</p>
                  </TableCell>
                  <TableCell className="text-sm">
                    {entry.phone_number
                      ? `${entry.phone_country_code ? `+${entry.phone_country_code} ` : ""}${entry.phone_number}`
                      : "-"}
                  </TableCell>
                  <TableCell className="text-sm">{entry.discord_username || "-"}</TableCell>
                  <TableCell className="text-sm">{entry.telegram_username || "-"}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatAdminDate(entry.created_at)}
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