"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Loader2, Pencil, Plus } from "lucide-react";
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

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<AssignmentPublic | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [savingForm, setSavingForm] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

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
    listInstructorAssignments(cohortId)
      .then((rows) => {
        if (!cancelled) setAssignments(rows);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load assignments");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
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

          <div className="space-y-3">
            {tracking!.submissions.map((row) => (
              <Card key={row.user_id} className="shadow-card">
                <CardHeader className="pb-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="font-medium">{row.full_name || row.email}</p>
                      <p className="text-xs text-muted-foreground">{row.email}</p>
                    </div>
                    <Badge className="capitalize">{row.submission.status.replace("_", " ")}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {row.submission.github_url && (
                    <a href={row.submission.github_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
                      GitHub <ExternalLink className="size-3" />
                    </a>
                  )}
                  {row.submission.live_url && (
                    <a href={row.submission.live_url} target="_blank" rel="noreferrer" className="ml-3 inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
                      Live <ExternalLink className="size-3" />
                    </a>
                  )}
                  {row.submission.build_in_public_url && (
                    <a href={row.submission.build_in_public_url} target="_blank" rel="noreferrer" className="ml-3 inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
                      Build in public <ExternalLink className="size-3" />
                    </a>
                  )}
                  {row.submission.text_response && (
                    <p className="whitespace-pre-wrap text-sm text-muted-foreground">{row.submission.text_response}</p>
                  )}

                  <div className="flex flex-wrap items-end gap-2">
                    <div>
                      <p className="mb-1 text-xs text-muted-foreground">Score / {tracking!.max_score}</p>
                      <Input
                        className="w-24"
                        type="number"
                        value={scores[row.submission.id] ?? (row.submission.score != null ? String(row.submission.score) : "")}
                        onChange={(e) => setScores((prev) => ({ ...prev, [row.submission.id]: e.target.value }))}
                      />
                    </div>
                    <div className="min-w-64 flex-1">
                      <p className="mb-1 text-xs text-muted-foreground">Feedback</p>
                      <Textarea
                        rows={2}
                        value={feedback[row.submission.id] ?? row.submission.feedback ?? ""}
                        onChange={(e) => setFeedback((prev) => ({ ...prev, [row.submission.id]: e.target.value }))}
                      />
                    </div>
                    <Button
                      size="sm"
                      disabled={savingId === row.submission.id}
                      onClick={() => saveReview(row.submission.id)}
                    >
                      {savingId === row.submission.id ? "Saving…" : "Save review"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
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
