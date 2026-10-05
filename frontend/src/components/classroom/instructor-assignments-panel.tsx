"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiError,
  getAssignmentTracking,
  listInstructorAssignments,
  reviewSubmission,
  type AssignmentPublic,
  type AssignmentTracking,
} from "@/lib/api";

export function InstructorAssignmentsPanel({ cohortId }: { cohortId: string }) {
  const [assignments, setAssignments] = useState<AssignmentPublic[]>([]);
  const [tracking, setTracking] = useState<AssignmentTracking | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scores, setScores] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [savingId, setSavingId] = useState<string | null>(null);

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

  if (loading) {
    return <p className="flex items-center gap-2 py-4 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" /> Loading assignments…</p>;
  }

  if (assignments.length === 0) {
    return <p className="py-4 text-sm text-muted-foreground">No assignments for this cohort yet.</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {assignments.map((assignment) => (
          <Button
            key={assignment.id}
            size="sm"
            variant={selectedId === assignment.id ? "default" : "outline"}
            onClick={() => openTracking(assignment.id)}
          >
            {assignment.title}
          </Button>
        ))}
      </div>

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
    </div>
  );
}

  }
