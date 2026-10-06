"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarPlus, CloudDownload, ExternalLink, Loader2, Pencil, Trash2, XCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatAdminDate } from "@/components/admin/admin-format";
import {
  ApiError,
  cancelAdminClassroomSession,
  createAdminClassroomSession,
  deleteAdminClassroomSession,
  getAdminClassroomCohorts,
  getAdminClassroomSessions,
  syncAdminClassroomRecording,
  syncAdminClassroomRecordings,
  updateAdminClassroomSession,
  type AdminCohortOption,
  type AdminLiveSessionInput,
  type AdminLiveSessionRow,
} from "@/lib/api";
import { cn } from "@/lib/utils";

type FormState = {
  cohort_id: string;
  title: string;
  week_label: string;
  session_number: number;
  session_type: "teaching" | "office_hour";
  objectives: string;
  assignment_summary: string;
  status: string;
  recording_url: string;
  meeting_url: string;
  starts_at: string;
  ends_at: string;
};

/** ISO timestamp → value for an <input type="datetime-local">. */
function toLocalInput(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
}

/** datetime-local value → ISO string (with timezone). */
function fromLocalInput(value: string): string {
  return new Date(value).toISOString();
}

function defaultForm(cohortId: string): FormState {
  const start = new Date();
  start.setDate(start.getDate() + 14);
  start.setHours(18, 0, 0, 0);
  const end = new Date(start);
  end.setHours(20, 0, 0, 0);
  return {
    cohort_id: cohortId,
    title: "",
    week_label: "",
    session_number: 1,
    session_type: "teaching",
    objectives: "",
    assignment_summary: "",
    status: "scheduled",
    recording_url: "",
    meeting_url: "",
    starts_at: toLocalInput(start.toISOString()),
    ends_at: toLocalInput(end.toISOString()),
  };
}

function phaseClass(phase: string) {
  if (phase === "live") return "bg-red-500/15 text-red-700 dark:text-red-300";
  if (phase === "upcoming") return "bg-brand-orange/15 text-brand-orange";
  if (phase === "cancelled") return "bg-destructive/10 text-destructive";
  return "bg-muted text-muted-foreground";
}

export function AdminClassroomContent() {
  const [cohorts, setCohorts] = useState<AdminCohortOption[]>([]);
  const [sessions, setSessions] = useState<AdminLiveSessionRow[]>([]);
  const [cohortFilter, setCohortFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<AdminLiveSessionRow | null>(null);
  const [form, setForm] = useState<FormState>(defaultForm(""));
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const refreshCohorts = useCallback(async () => {
    try {
      setCohorts(await getAdminClassroomCohorts());
    } catch {
      // Non-fatal: the cohort list only powers the filter dropdown.
    }
  }, []);

  // Load every session once and filter client-side. Re-fetching per cohort opened a
  // race (and swallowed errors) that could leave the table showing a partial list,
  // which read as "the cohort isn't showing the complete sessions".
  const reloadSessions = useCallback(async () => {
    const rows = await getAdminClassroomSessions();
    setSessions(rows);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [cohortOptions, rows] = await Promise.all([
          getAdminClassroomCohorts(),
          getAdminClassroomSessions(),
        ]);
        if (!cancelled) {
          setCohorts(cohortOptions);
          setSessions(rows);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load classroom");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedCohort = cohorts.find((cohort) => cohort.id === cohortFilter) ?? null;

  // Always show the full schedule in teaching order (Week 1 → Week 10).
  const filtered = useMemo(() => {
    const rows = cohortFilter
      ? sessions.filter((s) => s.cohort_id === cohortFilter)
      : sessions;
    return [...rows].sort(
      (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime()
    );
  }, [sessions, cohortFilter]);

  function openCreate() {
    setEditing(null);
    setForm(defaultForm(cohortFilter || cohorts[0]?.id || ""));
    setFormError(null);
    setDialogOpen(true);
  }

  function openEdit(row: AdminLiveSessionRow) {
    setEditing(row);
    setForm({
      cohort_id: row.cohort_id,
      title: row.title,
      week_label: row.week_label,
      session_number: row.session_number,
      session_type: row.session_type,
      objectives: row.objectives.join("\n"),
      assignment_summary: row.assignment_summary ?? "",
      status: row.status,
      recording_url: row.recording_url ?? "",
      meeting_url: row.meeting_url ?? "",
      starts_at: toLocalInput(row.starts_at),
      ends_at: toLocalInput(row.ends_at),
    });
    setFormError(null);
    setDialogOpen(true);
  }

  async function submit() {
    setFormError(null);
    if (!form.cohort_id) {
      setFormError("Select a cohort");
      return;
    }
    if (!form.title.trim()) {
      setFormError("Session title is required");
      return;
    }
    if (!form.starts_at || !form.ends_at) {
      setFormError("Start and end times are required");
      return;
    }
    const payload: AdminLiveSessionInput = {
      cohort_id: form.cohort_id,
      title: form.title.trim(),
      week_label: form.week_label.trim(),
      session_number: Number(form.session_number) || 1,
      session_type: form.session_type,
      objectives: form.objectives
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean),
      assignment_summary: form.assignment_summary.trim() || null,
      meeting_url: form.meeting_url.trim() || null,
      starts_at: fromLocalInput(form.starts_at),
      ends_at: fromLocalInput(form.ends_at),
    };
    if (editing) {
      payload.status = form.status;
      payload.recording_url = form.recording_url.trim() || null;
    }
    setSaving(true);
    try {
      if (editing) {
        await updateAdminClassroomSession(editing.id, payload);
      } else {
        await createAdminClassroomSession(payload);
      }
      setDialogOpen(false);
      await reloadSessions();
      await refreshCohorts();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.detail : "Could not save the session");
    } finally {
      setSaving(false);
    }
  }

  async function handleCancel(row: AdminLiveSessionRow) {
    setBusyId(row.id);
    setError(null);
    try {
      await cancelAdminClassroomSession(row.id);
      await reloadSessions();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not cancel the session");
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(row: AdminLiveSessionRow) {
    if (!window.confirm(`Delete "${row.title}"? This cannot be undone.`)) return;
    setBusyId(row.id);
    setError(null);
    try {
      await deleteAdminClassroomSession(row.id);
      await reloadSessions();
      await refreshCohorts();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not delete the session");
    } finally {
      setBusyId(null);
    }
  }

  async function handleSyncRecording(row: AdminLiveSessionRow) {
    setBusyId(row.id);
    setError(null);
    try {
      const updated = await syncAdminClassroomRecording(row.id);
      if (updated.recording_url) {
        setSessions((prev) =>
          prev.map((s) => (s.id === row.id ? { ...s, recording_url: updated.recording_url } : s))
        );
      } else {
        setError(
          "No recording is available yet. RealtimeKit keeps recordings after they finish uploading — try again in a few minutes.",
        );
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not sync the recording");
    } finally {
      setBusyId(null);
    }
  }

  async function handleSyncAll() {
    setSyncing(true);
    setError(null);
    try {
      const result = await syncAdminClassroomRecordings(cohortFilter || undefined);
      await reloadSessions();
      setError(
        `Recording sync complete — ${result.updated} new recording${
          result.updated === 1 ? "" : "s"
        } linked (${result.skipped} without a recording yet).`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not sync recordings");
    } finally {
      setSyncing(false);
    }
  }

  const field = "h-9 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm";

  return (
    <div>
      <PageHeader
        title="Live sessions"
        description="Create and manage classroom sessions. Students see them immediately after saving."
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label className="text-sm text-muted-foreground" htmlFor="cohort-filter">
          Cohort
        </label>
        <select
          id="cohort-filter"
          className={cn(field, "w-64")}
          value={cohortFilter}
          onChange={(e) => setCohortFilter(e.target.value)}
        >
          <option value="">All cohorts ({sessions.length} sessions)</option>
          {cohorts.map((cohort) => (
            <option key={cohort.id} value={cohort.id}>
              {cohort.name} ({cohort.sessions_count})
            </option>
          ))}
        </select>
        <Button
          className="bg-brand-orange text-white hover:bg-brand-orange/90"
          onClick={openCreate}
          disabled={cohorts.length === 0}
        >
          <CalendarPlus className="size-4" />
          Create session
        </Button>
        <Button variant="outline" onClick={handleSyncAll} disabled={syncing}>
          {syncing ? <Loader2 className="size-4 animate-spin" /> : <CloudDownload className="size-4" />}
          {syncing ? "Syncing…" : "Sync recordings"}
        </Button>
        <span className="text-xs text-muted-foreground">
          Showing {filtered.length}{" "}
          {selectedCohort ? `of ${selectedCohort.sessions_count} sessions for ${selectedCohort.name}` : "sessions"}
        </span>
      </div>

      {error && (
        <p className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center gap-2 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Loading sessions…
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<CalendarPlus className="size-6" />}
          title="No sessions yet"
          description="Create the first live session for this cohort."
        />
      ) : (
        <div className="rounded-xl border shadow-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Session</TableHead>
                <TableHead>Cohort</TableHead>
                <TableHead>When</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Recording</TableHead>
                <TableHead>Seats</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>
                    <p className="font-medium">{row.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {row.week_label ? `${row.week_label} · ` : ""}
                      {row.session_type === "office_hour"
                        ? "Office hour"
                        : `Session ${row.session_number}`}
                    </p>
                  </TableCell>
                  <TableCell className="text-sm">{row.cohort_name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatAdminDate(row.starts_at)}
                  </TableCell>
                  <TableCell>
                    <Badge className={phaseClass(row.phase)}>{row.phase}</Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    {row.recording_url ? (
                      <div className="flex items-center gap-2">
                        <a
                          href={row.recording_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-brand-orange hover:underline"
                        >
                          Recording <ExternalLink className="size-3" />
                        </a>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={busyId === row.id}
                          onClick={() => handleSyncRecording(row)}
                          title="Re-check recording"
                        >
                          <CloudDownload className="size-3.5" />
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={busyId === row.id}
                        onClick={() => handleSyncRecording(row)}
                        title="Pull recording from RealtimeKit"
                      >
                        {busyId === row.id ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : (
                          <CloudDownload className="size-4" />
                        )}
                        <span className="ml-1 text-xs">Sync</span>
                      </Button>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{row.member_count}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(row)}>
                        <Pencil className="size-4" />
                      </Button>
                      {row.status !== "cancelled" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={busyId === row.id}
                          onClick={() => handleCancel(row)}
                          title="Cancel session"
                        >
                          {busyId === row.id ? (
                            <Loader2 className="size-4 animate-spin" />
                          ) : (
                            <XCircle className="size-4" />
                          )}
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={busyId === row.id}
                        onClick={() => handleDelete(row)}
                        title="Delete session"
                      >
                        <Trash2 className="size-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{editing ? "Edit session" : "Create live session"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid gap-1.5">
              <Label htmlFor="s-cohort">Cohort</Label>
              <select
                id="s-cohort"
                className={field}
                value={form.cohort_id}
                onChange={(e) => setForm({ ...form, cohort_id: e.target.value })}
                disabled={Boolean(editing)}
              >
                <option value="">Select a cohort…</option>
                {cohorts.map((cohort) => (
                  <option key={cohort.id} value={cohort.id}>
                    {cohort.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="s-title">Title</Label>
              <Input
                id="s-title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="e.g. Containerized Ingestion Pipelines"
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="s-week">Week label</Label>
                <Input
                  id="s-week"
                  value={form.week_label}
                  onChange={(e) => setForm({ ...form, week_label: e.target.value })}
                  placeholder="Week 1"
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="s-num">Number</Label>
                <Input
                  id="s-num"
                  type="number"
                  min={1}
                  value={form.session_number}
                  onChange={(e) => setForm({ ...form, session_number: Number(e.target.value) })}
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="s-type">Type</Label>
                <select
                  id="s-type"
                  className={field}
                  value={form.session_type}
                  onChange={(e) =>
                    setForm({ ...form, session_type: e.target.value as FormState["session_type"] })
                  }
                >
                  <option value="teaching">Teaching</option>
                  <option value="office_hour">Office hour</option>
                </select>
              </div>
            </div>
            {editing && (
              <div className="grid grid-cols-2 gap-3">
                <div className="grid gap-1.5">
                  <Label htmlFor="s-status">Status</Label>
                  <select
                    id="s-status"
                    className={field}
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value })}
                  >
                    <option value="scheduled">Scheduled</option>
                    <option value="live">Live</option>
                    <option value="ended">Ended</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="s-meeting">Meeting URL</Label>
                  <Input
                    id="s-meeting"
                    value={form.meeting_url}
                    onChange={(e) => setForm({ ...form, meeting_url: e.target.value })}
                    placeholder="https://meet.google.com/…"
                  />
                </div>
              </div>
            )}
            {editing && (
              <div className="grid gap-1.5">
                <Label htmlFor="s-recording">Recording URL</Label>
                <Input
                  id="s-recording"
                  value={form.recording_url}
                  onChange={(e) => setForm({ ...form, recording_url: e.target.value })}
                  placeholder="https://…"
                />
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="s-start">Starts</Label>
                <Input
                  id="s-start"
                  type="datetime-local"
                  value={form.starts_at}
                  onChange={(e) => setForm({ ...form, starts_at: e.target.value })}
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="s-end">Ends</Label>
                <Input
                  id="s-end"
                  type="datetime-local"
                  value={form.ends_at}
                  onChange={(e) => setForm({ ...form, ends_at: e.target.value })}
                />
              </div>
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="s-objectives">Objectives (one per line)</Label>
              <Textarea
                id="s-objectives"
                rows={3}
                value={form.objectives}
                onChange={(e) => setForm({ ...form, objectives: e.target.value })}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="s-assignment">Assignment summary</Label>
              <Textarea
                id="s-assignment"
                rows={2}
                value={form.assignment_summary}
                onChange={(e) => setForm({ ...form, assignment_summary: e.target.value })}
              />
            </div>
            {formError && <p className="text-sm text-destructive">{formError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
              onClick={submit}
              disabled={saving}
            >
              {saving ? <Loader2 className="size-4 animate-spin" /> : null}
              {editing ? "Save changes" : "Create session"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}