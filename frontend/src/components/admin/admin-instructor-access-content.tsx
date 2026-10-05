"use client";

import { useEffect, useState } from "react";
import { Loader2, Users } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
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
  getAdminCourses,
  listAdminCatalogCohorts,
  type AdminCohortInstructorRow,
  type AdminCourseRow,
} from "@/lib/api";

export function AdminInstructorAccessContent() {
  const [courses, setCourses] = useState<AdminCourseRow[]>([]);
  const [cohorts, setCohorts] = useState<AdminCohortInstructorRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getAdminCourses(), listAdminCatalogCohorts()])
      .then(([courseRows, cohortRows]) => {
        if (!cancelled) {
          setCourses(courseRows);
          setCohorts(cohortRows);
        }
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof ApiError ? err.detail : "Failed to load programmes");
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
        Loading programmes…
      </div>
    );
  }

  if (error) {
    return <EmptyState icon={<Users className="size-6" />} title="Couldn't load" description={error} />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Instructor access"
        description="Grant or revoke which instructors can see and teach each live programme and self-paced course."
      />

      <section>
        <h2 className="mb-3 font-heading text-lg font-semibold">Live programmes</h2>
        {cohorts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No live programmes yet.</p>
        ) : (
          <div className="rounded-xl border shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Programme</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Instructors</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cohorts.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>
                      <div className="font-medium">{row.name}</div>
                      <div className="text-xs text-muted-foreground">{row.slug}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{row.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <ButtonLink
                        href={`/admin/cohorts/${row.slug}/instructors`}
                        variant="outline"
                        size="sm"
                      >
                        {row.instructor_count} assigned
                      </ButtonLink>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 font-heading text-lg font-semibold">Self-paced courses</h2>
        {courses.length === 0 ? (
          <p className="text-sm text-muted-foreground">No self-paced courses yet.</p>
        ) : (
          <div className="rounded-xl border shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Course</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Instructors</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {courses.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>
                      <div className="font-medium">{row.title}</div>
                      <div className="text-xs text-muted-foreground">{row.slug}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={row.published ? "default" : "outline"}>
                        {row.published ? "Published" : "Draft"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <ButtonLink
                        href={`/admin/courses/${row.slug}/instructors`}
                        variant="outline"
                        size="sm"
                      >
                        {row.instructor_count ?? 0} assigned
                      </ButtonLink>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>
    </div>
  );
}
