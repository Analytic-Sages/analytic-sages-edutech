"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiError,
  getAssignment,
  putMySubmission,
  type AssignmentDetail,
} from "@/lib/api";

function formatDate(iso: string | null) {
  if (!iso) return "No deadline";
  try {
    return new Intl.DateTimeFormat(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function AssignmentDetailContent({ assignmentId }: { assignmentId: string }) {
  const [assignment, setAssignment] = useState<AssignmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [text, setText] = useState("");
  const [github, setGithub] = useState("");
  const [live, setLive] = useState("");
  const [buildInPublic, setBuildInPublic] = useState("");
  const [docs, setDocs] = useState("");

  useEffect(() => {
    let cancelled = false;
    getAssignment(assignmentId)
      .then((data) => {
        if (cancelled) return;
        setAssignment(data);
        const sub = data.my_submission;
        setText(sub?.text_response ?? "");
        setGithub(sub?.github_url ?? "");
        setLive(sub?.live_url ?? "");
        setBuildInPublic(sub?.build_in_public_url ?? "");
        setDocs(sub?.documentation_url ?? "");
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load assignment");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [assignmentId]);

  async function submit(status: "draft" | "submitted") {
    if (!assignment) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await putMySubmission(assignment.id, {
        status,
        text_response: text,
        github_url: github,
        live_url: live,
        build_in_public_url: buildInPublic,
        documentation_url: docs,
        files: [],
      });
      setAssignment({ ...assignment, my_submission: updated });
      setMessage(status === "submitted" ? "Submitted. Awaiting instructor review." : "Draft saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save submission");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading assignment…
      </div>
    );
  }

  if (error && !assignment) {
    return (
      <EmptyState
        icon={<Loader2 className="size-5" />}
        title="Couldn't load assignment"
        description={error}
      />
    );
  }

  if (!assignment) return null;

  const sub = assignment.my_submission;

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title={assignment.title}
        description={`${assignment.week_label || "Assignment"} · due ${formatDate(assignment.due_date)}`}
      />

      <div className="mb-6 flex flex-wrap items-center gap-2">
        <Badge className="capitalize">{assignment.status}</Badge>
        {sub && <Badge className="capitalize" variant="outline">{sub.status.replace("_", " ")}</Badge>}
        {sub?.score != null && (
          <Badge className="bg-success/10 text-success">Score: {sub.score}/{assignment.max_score}</Badge>
        )}
      </div>

      <Card className="mb-6 shadow-card">
        <CardHeader>
          <CardTitle className="text-lg">Assignment</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">{assignment.description}</p>
          {assignment.instructions && (
            <div>
              <h3 className="mb-1 font-medium">Instructions</h3>
              <p className="whitespace-pre-wrap text-muted-foreground">{assignment.instructions}</p>
            </div>
          )}
          {assignment.required_fields.length > 0 && (
            <div>
              <h3 className="mb-1 font-medium">Requirements</h3>
              <ul className="list-inside list-disc text-sm text-muted-foreground">
                {assignment.required_fields.map((field) => (
                  <li key={field}>{field.replaceAll("_", " ")}</li>
                ))}
              </ul>
            </div>
          )}
          {assignment.resources.length > 0 && (
            <div>
              <h3 className="mb-1 font-medium">Resources</h3>
              <div className="flex flex-wrap gap-2">
                {assignment.resources.map((resource) => (
                  <a
                    key={resource.url}
                    href={resource.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline"
                  >
                    {resource.title}
                    <ExternalLink className="size-3" />
                  </a>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="mb-6 shadow-card">
        <CardHeader>
          <CardTitle className="text-lg">Your submission</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="text">Notes / answer</Label>
            <Textarea id="text" rows={5} value={text} onChange={(e) => setText(e.target.value)} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="github">GitHub URL</Label>
              <Input id="github" value={github} onChange={(e) => setGithub(e.target.value)} placeholder="https://github.com/you/repo" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="live">Live project URL</Label>
              <Input id="live" value={live} onChange={(e) => setLive(e.target.value)} placeholder="https://your-project.vercel.app" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bip">Build in public URL</Label>
              <Input id="bip" value={buildInPublic} onChange={(e) => setBuildInPublic(e.target.value)} placeholder="https://x.com/you/status" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="docs">Documentation URL</Label>
              <Input id="docs" value={docs} onChange={(e) => setDocs(e.target.value)} placeholder="https://docs.your-project.com" />
            </div>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}
          {message && <p className="text-sm text-success">{message}</p>}

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" disabled={saving} onClick={() => submit("draft")}>
              {saving ? "Saving…" : "Save draft"}
            </Button>
            <Button type="button" disabled={saving} onClick={() => submit("submitted")}>
              {saving ? "Submitting…" : "Submit assignment"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {sub && (sub.status === "reviewed" || sub.status === "returned") && (
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle className="text-lg">Instructor feedback</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {sub.score != null && (
              <p className="font-heading text-2xl">
                {sub.score} / {assignment.max_score}
              </p>
            )}
            {sub.feedback && <p className="whitespace-pre-wrap text-muted-foreground">{sub.feedback}</p>}
            {sub.reviewer_name && <p className="text-sm text-muted-foreground">Reviewed by {sub.reviewer_name}</p>}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
