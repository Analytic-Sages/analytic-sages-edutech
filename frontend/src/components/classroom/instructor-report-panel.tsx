"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiError, getCohortReport, type CohortReport } from "@/lib/api";

export function InstructorReportPanel({ cohortId }: { cohortId: string }) {
  const [report, setReport] = useState<CohortReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getCohortReport(cohortId)
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load report");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [cohortId]);

  if (loading) {
    return <p className="flex items-center gap-2 py-4 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" /> Loading report…</p>;
  }

  if (error) {
    return <p className="py-4 text-sm text-destructive">{error}</p>;
  }

  if (!report) return null;

  return (
    <div>
      <div className="mb-4 grid gap-3 sm:grid-cols-4">
        <Card className="shadow-card"><CardContent className="pt-4"><p className="text-2xl font-semibold">{report.student_count}</p><p className="text-xs text-muted-foreground">Students</p></CardContent></Card>
        <Card className="shadow-card"><CardContent className="pt-4"><p className="text-2xl font-semibold">{report.attendance_rate}%</p><p className="text-xs text-muted-foreground">Attendance</p></CardContent></Card>
        <Card className="shadow-card"><CardContent className="pt-4"><p className="text-2xl font-semibold">{report.assignment_completion_rate}%</p><p className="text-xs text-muted-foreground">Assignments</p></CardContent></Card>
        <Card className="shadow-card"><CardContent className="pt-4"><p className="text-2xl font-semibold">{report.projects_completed}</p><p className="text-xs text-muted-foreground">Projects completed</p></CardContent></Card>
      </div>

      <Card className="shadow-card">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">At-risk students</CardTitle>
            <Badge variant="outline">{report.at_risk_count}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {report.at_risk.length === 0 ? (
            <p className="text-sm text-muted-foreground">No students flagged.</p>
          ) : (
            <ul className="space-y-2">
              {report.at_risk.map((row) => (
                <li key={row.user_id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3 text-sm">
                  <div>
                    <p className="font-medium">{row.full_name || row.email}</p>
                    <p className="text-xs text-muted-foreground">{row.email}</p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <AlertTriangle className="size-3.5 text-warning" />
                    {row.missed_sessions} missed · {row.missing_assignments} missing · {row.incomplete_projects} projects
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card className="mt-6 shadow-card">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Gradebook</CardTitle>
            <Badge variant="outline">{report.gradebook.length} students</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {report.gradebook.length === 0 ? (
            <p className="text-sm text-muted-foreground">No students enrolled yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student</TableHead>
                    <TableHead>Attendance</TableHead>
                    <TableHead>Assignments</TableHead>
                    <TableHead>Avg score</TableHead>
                    <TableHead>Projects done</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {report.gradebook.map((row) => (
                    <TableRow key={row.user_id}>
                      <TableCell>
                        <p className="font-medium">{row.full_name || "-"}</p>
                        <p className="text-xs text-muted-foreground">{row.email}</p>
                      </TableCell>
                      <TableCell>
                        {row.attendance_present}/{row.attendance_total}
                      </TableCell>
                      <TableCell>
                        {row.assignments_submitted}/{row.assignments_total}
                      </TableCell>
                      <TableCell>{row.avg_score != null ? `${row.avg_score}%` : "—"}</TableCell>
                      <TableCell>{row.projects_completed}</TableCell>
                      <TableCell>
                        {row.at_risk ? (
                          <Badge className="bg-destructive/15 text-destructive">At risk</Badge>
                        ) : (
                          <Badge variant="outline">On track</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
