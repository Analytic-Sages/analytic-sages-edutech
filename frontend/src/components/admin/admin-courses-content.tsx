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
import { ApiError, getAdminCourses, type AdminCourseRow } from "@/lib/api";
import { ButtonLink } from "@/components/ui/button-link";

export function AdminCoursesContent() {
  const [rows, setRows] = useState<AdminCourseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAdminCourses()
      .then((data) => {
        if (!cancelled) setRows(data);
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
          action={{ label: "Back to admin", href: "/admin" }}
        />
    );
  }

  return (
    <div>
      <PageHeader
        title="Courses"
        description="Catalog, enrollments, and completion. Lesson authoring is still seed-based."
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
