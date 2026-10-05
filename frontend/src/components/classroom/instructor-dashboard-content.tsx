"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, Save } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  getInstructorStudents,
  listClassroomSessions,
  listInstructorCohorts,
  putInstructorAttendance,
  type CohortStudentDetail,
  type InstructorStudentRow,
  type LiveSessionPublic,
} from "@/lib/api";
import { InstructorAssignmentsPanel } from "@/components/classroom/instructor-assignments-panel";
import { InstructorProjectsPanel } from "@/components/classroom/instructor-projects-panel";
import { InstructorReportPanel } from "@/components/classroom/instructor-report-panel";

export function InstructorDashboardContent() {
  const [cohorts, setCohorts] = useState<CohortStudentDetail[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [students, setStudents] = useState<InstructorStudentRow[]>([]);
  const [sessions, setSessions] = useState<LiveSessionPublic[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [statusMap, setStatusMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listInstructorCohorts()
      .then((rows) => {
        if (cancelled) return;
        setCohorts(rows);
        if (rows.length > 0) setSelectedId(rows[0].id);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load cohorts");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    let cancelled = false;
    async function load() {
      setError(null);
      try {
        const [studentRows, sessionRows] = await Promise.all([
          getInstructorStudents(selectedId),
          listClassroomSessions().catch(() => [] as LiveSessionPublic[]),
        ]);
        if (cancelled) return;
        setStudents(studentRows);
        const cohortSessions = sessionRows.filter((s) => s.cohort_id === selectedId);
        setSessions(cohortSessions);
        setSessionId((prev) => prev || cohortSessions[0]?.id || "");
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load students");
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const cohort = useMemo(() => cohorts.find((c) => c.id === selectedId), [cohorts, selectedId]);

  function setStatus(userId: string, status: string) {
    setStatusMap((prev) => ({ ...prev, [userId]: status }));
  }

  async function saveAttendance() {
    if (!selectedId || !sessionId) return;
    setSaving(true);
    setMessage(null);
    setError(null);
    const items = students
      .filter((student) => statusMap[student.user_id])
      .map((student) => ({
        user_id: student.user_id,
        session_id: sessionId,
        status: statusMap[student.user_id],
      }));
    try {
      await putInstructorAttendance(selectedId, items);
      setMessage("Attendance saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save attendance");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading instructor dashboard…
      </div>
    );
  }

  if (cohorts.length === 0) {
    return (
      <EmptyState
        icon={<Loader2 className="size-5" />}
        title="No assigned cohorts"
        description="Ask an admin to assign you to a cohort as instructor."
      />
    );

  return (
    <div>
      <PageHeader title="Instructor dashboard" description="Cohorts, students and attendance." />

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <select
          className="h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm"
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          aria-label="Select cohort"
        >
          {cohorts.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        {cohort ? <Badge className="capitalize">{cohort!.status}</Badge> : null}
      </div>

      {error && (
        <p className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}
      {message && (
        <p className="mb-4 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
          {message}
        </p>
      )}

      {cohort && sessions.length > 0 && (
        <Card className="mb-6 shadow-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Record attendance</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap items-end gap-3">
            <div className="min-w-48">
              <p className="mb-1 text-xs text-muted-foreground">Session</p>
              <select
                className="h-9 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
              >
                {sessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.week_label || "Session"} · {s.title}
                  </option>
                ))}
              </select>
            </div>
            <Button size="sm" onClick={saveAttendance} disabled={saving || !sessionId}>
              <Save className="size-4" />
              {saving ? "Saving…" : "Save attendance"}
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="rounded-xl border shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Student</TableHead>
              <TableHead>Enrollment</TableHead>
              <TableHead>Attendance</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Mark</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {students.map((student) => (
              <TableRow key={student.user_id}>
                <TableCell>
                  <p className="font-medium">{student.full_name || "-"}</p>
                  <p className="text-xs text-muted-foreground">{student.email}</p>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="capitalize">
                    {student.enrollment_status}
                  </Badge>
                </TableCell>
                <TableCell>
                  {student.attendance_attended}/{student.attendance_total}
                </TableCell>
                <TableCell>{student.progress_percent}%</TableCell>
                <TableCell>
                  <select
                    className="h-8 rounded-md border border-input bg-transparent px-2 text-sm"
                    value={statusMap[student.user_id] || ""}
                    onChange={(e) => setStatus(student.user_id, e.target.value)}
                  >
                    <option value="">—</option>
                    <option value="attended">Attended</option>
                    <option value="late">Late</option>
                    <option value="absent">Absent</option>
                  </select>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <section className="mt-8">
        <h2 className="mb-4 font-heading text-lg font-semibold">Assignments</h2>
        <InstructorAssignmentsPanel cohortId={selectedId} />
      </section>

      <section className="mt-8">
        <h2 className="mb-4 font-heading text-lg font-semibold">Projects</h2>
        <InstructorProjectsPanel cohortId={selectedId} />
      </section>

      <section className="mt-8">
        <h2 className="mb-4 font-heading text-lg font-semibold">Cohort report</h2>
        <InstructorReportPanel cohortId={selectedId} />
      </section>
    </div>
  );
}

  }
