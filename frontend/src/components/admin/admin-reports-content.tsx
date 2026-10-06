"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { InstructorReportPanel } from "@/components/classroom/instructor-report-panel";
import {
  ApiError,
  getAdminClassroomCohorts,
  type AdminCohortOption,
} from "@/lib/api";

export function AdminReportsContent() {
  const [cohorts, setCohorts] = useState<AdminCohortOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAdminClassroomCohorts()
      .then((rows) => {
        if (cancelled) return;
        setCohorts(rows);
        if (rows.length > 0) setSelectedId(rows[0].id);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load cohorts");
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
        Loading reports…
      </div>
    );
  }

  if (error) {
    return <EmptyState icon={<Loader2 className="size-6" />} title="Couldn’t load reports" description={error} />;
  }

  if (cohorts.length === 0) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="No cohorts yet"
        description="Create a cohort to see student performance reports."
      />
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <PageHeader
          title="Reports"
          description="Attendance, assignment completion and grades across a cohort."
        />
        <select
          className="h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm"
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          aria-label="Select cohort"
        >
          {cohorts.map((cohort) => (
            <option key={cohort.id} value={cohort.id}>
              {cohort.name}
            </option>
          ))}
        </select>
      </div>

      {selectedId && <InstructorReportPanel key={selectedId} cohortId={selectedId} />}
    </div>
  );
}