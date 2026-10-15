"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, ChevronDown, ChevronUp, Clock3, ExternalLink, FileText, Loader2, Pencil, Plus, Search, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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
  ApiError,
  createInstructorAssignment,
  getAssignmentTracking,
  listInstructorAssignments,
  reviewSubmission,
  updateInstructorAssignment,
  type AssignmentPublic,
  type AssignmentTracking,
  type AssignmentUpsertPayload,
} from "@/lib/api";

const field = "h-9 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm";

type SubmissionFilter = "all" | "submitted" | "missing" | "reviewed";

function isSubmittedStatus(status: string): boolean {
  return status !== "draft" && status !== "missing";
}

function submissionStatusLabel(status: string): string {
  return status === "missing" ? "Not submitted" : status.replaceAll("_", " ");
}

function submissionStatusClass(status: string): string {
  if (status === "reviewed") return "border-emerald-200 bg-emerald-50 text-emerald-800";
  if (status === "missing") return "border-rose-200 bg-rose-50 text-rose-800";
  if (status === "draft") return "border-amber-200 bg-amber-50 text-amber-800";
  if (status === "under_review") return "border-sky-200 bg-sky-50 text-sky-800";
  if (status === "returned" || status === "late") return "border-orange-200 bg-orange-50 text-orange-800";
  return "border-blue-200 bg-blue-50 text-blue-800";
}

function formatSubmissionDate(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function toLocalInput(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
}

type FormState = {
  title: string;
  week_label: string;
  due_date: string;
  description: string;
  instructions: string;
  max_score: string;
  status: string;
};

const EMPTY_FORM: FormState = {
  title: "",
  week_label: "",
  due_date: "",
  description: "",
  instructions: "",
  max_score: "100",
  status: "draft",
};

export function InstructorAssignmentsPanel({ cohortId }: { cohortId: string }) {
  const [assignments, setAssignments] = useState<AssignmentPublic[]>([]);
  const [tracking, setTracking] = useState<AssignmentTracking | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scores, setScores] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [savingId, setSavingId] = useState<string | null>(null);
  const [submissionFilter, setSubmissionFilter] = useState<SubmissionFilter>("all");
  const [studentSearch, setStudentSearch] = useState("");
  const [expandedStudents, setExpandedStudents] = useState<Record<string, boolean>>({});

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<AssignmentPublic | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [savingForm, setSavingForm] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const visibleSubmissions = (tracking?.submissions ?? []).filter((row) => {
    const status = row.submission.status;
    const matchesFilter =
      submissionFilter === "all" ||
      (submissionFilter === "submitted" && isSubmittedStatus(status)) ||
      (submissionFilter === "missing" && !isSubmittedStatus(status)) ||
      (submissionFilter === "reviewed" && status === "reviewed");
    const query = studentSearch.trim().toLowerCase();
    const matchesSearch =
      !query ||
      (row.full_name ?? "").toLowerCase().includes(query) ||
      row.email.toLowerCase().includes(query);
    return matchesFilter && matchesSearch;
  });

  const filterCounts: Record<SubmissionFilter, number> = {
    all: tracking?.submissions.length ?? 0,
    submitted: (tracking?.submissions ?? []).filter((row) => isSubmittedStatus(row.submission.status)).length,
    missing: (tracking?.submissions ?? []).filter((row) => !isSubmittedStatus(row.submission.status)).length,
    reviewed: (tracking?.submissions ?? []).filter((row) => row.submission.status === "reviewed").length,
  };

  function reload() {
    setError(null);
    listInstructorAssignments(cohortId)
      .then(setAssignments)
      .catch((err) =>
        setError(err instanceof ApiError ? err.detail : "Failed to load assignments"),
      );
  }

  useEffect(() => {
    let cancelled = false;

    async function loadAssignmentsAndSubmissions() {
      try {
        const rows = await listInstructorAssignments(cohortId);
        if (cancelled) return;
        setAssignments(rows);

        // Open the first assignment automatically so this page lands on
        // the submission/review view instead of looking like a create-only page.
        const firstAssignment = rows[0];
        if (firstAssignment) {
          setSelectedId(firstAssignment.id);
          const data = await getAssignmentTracking(firstAssignment.id);
          if (!cancelled) setTracking(data);
        } else {
          setTracking(null);
          setSelectedId(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load assignments and submissions");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadAssignmentsAndSubmissions();
    return () => {
      cancelled = true;
    };
  }, [cohortId]);

  async function openTracking(assignmentId: string) {
    setSelectedId(assignmentId);
    setError(null);
    try {
      const data = await getAssignmentTracking(assignmentId);
      setTracking(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load tracking");
    }
  }

  async function saveReview(submissionId: string) {
    setSavingId(submissionId);
    setError(null);
    try {
      await reviewSubmission(submissionId, {
        score: scores[submissionId] ? Number(scores[submissionId]) : null,
        feedback: feedback[submissionId] || null,
        status: "reviewed",
      });
      if (selectedId) await openTracking(selectedId);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save review");
    } finally {
      setSavingId(null);
    }
  }

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(assignment: AssignmentPublic) {
    setEditing(assignment);
    setForm({
      title: assignment.title,
      week_label: assignment.week_label,
      due_date: toLocalInput(assignment.due_date),
      description: assignment.description,
      instructions: assignment.instructions ?? "",
      max_score: String(assignment.max_score),
      status: assignment.status,
    });
    setFormError(null);
    setFormOpen(true);
  }

  async function submitForm() {
    setSavingForm(true);
    setFormError(null);
    try {
      const payload: AssignmentUpsertPayload = {
        cohort_id: cohortId,
        title: form.title.trim(),
        week_label: form.week_label.trim(),
        due_date: form.due_date ? new Date(form.due_date).toISOString() : null,
        description: form.description,
        instructions: form.instructions.trim() || null,
        max_score: Number(form.max_score) || 100,
        status: form.status,
      };
      if (!payload.title) throw new Error("Title is required.");
      if (editing) {
        await updateInstructorAssignment(editing.id, payload);
      } else {
        await createInstructorAssignment(payload);
      }
      setFormOpen(false);
      reload();
    } catch (err) {
      setFormError(
        err instanceof ApiError ? err.detail : err instanceof Error ? err.message : "Could not save assignment",
      );
    } finally {
      setSavingForm(false);
    }
  }

  if (loading) {
    return <p className="flex items-center gap-2 py-4 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" /> Loading assignments…</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          {assignments.length === 0
            ? "No assignments for this cohort yet."
            : `${assignments.length} assignment${assignments.length === 1 ? "" : "s"}`}
        </p>
        <Button size="sm" onClick={openCreate}>
          <Plus className="size-4" /> Create assignment
        </Button>
      </div>

      {assignments.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {assignments.map((assignment) => (
            <div key={assignment.id} className="flex items-center gap-1">
              <Button
                size="sm"
                variant={selectedId === assignment.id ? "default" : "outline"}
                onClick={() => openTracking(assignment.id)}
              >
                {assignment.title}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                title="Edit assignment"
                onClick={() => openEdit(assignment)}
              >
                <Pencil className="size-3.5" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      {tracking && (
        <div>
          <div className="mb-4 grid gap-3 sm:grid-cols-4">
            <Card className="shadow-card"><CardContent className="pt-4"><p className="text-2xl font-semibold">{tracking!.student_count}</p><p className="text-xs text-muted-foreground">Students</p></CardContent></Card>
            <Card className="shadow-card"><CardContent className="pt-4"><p className="text-2xl font-semibold">{tracking!.submitted_count}</p><p className="text-xs text-muted-foreground">Submitted</p></CardContent></Card>
            <Card className="shadow-card"><CardContent className="pt-4"><p className="text-2xl font-semibold">{tracking!.missing_count}</p><p className="text-xs text-muted-foreground">Missing</p></CardContent></Card>
            <Card className="shadow-card"><CardContent className="pt-4"><p className="text-2xl font-semibold">{tracking!.reviewed_count}</p><p className="text-xs text-muted-foreground">Reviewed</p></CardContent></Card>
          </div>

          <section className="space-y-4">
            <div className="flex flex-col gap-3 rounded-xl border bg-muted/20 p-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="relative w-full sm:max-w-xs">
                <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={studentSearch}
                  onChange={(event) => setStudentSearch(event.target.value)}
                  placeholder="Search students by name or email"
                  aria-label="Search students by name or email"
                  className="pl-9"
                />
              </div>
              <div className="flex flex-wrap gap-2" aria-label="Filter students by submission status">
                {([
                  ["all", "All students"],
                  ["submitted", "Submitted"],
                  ["missing", "Not submitted"],
                  ["reviewed", "Reviewed"],
                ] as const).map(([value, label]) => (
                  <Button
                    key={value}
                    type="button"
                    size="sm"
                    variant={submissionFilter === value ? "default" : "outline"}
                    onClick={() => setSubmissionFilter(value)}
                    aria-pressed={submissionFilter === value}
                    className={submissionFilter === value ? "bg-brand-orange text-white hover:bg-brand-orange/90" : ""}
                  >
                    {label}
                    <span className="ml-1.5 rounded-full bg-background/20 px-1.5 py-0.5 text-xs">
                      {filterCounts[value]}
                    </span>
                  </Button>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium">
                {visibleSubmissions.length} student{visibleSubmissions.length === 1 ? "" : "s"}
                <span className="font-normal text-muted-foreground">
                  {submissionFilter === "all" ? " in this assignment" : ` · ${submissionFilter === "missing" ? "not submitted" : submissionFilter}`}
                </span>
              </p>
              {visibleSubmissions.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const allExpanded = visibleSubmissions.every((row) => expandedStudents[row.user_id]);
                    setExpandedStudents((previous) => {
                      const next = { ...previous };
                      visibleSubmissions.forEach((row) => { next[row.user_id] = !allExpanded; });
                      return next;
                    });
                  }}
                >
                  {visibleSubmissions.every((row) => expandedStudents[row.user_id]) ? "Collapse all" : "Expand all"}
                </Button>
              )}
            </div>

            {visibleSubmissions.length === 0 ? (
              <div className="rounded-xl border border-dashed px-6 py-10 text-center">
                <Users className="mx-auto mb-3 size-8 text-muted-foreground" />
                <p className="font-medium">No students match this view</p>
                <p className="mt-1 text-sm text-muted-foreground">Try another status filter or search term.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {visibleSubmissions.map((row) => {
                  const status = row.submission.status;
                  const submitted = isSubmittedStatus(status);
                  const expanded = Boolean(expandedStudents[row.user_id]);
                  const submittedDate = formatSubmissionDate(row.submission.submitted_at);
                  const studentName = row.full_name || row.email;
                  const initials = studentName
                    .split(/\s+/)
                    .filter(Boolean)
                    .slice(0, 2)
                    .map((part) => part[0]?.toUpperCase() ?? "")
                    .join("");

                  return (
                    <Card
                      key={row.user_id}
                      className={`overflow-hidden border-l-4 shadow-sm transition-shadow hover:shadow-card ${status === "reviewed" ? "border-l-emerald-500" : status === "missing" ? "border-l-rose-400" : status === "draft" ? "border-l-amber-400" : "border-l-brand-orange"}`}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <div className="flex min-w-0 items-center gap-3">
                            <div className="flex size-11 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold text-foreground">
                              {initials || <Users className="size-4" />}
                            </div>
                            <div className="min-w-0">
                              <p className="truncate font-semibold">{studentName}</p>
                              <p className="truncate text-sm text-muted-foreground">{row.email}</p>
                              <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                                {submitted ? <FileText className="size-3.5" /> : <Clock3 className="size-3.5" />}
                                {status === "missing"
                                  ? "No submission received"
                                  : status === "draft"
                                    ? "Draft saved · not submitted"
                                    : submittedDate
                                      ? `Submitted ${submittedDate}`
                                      : "Submission received"}
                                {row.enrollment_status !== "active" ? ` · ${row.enrollment_status.replaceAll("_", " ")}` : ""}
                              </p>
                            </div>
                          </div>
                          <div className="flex shrink-0 items-center gap-2 self-start sm:self-center">
                            <Badge variant="outline" className={`capitalize ${submissionStatusClass(status)}`}>
                              {status === "reviewed" && <CheckCircle2 className="mr-1 size-3" />}
                              {submissionStatusLabel(status)}
                            </Badge>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => setExpandedStudents((previous) => ({ ...previous, [row.user_id]: !expanded }))}
                              aria-expanded={expanded}
                            >
                              {expanded ? "Hide details" : "View submission"}
                              {expanded ? <ChevronUp className="ml-1.5 size-4" /> : <ChevronDown className="ml-1.5 size-4" />}
                            </Button>
                          </div>
                        </div>
                      </CardHeader>

                      {expanded && (
                        <CardContent className="space-y-4 border-t bg-muted/10 pt-4">
                          {!submitted && (
                            <div className="rounded-lg border border-dashed bg-background p-4 text-sm text-muted-foreground">
                              {status === "draft"
                                ? "This student has saved a draft but has not submitted the assignment yet."
                                : "This student has not submitted this assignment."}
                            </div>
                          )}

                          {(row.submission.github_url || row.submission.live_url || row.submission.build_in_public_url || row.submission.x_post_url || row.submission.linkedin_post_url || row.submission.documentation_url) && (
                            <div className="flex flex-wrap gap-x-4 gap-y-2 rounded-lg border bg-background p-3">
                              {([
                                ["GitHub", row.submission.github_url],
                                ["Live project", row.submission.live_url],
                                ["Build in public", row.submission.build_in_public_url],
                                ["X post", row.submission.x_post_url],
                                ["LinkedIn post", row.submission.linkedin_post_url],
                                ["Documentation", row.submission.documentation_url],
                              ] as const).map(([label, url]) => url ? (
                                <a key={label} href={url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-medium text-brand-orange hover:underline">
                                  {label} <ExternalLink className="size-3.5" />
                                </a>
                              ) : null)}
                            </div>
                          )}

                          {row.submission.text_response && (
                            <div className="rounded-lg border bg-background p-4">
                              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Student response</p>
                              <p className="whitespace-pre-wrap text-sm leading-6">{row.submission.text_response}</p>
                            </div>
                          )}
                          {row.submission.x_post_text && (
                            <div className="rounded-lg border bg-background p-4">
                              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">X post draft</p>
                              <p className="whitespace-pre-wrap text-sm leading-6">{row.submission.x_post_text}</p>
                            </div>
                          )}
                          {row.submission.linkedin_post_text && (
                            <div className="rounded-lg border bg-background p-4">
                              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">LinkedIn post draft</p>
                              <p className="whitespace-pre-wrap text-sm leading-6">{row.submission.linkedin_post_text}</p>
                            </div>
                          )}
                          {row.submission.files.length > 0 && (
                            <div className="rounded-lg border bg-background p-4">
                              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Attached files / resources</p>
                              <pre className="overflow-x-auto whitespace-pre-wrap break-words text-xs">{JSON.stringify(row.submission.files, null, 2)}</pre>
                            </div>
                          )}

                          {submitted ? (
                            <div className="rounded-lg border bg-background p-4">
                              <div className="mb-3">
                                <p className="font-semibold">Instructor review</p>
                                <p className="text-xs text-muted-foreground">Score and feedback are saved to this student&apos;s submission.</p>
                              </div>
                              <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-end">
                                <div>
                                  <p className="mb-1 text-xs text-muted-foreground">Score / {tracking!.max_score}</p>
                                  <Input
                                    className="w-28"
                                    type="number"
                                    min={0}
                                    max={tracking!.max_score}
                                    value={scores[row.submission.id] ?? (row.submission.score != null ? String(row.submission.score) : "")}
                                    onChange={(event) => setScores((previous) => ({ ...previous, [row.submission.id]: event.target.value }))}
                                  />
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className="mb-1 text-xs text-muted-foreground">Feedback</p>
                                  <Textarea
                                    rows={3}
                                    value={feedback[row.submission.id] ?? row.submission.feedback ?? ""}
                                    onChange={(event) => setFeedback((previous) => ({ ...previous, [row.submission.id]: event.target.value }))}
                                    placeholder="Write actionable feedback for this student…"
                                  />
                                </div>
                                <Button
                                  size="sm"
                                  disabled={savingId === row.submission.id}
                                  onClick={() => saveReview(row.submission.id)}
                                  className="shrink-0 bg-brand-orange text-white hover:bg-brand-orange/90"
                                >
                                  {savingId === row.submission.id ? "Saving…" : status === "reviewed" ? "Update review" : "Save review"}
                                </Button>
                              </div>
                              {row.submission.feedback && !feedback[row.submission.id] && (
                                <p className="mt-3 whitespace-pre-wrap rounded-md bg-muted/50 p-3 text-sm text-muted-foreground">
                                  Current feedback: {row.submission.feedback}
                                </p>
                              )}
                            </div>
                          ) : (
                            <p className="text-xs text-muted-foreground">
                              Review controls become available after the student submits the assignment.
                            </p>
                          )}
                        </CardContent>
                      )}
                    </Card>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      )}

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{editing ? "Edit assignment" : "Create assignment"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid gap-1.5">
              <Label htmlFor="a-title">Title</Label>
              <Input
                id="a-title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="e.g. Week 1 — Extraction pipeline"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="a-week">Week label</Label>
                <Input
                  id="a-week"
                  value={form.week_label}
                  onChange={(e) => setForm({ ...form, week_label: e.target.value })}
                  placeholder="Week 1"
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="a-due">Due date</Label>
                <Input
                  id="a-due"
                  type="datetime-local"
                  value={form.due_date}
                  onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                />
              </div>
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="a-desc">Description</Label>
              <Textarea
                id="a-desc"
                rows={2}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="What students need to build or deliver."
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="a-instr">Instructions</Label>
              <Textarea
                id="a-instr"
                rows={3}
                value={form.instructions}
                onChange={(e) => setForm({ ...form, instructions: e.target.value })}
                placeholder="Step-by-step instructions and submission requirements."
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="a-max">Max score</Label>
                <Input
                  id="a-max"
                  type="number"
                  value={form.max_score}
                  onChange={(e) => setForm({ ...form, max_score: e.target.value })}
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="a-status">Status</Label>
                <select
                  id="a-status"
                  className={field}
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                >
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>
            {formError && <p className="text-sm text-destructive">{formError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFormOpen(false)} disabled={savingForm}>
              Cancel
            </Button>
            <Button
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
              onClick={submitForm}
              disabled={savingForm}
            >
              {savingForm ? <Loader2 className="size-4 animate-spin" /> : null}
              {editing ? "Save changes" : "Create assignment"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
