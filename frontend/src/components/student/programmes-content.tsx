"use client";

import { useEffect, useState } from "react";
import { Loader2, Radio } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiError,
  getAccessToken,
  getMyLiveEnrollments,
  listProgrammes,
  type MyLiveEnrollment,
  type ProgrammePublic,
} from "@/lib/api";

export function ProgrammesContent() {
  const [mine, setMine] = useState<MyLiveEnrollment[]>([]);
  const [available, setAvailable] = useState<ProgrammePublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        if (getAccessToken()) {
          const enrolled = await getMyLiveEnrollments().catch(() => []);
          if (!cancelled) setMine(enrolled);
        }
        const publicRows = await listProgrammes().catch(() => []);
        if (!cancelled) setAvailable(publicRows);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load programmes");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading programmes…
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Live Programmes"
        description="Instructor-led cohorts with live sessions, assignments and projects."
      />

      {error && (
        <p className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      {mine.length > 0 && (
        <section className="mb-10">
          <h2 className="mb-4 font-heading text-lg font-semibold">My programmes</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {mine.map((programme) => (
              <Card key={programme.cohort_id} className="shadow-card">
                <CardHeader className="pb-3">
                  <Badge className="mb-2 w-fit capitalize">{programme.enrollment_status}</Badge>
                  <CardTitle className="font-heading text-lg">
                    {programme.programme_title || programme.cohort_name}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">{programme.cohort_name}</p>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-medium">{programme.progress_percent}%</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-brand-orange"
                      style={{ width: `${programme.progress_percent}%` }}
                    />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Attendance {programme.attendance_attended}/{programme.attendance_total}
                  </p>
                  <ButtonLink
                    href={`/programmes/${programme.programme_slug || programme.cohort_slug}`}
                    variant="outline"
                    className="w-full"
                  >
                    View programme
                  </ButtonLink>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-4 font-heading text-lg font-semibold">Available programmes</h2>
        {available.length === 0 ? (
          <EmptyState
            icon={<Radio className="size-5" />}
            title="No open programmes right now"
            description="New live cohorts are announced on the instructor-led page."
            action={{ label: "View instructor-led training", href: "/instructor-led" }}
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {available.map((programme) => (
              <Card key={programme.id} className="shadow-card">
                <CardHeader className="pb-3">
                  <CardTitle className="font-heading text-lg">{programme.title}</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {programme.duration || "Live instruction"}
                  </p>
                </CardHeader>
                <CardContent>
                  <p className="line-clamp-3 text-sm text-muted-foreground">
                    {programme.description}
                  </p>
                  <ButtonLink
                    href={`/programmes/${programme.slug}`}
                    variant="outline"
                    className="mt-4 w-full"
                  >
                    View details
                  </ButtonLink>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
