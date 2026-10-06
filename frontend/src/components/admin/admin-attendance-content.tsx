"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, Save } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { AdminSessionAttendancePanel } from "@/components/admin/admin-session-attendance-panel";
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
  getAdminClassroomCohorts,
  getInstructorStudents,
  listClassroomSessions,
  putInstructorAttendance,
  type AdminCohortOption,
  type InstructorStudentRow,
  type LiveSessionPublic,
} from "@/lib/api";

export function AdminAttendanceContent() {
  const [cohorts, setCohorts] = useState<AdminCohortOption[]>([]);
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
    getAdminClassroomCohorts()
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
      setMessage(null);
      setStatusMap({});
      try {
        const [studentRows, sessionRows] = await Promise.all([
          getInstructorStudents(selectedId),
          listClassroomSessions().catch(() => [] as LiveSessionPublic[]),
        ]);
        if (cancelled) return;
        setStudents(studentRows);
        const cohortSessions = sessionRows.filter((s) => s.cohort_id === selectedId);
        setSessions(cohortSessions);
        setSessionId(cohortSessions[0]?.id || "");
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
  const selectedSession = useMemo(
    () => sessions.find((s) => s.id === sessionId),
    [sessions, sessionId]
  );

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
    if (items.length === 0) {
      setError("Mark at least one student before saving.");
      setSaving(false);
      return;
    }
    try {
      await putInstructorAttendance(selectedId, items);
      setMessage(`Saved attendance for ${items.length} student${items.length === 1 ? "" : "s"}.`);
      const refreshed = await getInstructorStudents(selectedId);
      setStudents(refreshed);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save attendance");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading attendance…
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <PageHeader
          title="Attendance"
          description={cohort ? `Marking ${cohort.name}` : "Mark attendance for a cohort."}
        />
        <select
          className="h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm"
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          aria-label="Select cohort"
        >
          {cohorts.map((option) => (
            <option key={option.id} value={option.id}>
              {option.name}
            </option>
          ))}
        </select>
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

      <p className="mb-4 rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
        Attendance is the official cohort record. It is imported automatically from Cloudflare
        RealtimeKit after each class and can also be marked by staff (or a TA) per session — a staff
        entry always wins over the imported value. This sheet is what appears on the
        student&apos;s classroom and the cohort report.
      </p>

      {sessions.length > 0 && (
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

      {sessionId && (
        <AdminSessionAttendancePanel
          key={sessionId}
          sessionId={sessionId}
          sessionTitle={selectedSession?.title || "Session"}
        />
      )}

      {students.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No students yet"
          description="Students appear once they enrol in this cohort."
        />
      ) : (
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
                      onChange={(e) =>
                        setStatusMap((prev) => ({ ...prev, [student.user_id]: e.target.value }))
                      }
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
      )}
    </div>
  );
}
