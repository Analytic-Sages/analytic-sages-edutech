"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { InstructorAssignmentsPanel } from "@/components/classroom/instructor-assignments-panel";
import { ApiError, listInstructorCohorts, type CohortStudentDetail } from "@/lib/api";

export function InstructorAssignmentsPageContent() {
  const [cohorts, setCohorts] = useState<CohortStudentDetail[]>([]);
  const [cohortId, setCohortId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadCohorts() {
      setLoading(true);
      setError(null);
      try {
        const rows = await listInstructorCohorts();
        if (cancelled) return;
        setCohorts(rows);
        setCohortId((current) =>
          current && rows.some((cohort) => cohort.id === current) ? current : rows[0]?.id ?? "",
        );
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Could not load your assigned cohorts. Please refresh and try again.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadCohorts();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <PageHeader
        title="Assignments"
        description="Create assignments, track student submissions, and review student work across your assigned cohorts."
      />

      {loading ? (
        <p className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Loading your cohorts…
        </p>
      ) : error ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="Could not load assignments"
          description={error}
        />
      ) : cohorts.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No assigned cohorts"
          description="Ask an admin to assign you as an instructor or teaching assistant to a cohort before managing its assignments."
        />
      ) : (
        <>
          <div className="mb-6">
            <label htmlFor="instructor-assignment-cohort" className="mb-1 block text-sm font-medium">
              Cohort
            </label>
            <select
              id="instructor-assignment-cohort"
              className="h-9 min-w-64 rounded-lg border border-input bg-transparent px-2.5 text-sm"
              value={cohortId}
              onChange={(event) => setCohortId(event.target.value)}
            >
              {cohorts.map((cohort) => (
                <option key={cohort.id} value={cohort.id}>
                  {cohort.name}
                </option>
              ))}
            </select>
          </div>
          {cohortId ? <InstructorAssignmentsPanel key={cohortId} cohortId={cohortId} /> : null}
        </>
      )}
    </div>
  );
}
