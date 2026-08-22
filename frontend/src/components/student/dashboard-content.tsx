"use client";

import { useEffect, useState } from "react";
import { BookOpen, CalendarDays, Loader2, Radio } from "lucide-react";
import { EventCard } from "@/components/events/event-card";
import { CourseCard } from "@/components/course/course-card";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { StatsCard } from "@/components/shared/stats-card";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiError,
  getAccessToken,
  getMe,
  getMyEvents,
  listClassroomSessions,
  type AuthUser,
  type EventRegistrationPublic,
  type LiveSessionPublic,
} from "@/lib/api";
import { fetchEnrolledCourses, type EnrolledCourseBundle } from "@/lib/enrollments";

import { LearningProgress } from "@/components/student/learning-progress";

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
  const [eventRegs, setEventRegs] = useState<EventRegistrationPublic[]>([]);
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
        const [me, enrolled, sessions, myEvents] = await Promise.all([
          getMe(),
          fetchEnrolledCourses(),
          listClassroomSessions().catch(() => [] as LiveSessionPublic[]),
          getMyEvents().catch(() => [] as EventRegistrationPublic[]),
        ]);
        if (!cancelled) {
          setAuthed(true);
          setUser(me);
          setItems(enrolled);
          setEventRegs(myEvents);
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
  const courseCount = items.length;
  const avgProgress =
    courseCount > 0
      ? Math.round(items.reduce((sum, item) => sum + (item.course.progress ?? 0), 0) / courseCount)
      : 0;

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
          description="courses in progress"
        />
        <StatsCard title="Certificates" value="-" icon="award" description="Coming soon" />
        <StatsCard
          title="Avg. progress"
          value={`${avgProgress}%`}
          icon="clock"
          description="lesson tracking"
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

      {items.length > 0 ? (
        <div className="mb-8">
          <LearningProgress items={items} />
        </div>
      ) : (
        <Card className="mb-8 shadow-card">
          <CardContent className="flex flex-col gap-4 py-8 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-heading text-lg font-semibold">Start learning</h3>
              <p className="text-sm text-muted-foreground">
                You haven&apos;t enrolled in any courses yet.
              </p>
            </div>
            <ButtonLink href="/courses?price=free" className="bg-brand-orange text-white hover:bg-brand-orange/90">
              Explore Free Courses
            </ButtonLink>
          </CardContent>
        </Card>
      )}

      <section className="mb-8">
        <h2 className="mb-4 font-heading text-lg font-semibold">Certificates</h2>
        <Card className="shadow-card">
          <CardContent className="py-10 text-center">
            <p className="font-heading text-lg font-semibold">Coming soon</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Platform certificates are not issued yet. Completing a course still gives you the work
              you can show.
            </p>
          </CardContent>
        </Card>
      </section>

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
            title="You haven't enrolled in any courses yet."
            description="Explore a free self-paced course to start learning."
            action={{ label: "Explore Free Courses", href: "/courses?price=free" }}
          />
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {items.map(({ course }) => (
              <CourseCard key={course.id} course={course} variant="enrolled" />
            ))}
          </div>
        )}
      </section>

      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-heading text-lg font-semibold">My Events</h2>
          <ButtonLink href="/my-events" variant="ghost" size="sm">
            View all
          </ButtonLink>
        </div>
        {eventRegs.length === 0 ? (
          <EmptyState
            icon={<CalendarDays className="size-5" />}
            title="No event registrations yet"
            description="Browse free workshops and register with this account."
            action={{ label: "Browse events", href: "/events" }}
          />
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {eventRegs.slice(0, 3).map((row) => (
              <EventCard key={row.id} event={row.event} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
