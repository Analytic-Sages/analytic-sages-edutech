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

  useEffect(() => {
    getAdminClassroomCohorts()
      .then((rows) => {
        setCohorts(rows);
        if (rows.length > 0) setCohortId(rows[0].id);
      })
      .catch(() => {});
  }, []);

  return (
    <div>
      <PageHeader
        title="Assignments"
        description="Track submissions and review student work across a cohort."
      />

      {cohorts.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No cohorts"
          description="Create a cohort to start tracking assignments."
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
