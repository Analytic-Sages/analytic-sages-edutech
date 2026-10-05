"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, getMyPortfolio, updateMyPortfolioVisibility, type MyPortfolio } from "@/lib/api";

export function PortfolioContent() {
  const [portfolio, setPortfolio] = useState<MyPortfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyPortfolio()
      .then(setPortfolio)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Failed to load portfolio"))
      .finally(() => setLoading(false));
  }, []);

  async function togglePublic(next: boolean) {
    if (!portfolio) return;
    try {
      const updated = await updateMyPortfolioVisibility(next);
      setPortfolio(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update visibility");
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading portfolio…
      </div>
    );
  }

  if (error && !portfolio) {
    return <EmptyState icon={<Loader2 className="size-5" />} title="Couldn't load portfolio" description={error} />;
  }

  if (!portfolio) return null;

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="My Portfolio" description="Your public profile and projects." />

      <Card className="mb-6 shadow-card">
        <CardHeader>
          <CardTitle className="text-lg">Visibility</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={portfolio.portfolio_public}
              onChange={(e) => togglePublic(e.target.checked)}
            />
            Make my portfolio public
          </label>
          {portfolio.public_url && (
            <p className="text-sm">
              Public link:{" "}
              <a href={portfolio.public_url} className="text-brand-orange hover:underline">
                {portfolio.public_url}
              </a>
            </p>
          )}
          <div className="flex flex-wrap gap-2">
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
        </CardContent>
      </Card>

      <section className="mb-6">
        <h2 className="mb-3 font-heading text-lg font-semibold">Projects</h2>
        {portfolio.projects.length === 0 ? (
          <p className="text-sm text-muted-foreground">No projects yet.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {portfolio.projects.map((project) => (
              <Card key={project.id} className="shadow-card">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="text-base">{project.title}</CardTitle>
                    <Badge className="capitalize">{project.status.replace("_", " ")}</Badge>
                  </div>
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
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 font-heading text-lg font-semibold">Certificate eligibility</h2>
        {portfolio.certificates.length === 0 ? (
          <p className="text-sm text-muted-foreground">No live programmes enrolled yet.</p>
        ) : (
          <div className="space-y-3">
            {portfolio.certificates.map((cert) => (
              <Card key={cert.cohort_id} className="shadow-card">
                <CardHeader className="flex flex-row items-center justify-between gap-2 pb-2">
                  <CardTitle className="text-base">{cert.programme_title || cert.cohort_name}</CardTitle>
                  <Badge className={cert.eligible ? "bg-success/10 text-success" : "bg-muted text-muted-foreground"}>
                    {cert.eligible ? "Eligible" : "Not eligible"}
                  </Badge>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground">
                  <p>Attendance {cert.attendance_percent}%</p>
                  <p>Assignments {cert.assignments_submitted}/{cert.assignments_total}</p>
                  <p>Projects completed {cert.projects_completed}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <div className="mt-6">
        <ButtonLink href="/showcase" variant="outline">
          View public showcase
        </ButtonLink>
      </div>
    </div>
  );
}
