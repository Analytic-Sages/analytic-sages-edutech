"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiError,
  listInstructorProjects,
  reviewProject,
  type InstructorProjectRow,
} from "@/lib/api";

export function InstructorProjectsPanel({ cohortId }: { cohortId: string }) {
  const [projects, setProjects] = useState<InstructorProjectRow[]>([]);
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [savingId, setSavingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listInstructorProjects(cohortId)
      .then((rows) => {
        if (!cancelled) setProjects(rows);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load projects");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [cohortId]);

  async function saveReview(projectId: string, status: string) {
    setSavingId(projectId);
    setError(null);
    try {
      await reviewProject(projectId, { feedback: feedback[projectId] || null, status });
      const refreshed = await listInstructorProjects(cohortId);
      setProjects(refreshed);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save review");
    } finally {
      setSavingId(null);
    }
  }

  if (loading) {
    return <p className="flex items-center gap-2 py-4 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" /> Loading projects…</p>;
  }

  if (projects.length === 0) {
    return <p className="py-4 text-sm text-muted-foreground">No projects yet.</p>;
  }

  return (
    <div className="space-y-3">
      {error && <p className="text-sm text-destructive">{error}</p>}
      {projects.map((row) => (
        <Card key={row.project.id} className="shadow-card">
          <CardHeader className="pb-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-medium">{row.project.title}</p>
                <p className="text-xs text-muted-foreground">{row.full_name || row.email}</p>
              </div>
              <Badge className="capitalize">{row.project.status.replace("_", " ")}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {row.project.description && <p className="text-sm text-muted-foreground">{row.project.description}</p>}
            <div className="flex flex-wrap gap-2">
              {row.project.github_url && (
                <a href={row.project.github_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
                  GitHub <ExternalLink className="size-3" />
                </a>
              )}
              {row.project.live_url && (
                <a href={row.project.live_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
                  Live <ExternalLink className="size-3" />
                </a>
              )}
            </div>
            <Textarea
              rows={2}
              placeholder="Feedback"
              value={feedback[row.project.id] ?? row.project.feedback ?? ""}
              onChange={(e) => setFeedback((prev) => ({ ...prev, [row.project.id]: e.target.value }))}
            />
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="outline" disabled={savingId === row.project.id} onClick={() => saveReview(row.project.id, "reviewed")}>
                Mark reviewed
              </Button>
              <Button size="sm" disabled={savingId === row.project.id} onClick={() => saveReview(row.project.id, "completed")}>
                {savingId === row.project.id ? "Saving…" : "Mark completed"}
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
