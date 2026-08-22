"use client";

import { useEffect, useState } from "react";
import { BookOpen, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
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
import { ButtonLink } from "@/components/ui/button-link";

export function AdminCoursesContent() {
  const [rows, setRows] = useState<AdminCourseRow[]>([]);
  const [cohorts, setCohorts] = useState<AdminCohortInstructorRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getAdminCourses(), listAdminCatalogCohorts()])
      .then(([courses, liveCohorts]) => {
        if (!cancelled) {
          setRows(courses);
          setCohorts(liveCohorts);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load courses");
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
        Loading courses…
      </div>
    );
  }

  if (error) {
    return (
        <EmptyState
          icon={<BookOpen className="size-5" />}
          title="Couldn't load courses"
          description={error}
          action={{ label: "Back to courses", href: "/admin/courses" }}
        />
    );
  }

  return (
    <div>
      <PageHeader
        title="Courses"
        description="Assign instructors to catalog courses and live cohorts. Lesson authoring is still seed-based."
      />
      {rows.length === 0 ? (
        <EmptyState
          icon={<BookOpen className="size-5" />}
          title="No courses yet"
          description="Seed the catalog and the free Dune course from the backend scripts."
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Course</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Lessons</TableHead>
                <TableHead>Enrollments</TableHead>
                <TableHead>Completions</TableHead>
                <TableHead>Avg progress</TableHead>
                <TableHead>Instructors</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
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
                  <TableCell>
                    {row.is_free ? "Free" : `${row.price} ${row.currency}`}
                    <div className="text-xs text-muted-foreground">{row.delivery_type}</div>
                  </TableCell>
                  <TableCell>
                    {row.lessons_count} / {row.modules_count} modules
                  </TableCell>
                  <TableCell>{row.enrollments_count}</TableCell>
                  <TableCell>{row.completions_count}</TableCell>
                  <TableCell>{row.avg_progress_percent}%</TableCell>
                  <TableCell>
                    <ButtonLink href={`/admin/courses/${row.slug}/instructors`} variant="outline" size="sm">
                      {row.instructor_count ?? 0} assigned
                    </ButtonLink>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <h2 className="mt-12 font-heading text-xl font-semibold">Live cohorts</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Cohort pages show these instructors. If a cohort has none, it falls back to its linked course.
      </p>
      {cohorts.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">No cohorts seeded yet.</p>
      ) : (
        <div className="mt-4 overflow-x-auto rounded-xl border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cohort</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Instructors</TableHead>
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
                  <TableCell>
                    <ButtonLink href={`/admin/cohorts/${row.slug}/instructors`} variant="outline" size="sm">
                      {row.instructor_count} assigned
                    </ButtonLink>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <p className="mt-4 text-sm text-muted-foreground">
        Full create/edit/publish tools are not live yet. Public course pages render from this data
        model, so a new seeded course appears without a new frontend.
      </p>
      <div className="mt-3">
        <ButtonLink href="/courses" variant="outline" size="sm">
          View public catalog
        </ButtonLink>
      </div>
    </div>
  );
}
