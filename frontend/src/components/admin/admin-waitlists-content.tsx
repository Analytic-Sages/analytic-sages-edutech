"use client";

import { useEffect, useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
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
  getAdminClassroomCohorts,
  getAdminCohortWaitlist,
  type AdminWaitlistResponse,
  type AdminWaitlistRow,
} from "@/lib/api";

type ProgramWaitlist = AdminWaitlistResponse;

function csvCell(value: string | null) {
  return `"${(value ?? "").replace(/"/g, '""')}"`;
}

function phone(entry: AdminWaitlistRow) {
  if (!entry.phone_number) return "";
  return `${entry.phone_country_code ? `+${entry.phone_country_code} ` : ""}${entry.phone_number}`;
}

function rowsToCsv(programs: ProgramWaitlist[]) {
  const header = [
    "programme",
    "full_name",
    "email",
    "phone",
    "country_of_residence",
    "discord_username",
    "telegram_username",
    "note",
    "joined_at",
  ];
  const lines = programs.flatMap((program) =>
    program.entries.map((entry) =>
      [
        program.cohort_name,
        entry.full_name,
        entry.email,
        phone(entry),
        entry.country_of_residence,
        entry.discord_username,
        entry.telegram_username,
        entry.note,
        entry.created_at,
      ]
        .map((value) => csvCell(value))
        .join(","),
    ),
  );
  return [header.join(","), ...lines].join("\n");
}

function downloadCsv(filename: string, csv: string) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function AdminWaitlistsContent() {
  const [programs, setPrograms] = useState<ProgramWaitlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const cohorts = await getAdminClassroomCohorts();
        const lists = await Promise.all(
          cohorts.map((cohort) => getAdminCohortWaitlist(cohort.slug)),
        );
        if (!cancelled) {
          setPrograms(
            [...lists].sort((a, b) => a.cohort_name.localeCompare(b.cohort_name)),
          );
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load waitlists");
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

  const total = programs.reduce((sum, program) => sum + program.count, 0);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading waitlists…
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn’t load waitlists"
        description={error}
        action={{ label: "Retry", href: "/admin/waitlists" }}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Waitlists"
        description="People waiting for the next intake, grouped by programme."
        action={
          total > 0 ? (
            <Button
              variant="outline"
              onClick={() => downloadCsv("programme-waitlists.csv", rowsToCsv(programs))}
            >
              <Download className="size-4" />
              Export all
            </Button>
          ) : null
        }
      />

      {programs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No programmes to list yet.</p>
      ) : (
        <div className="space-y-10">
          {programs.map((program) => (
            <section key={program.cohort_id}>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-heading text-xl font-semibold">{program.cohort_name}</h2>
                  <p className="text-sm text-muted-foreground">
                    {program.count} {program.count === 1 ? "person" : "people"}
                    {program.is_open ? " · Waitlist open" : " · Waitlist closed"}
                  </p>
                </div>
                {program.count > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      downloadCsv(`${program.cohort_slug}-waitlist.csv`, rowsToCsv([program]))
                    }
                  >
                    <Download className="size-4" />
                    Export CSV
                  </Button>
                )}
              </div>
              {program.count === 0 ? (
                <p className="text-sm text-muted-foreground">No one on this waitlist yet.</p>
              ) : (
                <div className="rounded-xl border shadow-card">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Contact</TableHead>
                        <TableHead>Country</TableHead>
                        <TableHead>Discord</TableHead>
                        <TableHead>Telegram</TableHead>
                        <TableHead>Joined</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {program.entries.map((entry) => (
                        <TableRow key={entry.user_id}>
                          <TableCell>
                            <p className="font-medium">{entry.full_name || "-"}</p>
                            <p className="text-xs text-muted-foreground">{entry.email}</p>
                          </TableCell>
                          <TableCell className="text-sm">{phone(entry) || "-"}</TableCell>
                          <TableCell className="text-sm">
                            {entry.country_of_residence || "-"}
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
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
