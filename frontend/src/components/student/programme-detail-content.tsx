"use client";

import { useEffect, useState } from "react";
import { CalendarDays, ExternalLink, Loader2, Radio } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StudentProjectsSection } from "@/components/student/student-projects-section";
import {
  ApiError,
  getAccessToken,
  getMyAssignments,
  getMyCohort,
  getMyLiveEnrollments,
  getProgramme,
  type AssignmentPublic,
  type CohortStudentDetail,
  type ProgrammeDetailPublic,
} from "@/lib/api";

function formatWhen(iso: string | null) {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function ProgrammeDetailContent({ slug }: { slug: string }) {
  const [cohort, setCohort] = useState<CohortStudentDetail | null>(null);
  const [assignments, setAssignments] = useState<AssignmentPublic[]>([]);
  const [programme, setProgramme] = useState<ProgrammeDetailPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        if (getAccessToken()) {
          const mine = await getMyLiveEnrollments().catch(() => []);
          const match = mine.find(
            (item) => item.programme_slug === slug || item.cohort_slug === slug,
          );
          if (match) {
            const [detail, cohortAssignments] = await Promise.all([
              getMyCohort(match.cohort_id),
              getMyAssignments(match.cohort_id).catch(() => [] as AssignmentPublic[]),
            ]);
            if (!cancelled) {
              setCohort(detail);
              setAssignments(cohortAssignments);
            }
            return;
          }
        }
        const publicDetail = await getProgramme(slug);
        if (!cancelled) setProgramme(publicDetail);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load programme");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading programme…
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={<Radio className="size-5" />}
        title="Couldn't load programme"
        description={error}
        action={{ label: "Back to programmes", href: "/programmes" }}
      />
    );
  }

  if (cohort) {
    const attendance = cohort.attendance;
    return (
      <div>
        <PageHeader title={cohort.programme?.title || cohort.name} description={cohort.name} />
        <div className="mb-6 flex flex-wrap items-center gap-2">
          <Badge className="capitalize">{cohort.status}</Badge>
          <span className="text-sm text-muted-foreground">
            {formatWhen(cohort.starts_at)} → {formatWhen(cohort.ends_at)}
          </span>
        </div>

        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          <Card className="shadow-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-heading text-2xl">{cohort.progress_percent}%</p>
              <Progress value={cohort.progress_percent} className="mt-2" />
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Attendance</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-heading text-2xl">
                {attendance.attended + attendance.late} / {cohort.sessions.length}
              </p>
              <p className="text-xs text-muted-foreground">
                {attendance.late} late · {attendance.absent} absent
              </p>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-heading text-2xl">{cohort.sessions.length}</p>
              <p className="text-xs text-muted-foreground">live cohort sessions</p>
            </CardContent>
          </Card>
        </div>

        {Object.keys(cohort.community_links).length > 0 && (
          <section className="mb-8">
            <h2 className="mb-3 font-heading text-lg font-semibold">Community</h2>
            <div className="flex flex-wrap gap-2">
              {Object.entries(cohort.community_links).map(([label, url]) => (
                <ButtonLink key={label} href={url} variant="outline" size="sm" target="_blank">
                  <ExternalLink className="size-4" />
                  {label}
                </ButtonLink>
              ))}
            </div>
          </section>
        )}
        {assignments.length > 0 && (
          <section className="mb-8">
            <h2 className="mb-3 font-heading text-lg font-semibold">Assignments</h2>
            <div className="space-y-3">
              {assignments.map((assignment) => (
                <Card key={assignment.id} className="shadow-card">
                  <CardHeader className="flex flex-row items-start justify-between gap-4 pb-2">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">
                        {assignment.week_label || "Assignment"}
                      </p>
                      <CardTitle className="font-heading text-base">{assignment.title}</CardTitle>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Due {formatWhen(assignment.due_date)}
                      </p>
                    </div>
                    <ButtonLink href={`/assignments/${assignment.id}`} variant="outline">
                      View
                    </ButtonLink>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </section>
        )}

        <StudentProjectsSection cohortId={cohort.id} />

        <section>
          <h2 className="mb-3 font-heading text-lg font-semibold">Schedule</h2>
          <div className="space-y-3">
            {cohort.sessions.map((session) => (
              <Card key={session.id} className="shadow-card">
                <CardHeader className="flex flex-row items-start justify-between gap-4 pb-2">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">
                      {session.week_label || "Session"}
                    </p>
                    <CardTitle className="font-heading text-base">{session.title}</CardTitle>
                    <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
                      <CalendarDays className="size-3.5" />
                      {formatWhen(session.starts_at)}
                    </p>
                  </div>
                  {session.access_blocked ? (
                    <span className="rounded-md bg-destructive/10 px-2 py-1 text-xs text-destructive">
                      Payment required
                    </span>
                  ) : session.can_join ? (
                    <ButtonLink
                      href={`/classroom/${session.id}`}
                      className="bg-brand-orange text-white hover:bg-brand-orange/90"
                    >
                      Join
                    </ButtonLink>
                  ) : (
                    <ButtonLink href={`/classroom/${session.id}`} variant="outline">
                      View
                    </ButtonLink>
                  )}
                </CardHeader>
                {session.resources.length > 0 && (
                  <CardContent className="pt-0">
                    <div className="flex flex-wrap gap-2">
                      {session.resources.map((resource) => (
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
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        </section>
      </div>
    );
  }

  if (programme) {
    return (
      <div>
        <PageHeader title={programme.title} description={programme.description} />
        <div className="mb-6 flex flex-wrap items-center gap-2">
          <Badge className="capitalize">{programme.status}</Badge>
          {programme.duration && (
            <span className="text-sm text-muted-foreground">{programme.duration}</span>
          )}
        </div>
        <p className="mb-6 max-w-3xl text-muted-foreground">
          {programme.overview || programme.description}
        </p>
        {programme.cohorts.length === 0 ? (
          <EmptyState
            icon={<Radio className="size-5" />}
            title="No open cohorts yet"
            description="This programme has not opened a cohort for registration."
          />
        ) : (
          <div className="space-y-3">
            {programme.cohorts.map((cohort) => (
              <Card key={cohort.id} className="shadow-card">
                <CardHeader className="flex flex-row items-start justify-between gap-4">
                  <div>
                    <CardTitle className="font-heading text-lg">{cohort.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {formatWhen(cohort.starts_at)} · {cohort.timezone}
                    </p>
                  </div>
                  <Badge className="capitalize">{cohort.status}</Badge>
                </CardHeader>
                <CardContent>
                  <ButtonLink
                    href={`/checkout/cohort/${cohort.slug}`}
                    className="bg-brand-orange text-white hover:bg-brand-orange/90"
                  >
                    Register
                  </ButtonLink>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <EmptyState
      icon={<Radio className="size-5" />}
      title="Programme not found"
      description="This programme may not be available yet."
      action={{ label: "View all programmes", href: "/programmes" }}
    />
  );
}

