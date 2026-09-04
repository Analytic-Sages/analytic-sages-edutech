"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PageHeader } from "@/components/layout/page-header";
import { StatsCard } from "@/components/shared/stats-card";
import { EmptyState } from "@/components/shared/empty-state";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatAdminDate, formatMoneyList } from "@/components/admin/admin-format";
import { ApiError, getAdminAnalytics, type AdminAnalytics } from "@/lib/api";

function formatDay(iso: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      timeZone: "UTC",
    }).format(new Date(`${iso}T00:00:00Z`));
  } catch {
    return iso;
  }
}

function prettyName(value: string) {
  return value.replaceAll("_", " ");
}

export function AdminAnalyticsContent() {
  const [data, setData] = useState<AdminAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getAdminAnalytics()
      .then((analytics) => {
        if (!cancelled) setData(analytics);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load analytics");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading live numbers…
      </div>
    );
  }

  if (error || !data) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn’t load analytics"
        description={error || "Try signing in again as an admin."}
        action={{ label: "Retry", href: "/admin/analytics" }}
      />
    );
  }

  const cohort = data.featured_cohort;
  const signupSeries = data.signups_by_day.map((point) => ({
    ...point,
    day: formatDay(point.label),
  }));
  const enrollmentSeries = data.enrollments_by_day.map((point) => ({
    ...point,
    day: formatDay(point.label),
  }));

  return (
    <div>
      <PageHeader
        title="Analytics"
        description="Live counts from the database. Zeros mean nothing has happened yet — they are not sample data."
        action={
          <ButtonLink href="/admin" variant="outline">
            Featured cohort monitor
          </ButtonLink>
        }
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Signups (30 days)"
          value={data.signups_30d}
          icon="users"
          description={`${data.signups_7d} in 7 days · ${data.signups_24h} in 24 hours`}
        />
        <StatsCard
          title="Accounts"
          value={data.users_total}
          icon="users"
          description={`${data.users_verified} verified · ${data.users_unverified} unverified · ${data.students_total} students`}
        />
        <StatsCard
          title="Learning"
          value={data.enrollments_active + data.enrollments_completed}
          icon="courses"
          description={`${data.enrollments_active} active · ${data.enrollments_completed} completed · ${data.lessons_completed} lessons marked complete`}
        />
        <StatsCard
          title="Confirmed payments"
          value={data.payments_confirmed}
          icon="payments"
          description={`${data.payments_pending} pending · ${formatMoneyList(data.revenue_by_currency)}`}
        />
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Lesson activity (7 days)"
          value={data.learners_active_7d}
          icon="clock"
          description="Distinct learners with lesson progress in the last 7 days"
        />
        <StatsCard
          title="Event signups"
          value={data.event_registrations}
          icon="users"
          description="Registered event seats, excluding cancelled"
        />
        <StatsCard
          title="Published opportunities"
          value={data.published_opportunities}
          icon="trending"
          description={`${data.opportunity_saves} saved or marked applied`}
        />
        <StatsCard
          title="Published insights"
          value={data.published_insights}
          icon="award"
          description={
            cohort
              ? `${cohort.name}: ${cohort.student_seats} student seats`
              : "Featured cohort is not in the database yet"
          }
        />
      </div>

      <div className="mb-8 grid gap-6 lg:grid-cols-2">
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Signups by day</CardTitle>
            <p className="text-sm text-muted-foreground">New accounts created in the last 30 days</p>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={signupSeries}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} interval={4} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={32} />
                <Tooltip />
                <Line type="monotone" dataKey="value" name="Signups" stroke="#F58220" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Enrollments by day</CardTitle>
            <p className="text-sm text-muted-foreground">Course enrollments created in the last 30 days</p>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={enrollmentSeries}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} interval={4} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={32} />
                <Tooltip />
                <Bar dataKey="value" name="Enrollments" fill="#101A8A" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="mb-8 grid gap-6 lg:grid-cols-2">
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Roles</CardTitle>
            <p className="text-sm text-muted-foreground">Every account, including staff</p>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {data.roles.map((row) => (
                <li key={row.name} className="flex items-center justify-between capitalize">
                  <span>{prettyName(row.name)}</span>
                  <span className="font-medium tabular-nums">{row.value}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Opportunity pipeline</CardTitle>
            <p className="text-sm text-muted-foreground">Listings by status, including drafts</p>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {data.opportunity_statuses.map((row) => (
                <li key={row.name} className="flex items-center justify-between capitalize">
                  <span>{prettyName(row.name)}</span>
                  <span className="font-medium tabular-nums">{row.value}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <div className="mb-8 grid gap-6 lg:grid-cols-2">
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Course enrollments</CardTitle>
            <p className="text-sm text-muted-foreground">Active and completed seats, not revoked</p>
          </CardHeader>
          <CardContent>
            {data.courses.length === 0 ? (
              <p className="text-sm text-muted-foreground">No course enrollments yet.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {data.courses.map((row) => (
                  <li key={row.name} className="flex items-center justify-between gap-4">
                    <span className="min-w-0 truncate">{row.name}</span>
                    <span className="font-medium tabular-nums">{row.value}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Recent lesson activity</CardTitle>
            <p className="text-sm text-muted-foreground">Last lesson progress, not last login</p>
          </CardHeader>
          <CardContent>
            {data.recent_learners.length === 0 ? (
              <p className="text-sm text-muted-foreground">No lesson activity recorded yet.</p>
            ) : (
              <ul className="space-y-3 text-sm">
                {data.recent_learners.map((row) => (
                  <li key={`${row.user_email}-${row.last_activity_at}`}>
                    <p className="font-medium">{row.user_name || row.user_email}</p>
                    <p className="text-muted-foreground">
                      {row.course_title} · {formatAdminDate(row.last_activity_at)}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Not tracked yet</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {data.untracked.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
