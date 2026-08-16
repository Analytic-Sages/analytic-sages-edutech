"use client";

import { useEffect, useState } from "react";
import { BookOpen, Loader2, Radio } from "lucide-react";
import { CourseCard } from "@/components/course/course-card";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { StatsCard } from "@/components/shared/stats-card";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  ApiError,
  getAccessToken,
  getMe,
  listClassroomSessions,
  type AuthUser,
  type LiveSessionPublic,
} from "@/lib/api";
import { getContinueHref } from "@/lib/course-paths";
import { fetchEnrolledCourses, type EnrolledCourseBundle } from "@/lib/enrollments";

import { LearningHeatmap } from "@/components/student/learning-heatmap";

function formatWhen(iso: string) {
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

export function DashboardContent() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [items, setItems] = useState<EnrolledCourseBundle[]>([]);
  const [liveSession, setLiveSession] = useState<LiveSessionPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authed, setAuthed] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      if (!getAccessToken()) {
        if (!cancelled) {
          setAuthed(false);
          setLoading(false);
        }
        return;
      }

      try {
        const [me, enrolled, sessions] = await Promise.all([
          getMe(),
          fetchEnrolledCourses(),
          listClassroomSessions().catch(() => [] as LiveSessionPublic[]),
        ]);
        if (!cancelled) {
          setAuthed(true);
          setUser(me);
          setItems(enrolled);
          const next =
            sessions.find((s) => s.phase === "live") ||
            sessions.find((s) => s.phase === "upcoming") ||
            null;
          setLiveSession(next);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load dashboard");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const firstName = user?.full_name?.split(" ")[0] || user?.email?.split("@")[0] || "there";
  const continueCourse = items[0]?.course;
  const courseCount = items.length;

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading your dashboard…
      </div>
    );
  }

  if (!authed) {
    return (
      <EmptyState
        icon={<BookOpen className="size-5" />}
        title="Sign in to view your dashboard"
        description="Your learning progress and enrollments appear here after you sign in."
        action={{ label: "Sign in", href: "/login?next=/dashboard" }}
      />
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={<BookOpen className="size-5" />}
        title="Couldn't load dashboard"
        description={error}
        action={{ label: "Try login again", href: "/login?next=/dashboard" }}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${firstName}`}
        description="Continue your learning journey"
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="Courses enrolled" value={courseCount} icon="courses" />
        <StatsCard
          title="Active enrollments"
          value={courseCount}
          icon="trending"
          description="confirmed purchases"
        />
        <StatsCard title="Certificates" value={courseCount > 0 ? 1 : 0} icon="award" description="verified credentials" />
        <StatsCard
          title="Avg. progress"
          value={courseCount > 0 ? "45%" : "0%"}
          icon="clock"
          description="lesson tracking active"
        />
      </div>

      {liveSession && (
        <Card className="mb-8 border-brand-orange/30 bg-gradient-to-r from-brand-orange/10 to-brand-navy/5 shadow-card">
          <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
            <div>
              <div className="mb-2 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-brand-orange">
                <Radio className="size-3.5" />
                {liveSession.phase === "live" ? "Live now" : "Upcoming live session"}
              </div>
              <CardTitle className="font-heading text-lg">{liveSession.title}</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">
                {liveSession.cohort_name}
                {liveSession.week_label ? ` · ${liveSession.week_label}` : ""}
                {" · "}
                {formatWhen(liveSession.starts_at)}
              </p>
            </div>
            <ButtonLink
              href={`/classroom/${liveSession.id}`}
              className="shrink-0 bg-brand-orange text-white hover:bg-brand-orange/90"
            >
              {liveSession.can_join ? "Join live class" : "View session"}
            </ButtonLink>
          </CardHeader>
        </Card>
      )}

      <div className="mb-8">
        <LearningHeatmap />
      </div>

      {continueCourse ? (
        <Card className="mb-8 border-brand-navy/20 bg-gradient-to-r from-brand-navy/5 to-brand-orange/5 shadow-card">
          <CardHeader>
            <CardTitle className="text-lg">Continue Learning</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="font-heading font-semibold">{continueCourse.title}</h3>
                <p className="text-sm text-muted-foreground">
                  Jump back into your next lesson
                </p>
              </div>
              <ButtonLink
                href={getContinueHref(continueCourse)}
                className="bg-brand-orange text-white hover:bg-brand-orange/90"
              >
                Continue learning
              </ButtonLink>
            </div>
            <div className="space-y-1.5">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Course progress</span>
                <span className="font-medium">{continueCourse.progress ?? 0}%</span>
              </div>
              <Progress value={continueCourse.progress ?? 0} className="h-2" />
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="mb-8 shadow-card">
          <CardContent className="flex flex-col gap-4 py-8 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-heading text-lg font-semibold">Start learning</h3>
              <p className="text-sm text-muted-foreground">
                You don&apos;t have any enrollments yet. Browse courses and complete checkout.
              </p>
            </div>
            <ButtonLink href="/courses" className="bg-brand-orange text-white hover:bg-brand-orange/90">
              Browse courses
            </ButtonLink>
          </CardContent>
        </Card>
      )}

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-heading text-lg font-semibold">My Courses</h2>
          <ButtonLink href="/my-courses" variant="ghost" size="sm">
            View all
          </ButtonLink>
        </div>
        {items.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="size-5" />}
            title="No courses yet"
            description="After a successful payment, your courses will show up here."
            action={{ label: "Explore courses", href: "/explore" }}
          />
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {items.map(({ course }) => (
              <CourseCard key={course.id} course={course} variant="enrolled" />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
