"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarPlus, CloudDownload, Loader2, Pencil, Trash2, XCircle } from "lucide-react";
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
import {
  ApiError,
  cancelAdminClassroomSession,
  createAdminClassroomSession,
  deleteAdminClassroomSession,
  getAdminClassroomCohorts,
  getAdminClassroomSessions,
  backfillAdminClassroomRecording,
  importAdminClassroomRecording,
  previewAdminRecordingImport,
  syncAdminClassroomRecording,
  syncAdminClassroomRecordings,
  updateAdminClassroomSession,
  type AdminCohortOption,
  type AdminLiveSessionInput,
  type AdminLiveSessionRow,
  type RecordingImportPreview,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const WAT = "Africa/Lagos";

/** Class times are always West Africa Time, never the computer's timezone. */
function toWatInput(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: WAT,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const get = (type: string) => parts.find((part) => part.type === type)?.value ?? "";
  return `${get("year")}-${get("month")}-${get("day")}T${get("hour")}:${get("minute")}`;
}

function fromWatInput(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(value);
  if (!match) return new Date(value).toISOString();
  const [, year, month, day, hour, minute] = match;
  // Africa/Lagos is UTC+1 all year.
  return new Date(
    Date.UTC(Number(year), Number(month) - 1, Number(day), Number(hour) - 1, Number(minute))
  ).toISOString();
}

function formatWatDate(iso: string) {
  try {
    const formatted = new Intl.DateTimeFormat("en-GB", {
      timeZone: WAT,
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).format(new Date(iso));
    return `${formatted} WAT`;
  } catch {
    return iso;
  }
}

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

function defaultForm(cohortId: string): FormState {
  const watNow = new Date(Date.now() + 60 * 60 * 1000);
  watNow.setUTCDate(watNow.getUTCDate() + 14);
  const pad = (n: number) => String(n).padStart(2, "0");
  const day = `${watNow.getUTCFullYear()}-${pad(watNow.getUTCMonth() + 1)}-${pad(watNow.getUTCDate())}`;
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
    starts_at: `${day}T18:00`,
    ends_at: `${day}T20:00`,
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
  const [importRecordingId, setImportRecordingId] = useState("");
  const [importPreview, setImportPreview] = useState<RecordingImportPreview | null>(null);
  const [importDownloadUrl, setImportDownloadUrl] = useState("");
  const [importReason, setImportReason] = useState("");
  const [replaceExistingRecording, setReplaceExistingRecording] = useState(false);
  const [importBusy, setImportBusy] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);

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

  function resetImport() {
    setImportRecordingId("");
    setImportPreview(null);
    setImportDownloadUrl("");
    setImportReason("");
    setReplaceExistingRecording(false);
    setImportMessage(null);
  }

  function openCreate() {
    setEditing(null);
    setForm(defaultForm(cohortFilter || cohorts[0]?.id || ""));
    setFormError(null);
    resetImport();
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
      starts_at: toWatInput(row.starts_at),
      ends_at: toWatInput(row.ends_at),
    });
    setFormError(null);
    resetImport();
    setDialogOpen(true);
  }

  const importVerified =
    Boolean(editing) &&
    importPreview !== null &&
    !importPreview.ambiguous &&
    importPreview.candidates.length === 1 &&
    importPreview.candidates[0]?.session_id === editing?.id;
  const importManual = Boolean(importDownloadUrl.trim() && importReason.trim());
  const canImport = Boolean(importRecordingId.trim()) && (importVerified || importManual);

  async function handlePreviewImport() {
    if (!importRecordingId.trim()) {
      setImportMessage("Enter a RealtimeKit recording ID.");
      return;
    }
    setImportBusy(true);
    setImportMessage(null);
    setImportPreview(null);
    try {
      setImportPreview(await previewAdminRecordingImport(importRecordingId.trim()));
    } catch (err) {
      setImportMessage(err instanceof ApiError ? err.detail : "Could not preview this recording.");
    } finally {
      setImportBusy(false);
    }
  }

  async function handleImportRecording() {
    if (!editing || !canImport) return;
    setImportBusy(true);
    setImportMessage(null);
    try {
      const updated = await importAdminClassroomRecording(editing.id, {
        recording_id: importRecordingId.trim(),
        download_url: importDownloadUrl.trim() || null,
        reason: importReason.trim() || null,
        replace_existing: replaceExistingRecording,
      });
      setSessions((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
      setEditing(updated);
      setImportMessage("Recording imported. Students can watch it once Cloudflare Stream finishes.");
    } catch (err) {
      setImportMessage(err instanceof ApiError ? err.detail : "Could not import this recording.");
    } finally {
      setImportBusy(false);
    }
  }

  async function handleArchiveRecording() {
    if (!importRecordingId.trim()) {
      setImportMessage("Enter a RealtimeKit recording ID.");
      return;
    }
    setImportBusy(true);
    setImportMessage(null);
    try {
      const result = await backfillAdminClassroomRecording(
        importRecordingId.trim(),
        editing?.id
      );
      setImportMessage(result.detail);
    } catch (err) {
      setImportMessage(err instanceof ApiError ? err.detail : "Could not archive this recording.");
    } finally {
      setImportBusy(false);
    }
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
      timezone: WAT,
      starts_at: fromWatInput(form.starts_at),
      ends_at: fromWatInput(form.ends_at),
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
                    {formatWatDate(row.starts_at)}
                  </TableCell>
                  <TableCell>
                    <Badge className={phaseClass(row.phase)}>{row.phase}</Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    <div className="flex items-center gap-2">
                      {row.recording_url || row.recording_status === "ready" ? (
                        <Badge className="bg-success/15 text-success">Ready</Badge>
                      ) : row.recording_status === "processing" ? (
                        <Badge variant="outline">Processing</Badge>
                      ) : row.recording_status === "failed" ? (
                        <Badge className="bg-destructive/15 text-destructive">Failed</Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={busyId === row.id}
                        onClick={() => handleSyncRecording(row)}
                        title="Persist recording from RealtimeKit"
                      >
                        {busyId === row.id ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : (
                          <CloudDownload className="size-4" />
                        )}
                        <span className="ml-1 text-xs">Sync</span>
                      </Button>
                    </div>
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
            {editing && (
              <div className="grid gap-3 rounded-lg border p-3">
                <div className="grid gap-1.5">
                  <Label htmlFor="s-rtk-recording">Existing RealtimeKit recording ID</Label>
                  <Input
                    id="s-rtk-recording"
                    value={importRecordingId}
                    onChange={(e) => {
                      setImportRecordingId(e.target.value);
                      setImportPreview(null);
                    }}
                    placeholder="fff4d97c-b29d-4a88-8fb6-0d46e13ee11c"
                  />
                </div>
                {editing && (editing.recording_url || editing.recording_status === "ready" || editing.recording_status === "processing") && (
                  <label className="flex items-start gap-2 text-sm text-muted-foreground">
                    <input
                      type="checkbox"
                      className="mt-1"
                      checked={replaceExistingRecording}
                      onChange={(event) => setReplaceExistingRecording(event.target.checked)}
                    />
                    <span>
                      Replace the currently linked recording with this one. Verify the new recording is the correct lesson first. The old provider file will not be deleted, but it will no longer be the class&apos;s primary recording.
                    </span>
                  </label>
                )}
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={importBusy || !importRecordingId.trim()}
                    onClick={handlePreviewImport}
                  >
                    {importBusy ? <Loader2 className="size-4 animate-spin" /> : null}
                    Preview
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    className="bg-brand-navy text-white hover:bg-brand-navy/90"
                    disabled={
                      importBusy ||
                      !canImport ||
                      ((Boolean(editing?.recording_url) ||
                        editing?.recording_status === "ready" ||
                        editing?.recording_status === "processing") &&
                        !replaceExistingRecording &&
                        importPreview?.already_linked_session_id !== editing?.id)
                    }
                    onClick={handleImportRecording}
                  >
                    Import onto this session
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={importBusy || !importRecordingId.trim()}
                    onClick={handleArchiveRecording}
                  >
                    Archive to R2
                  </Button>
                </div>
                {importPreview && (
                  <div className="space-y-1 text-sm text-muted-foreground">
                    <p>
                      {importPreview.title || "Untitled"} · {importPreview.status || "unknown status"}
                      {importPreview.meeting_id ? ` · meeting ${importPreview.meeting_id}` : ""}
                    </p>
                    <p>
                      {importPreview.candidates.length === 0
                        ? "No verified session match."
                        : importPreview.candidates
                            .map((candidate) => `${candidate.title} (${candidate.match})`)
                            .join(", ")}
                    </p>
                    {importPreview.note && <p>{importPreview.note}</p>}
                    {importVerified && (
                      <p className="text-success">This session is the single verified match.</p>
                    )}
                  </div>
                )}
                <div className="grid gap-1.5">
                  <Label htmlFor="s-import-url">Manual download URL</Label>
                  <Input
                    id="s-import-url"
                    value={importDownloadUrl}
                    onChange={(e) => setImportDownloadUrl(e.target.value)}
                    placeholder="Only if RealtimeKit metadata is missing or ambiguous"
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="s-import-reason">Recovery reason</Label>
                  <Input
                    id="s-import-reason"
                    value={importReason}
                    onChange={(e) => setImportReason(e.target.value)}
                    placeholder="Required with a manual download URL"
                  />
                </div>
                {importMessage && <p className="text-sm text-muted-foreground">{importMessage}</p>}
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="s-start">Starts (West Africa Time)</Label>
                <Input
                  id="s-start"
                  type="datetime-local"
                  value={form.starts_at}
                  onChange={(e) => setForm({ ...form, starts_at: e.target.value })}
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="s-end">Ends (West Africa Time)</Label>
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