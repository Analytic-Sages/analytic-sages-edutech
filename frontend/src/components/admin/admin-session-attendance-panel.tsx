"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Check, Loader2, RefreshCw } from "lucide-react";
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
  getAdminSessionAttendance,
  resolveAdminAttendanceParticipant,
  syncAdminClassroomAttendance,
  type AttendanceParticipantRow,
  type SessionAttendanceDetail,
} from "@/lib/api";

function formatDuration(seconds: number | null | undefined): string {
  if (!seconds || seconds <= 0) return "—";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);
  if (hours > 0) return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
  return `${minutes}m`;
}

function formatTime(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return "—";
  }
}

function statusBadge(row: AttendanceParticipantRow) {
  if (!row.matched) {
    return <Badge className="bg-warning/15 text-warning">Needs review</Badge>;
  }
  switch (row.status) {
    case "attended":
      return <Badge className="bg-success/15 text-success">Present</Badge>;
    case "late":
      return <Badge className="bg-warning/15 text-warning">Late</Badge>;
    case "absent":
      return <Badge className="bg-destructive/15 text-destructive">Absent</Badge>;
    default:
      return <Badge variant="outline">—</Badge>;
  }
}

function syncBadge(status: string) {
  const map: Record<string, { label: string; className: string }> = {
    ok: { label: "Synced", className: "bg-success/15 text-success" },
    pending: { label: "In progress", className: "bg-muted text-muted-foreground" },
    needs_review: { label: "Needs review", className: "bg-warning/15 text-warning" },
    error: { label: "Sync error", className: "bg-destructive/15 text-destructive" },
  };
  const entry = map[status] ?? { label: status, className: "" };
  return <Badge className={entry.className}>{entry.label}</Badge>;
}

export function AdminSessionAttendancePanel({
  sessionId,
  sessionTitle,
}: {
  sessionId: string;
  sessionTitle: string;
}) {
  const [detail, setDetail] = useState<SessionAttendanceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [resolving, setResolving] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const data = await getAdminSessionAttendance(sessionId);
    setDetail(data);
    setError(null);
  }, [sessionId]);

  useEffect(() => {
    let cancelled = false;
    getAdminSessionAttendance(sessionId)
      .then((data) => {
        if (cancelled) return;
        setDetail(data);
        setError(null);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load RealtimeKit attendance");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  async function handleSync() {
    setSyncing(true);
    setMessage(null);
    setError(null);
    try {
      const result = await syncAdminClassroomAttendance(sessionId);
      setMessage(
        result.status === "skipped"
          ? result.note || "Nothing to sync for this session."
          : `Synced ${result.participants} participant(s): ${result.matched} matched, ${result.unmatched} need review, ${result.attendance_written} attendance record(s) written.`
      );
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to sync attendance");
    } finally {
      setSyncing(false);
    }
  }

  async function handleResolve(participantId: string, userId: string) {
    if (!userId) return;
    setResolving(participantId);
    setMessage(null);
    setError(null);
    try {
      await resolveAdminAttendanceParticipant(participantId, {
        user_id: userId,
        status: "attended",
        reason: "Matched manually from the admin attendance panel",
      });
      setMessage("Participant matched and attendance recorded as a manual override.");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to match participant");
    } finally {
      setResolving(null);
    }
  }

  return (
    <Card className="mb-6 shadow-card">
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              RealtimeKit attendance
              {detail && syncBadge(detail.sync_status)}
            </CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">
              Imported from Cloudflare RealtimeKit for <strong>{sessionTitle}</strong>.
              {detail?.last_synced_at ? ` Last synced ${formatTime(detail.last_synced_at)}.` : ""}
            </p>
          </div>
          <Button size="sm" onClick={handleSync} disabled={syncing}>
            {syncing ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            {syncing ? "Syncing…" : "Sync attendance"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {message && (
          <p className="mb-3 flex items-center gap-2 rounded-md border border-success/30 bg-success/10 p-2 text-xs text-success">
            <Check className="size-3.5" /> {message}
          </p>
        )}
        {error && <p className="mb-3 text-sm text-destructive">{error}</p>}

        {loading ? (
          <p className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> Loading attendance…
          </p>
        ) : detail ? (
          <>
            <div className="mb-4 flex flex-wrap gap-2 text-xs">
              <Badge variant="outline">{detail.expected_students.length} enrolled</Badge>
              <Badge variant="outline">{detail.matched_count} matched</Badge>
              <Badge variant="outline">{detail.unmatched_count} unmatched</Badge>
            </div>

            {detail.participants.length === 0 ? (
              <p className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
                <AlertTriangle className="size-4" /> No participant data yet. Run a sync after the
                class has finished.
              </p>
            ) : (
              <div className="overflow-x-auto rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Participant</TableHead>
                      <TableHead>Student</TableHead>
                      <TableHead>First join</TableHead>
                      <TableHead>Last leave</TableHead>
                      <TableHead>Attended</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Match</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {detail.participants.map((row) => (
                      <TableRow key={row.id}>
                        <TableCell>
                          <p className="font-medium">{row.display_name || "Unknown"}</p>
                          <p className="text-xs text-muted-foreground">
                            {row.intervals.length > 1
                              ? `${row.intervals.length} intervals`
                              : row.custom_participant_id
                                ? "identified"
                                : "no identity"}
                          </p>
                        </TableCell>
                        <TableCell>
                          {row.matched ? (
                            <div>
                              <p className="font-medium">{row.user_name || "—"}</p>
                              <p className="text-xs text-muted-foreground">{row.user_email}</p>
                            </div>
                          ) : (
                            <span className="text-xs text-muted-foreground">Unmatched</span>
                          )}
                        </TableCell>
                        <TableCell className="text-sm">{formatTime(row.first_joined_at)}</TableCell>
                        <TableCell className="text-sm">{formatTime(row.last_left_at)}</TableCell>
                        <TableCell className="text-sm">
                          {formatDuration(row.total_attendance_seconds)}
                        </TableCell>
                        <TableCell>{statusBadge(row)}</TableCell>
                        <TableCell>
                          {row.matched ? (
                            <Badge variant="outline">Auto</Badge>
                          ) : (
                            <div className="flex items-center gap-2">
                              <select
                                className="h-8 rounded-md border border-input bg-transparent px-2 text-xs"
                                defaultValue=""
                                disabled={resolving === row.id}
                                onChange={(e) => handleResolve(row.id, e.target.value)}
                                aria-label="Match participant to student"
                              >
                                <option value="">Match to…</option>
                                {detail.expected_students.map((student) => (
                                  <option key={student.user_id} value={student.user_id}>
                                    {student.full_name || student.email}
                                  </option>
                                ))}
                              </select>
                              {resolving === row.id && (
                                <Loader2 className="size-3.5 animate-spin text-muted-foreground" />
                              )}
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}