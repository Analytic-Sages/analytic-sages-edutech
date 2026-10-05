"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, getPublicPortfolio, type PublicPortfolio } from "@/lib/api";

export function PublicPortfolioContent({ userId }: { userId: string }) {
  const [portfolio, setPortfolio] = useState<PublicPortfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPublicPortfolio(userId)
      .then(setPortfolio)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Portfolio not found"))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading portfolio…
      </div>
    );
  }

  if (error || !portfolio) {
    return (
      <EmptyState
        icon={<Loader2 className="size-5" />}
        title="Portfolio not found"
        description="This portfolio is not public or does not exist."
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={portfolio.full_name || "Student"} description="Analytic Sages student portfolio" />

      <div className="mb-6 flex flex-wrap gap-2">
        {portfolio.github_url && (
          <a href={portfolio.github_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
            GitHub <ExternalLink className="size-3" />
          </a>
        )}
        {portfolio.linkedin_url && (
          <a href={portfolio.linkedin_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
            LinkedIn <ExternalLink className="size-3" />
          </a>
        )}
        {portfolio.portfolio_url && (
          <a href={portfolio.portfolio_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
            Website <ExternalLink className="size-3" />
          </a>
        )}
      </div>

      <section>
        <h2 className="mb-3 font-heading text-lg font-semibold">Projects</h2>
        {portfolio.projects.length === 0 ? (
          <p className="text-sm text-muted-foreground">No public projects.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {portfolio.projects.map((project) => (
              <Card key={project.id} className="shadow-card">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{project.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {project.description && <p className="text-sm text-muted-foreground">{project.description}</p>}
                  {project.technologies.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {project.technologies.map((t) => (
                        <Badge key={t} variant="outline">{t}</Badge>
                      ))}
                    </div>
                  )}
                  {project.github_url && (
                    <a href={project.github_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
                      GitHub <ExternalLink className="size-3" />
                    </a>
                  )}
                  {project.live_url && (
                    <a href={project.live_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
                      Live <ExternalLink className="size-3" />
                    </a>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
