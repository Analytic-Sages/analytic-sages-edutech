"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, listShowcaseProjects, type ShowcaseProject } from "@/lib/api";

export function ShowcaseContent() {
  const [projects, setProjects] = useState<ShowcaseProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listShowcaseProjects()
      .then(setProjects)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Failed to load showcase"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading student projects…
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Student projects"
        description="Real work built by Analytic Sages learners in live cohorts."
      />

      {error && <p className="mb-4 text-sm text-destructive">{error}</p>}

      {projects.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-5" />}
          title="No public projects yet"
          description="Projects will appear here as students publish their work."
        />
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((row) => (
            <Card key={row.project.id} className="shadow-card">
              <CardHeader className="pb-2">
                <CardTitle className="font-heading text-lg">{row.project.title}</CardTitle>
                <p className="text-sm text-muted-foreground">
                  By {row.full_name || "Analytic Sages student"}
                </p>
              </CardHeader>
              <CardContent className="space-y-3">
                {row.project.description && (
                  <p className="line-clamp-3 text-sm text-muted-foreground">{row.project.description}</p>
                )}
                {row.project.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {row.project.technologies.map((t) => (
                      <Badge key={t} variant="outline">{t}</Badge>
                    ))}
                  </div>
                )}
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
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
