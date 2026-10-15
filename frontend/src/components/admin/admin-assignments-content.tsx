"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { InstructorAssignmentsPanel } from "@/components/classroom/instructor-assignments-panel";
import {
  getAdminClassroomCohorts,
  type AdminCohortOption,
} from "@/lib/api";

export function AdminAssignmentsContent() {
  const [cohorts, setCohorts] = useState<AdminCohortOption[]>([]);
  const [cohortId, setCohortId] = useState("");
  const [loadingCohorts, setLoadingCohorts] = useState(true);
  const [cohortError, setCohortError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAdminClassroomCohorts()
      .then((rows) => {
        if (cancelled) return;
        setCohorts(rows);
        if (rows.length > 0) setCohortId(rows[0].id);
      })
      .catch((err) => {
        if (!cancelled) {
          setCohortError(err instanceof Error ? err.message : "Could not load cohorts. Please refresh and try again.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingCohorts(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <PageHeader
        title="Assignments"
        description="Track submissions and review student work across a cohort."
      />

      {loadingCohorts ? (
        <p className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Loading cohorts…
        </p>
      ) : cohortError ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="Could not load cohorts"
          description={cohortError}
        />
      ) : cohorts.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No cohorts available"
          description="Create or activate a cohort to start tracking student assignment submissions."
        />
      ) : (
        <>
          <div className="mb-6">
            <select
              className="h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm"
              value={cohortId}
              onChange={(e) => setCohortId(e.target.value)}
              aria-label="Select cohort"
            >
              {cohorts.map((cohort) => (
                <option key={cohort.id} value={cohort.id}>
                  {cohort.name}
                </option>
              ))}
            </select>
          </div>
          {cohortId && <InstructorAssignmentsPanel cohortId={cohortId} />}
        </>
      )}
    </div>
  );
}
