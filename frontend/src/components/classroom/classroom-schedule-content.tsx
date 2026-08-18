"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  Clock,
  ExternalLink,
  FileText,
  Loader2,
  Radio,
  Video,
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, listClassroomSessions, type LiveSessionPublic } from "@/lib/api";
import { cn } from "@/lib/utils";

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

function PhaseBadge({ phase }: { phase: LiveSessionPublic["phase"] }) {
  const styles = {
    live: "bg-red-500/15 text-red-700 dark:text-red-300",
    upcoming: "bg-brand-orange/15 text-brand-orange",
    ended: "bg-muted text-muted-foreground",
    cancelled: "bg-muted text-muted-foreground",
  } as const;
  const labels = {
    live: "Live now",
    upcoming: "Upcoming",
    ended: "Ended",
    cancelled: "Cancelled",
  } as const;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-semibold uppercase tracking-wide",
        styles[phase]
      )}
    >
      {phase === "live" && <span className="size-1.5 animate-pulse rounded-full bg-red-500" />}
      {labels[phase]}
    </span>
  );
}

export function ClassroomScheduleContent({
  audience = "student",
}: {
  audience?: "student" | "staff";
}) {
  const [sessions, setSessions] = useState<LiveSessionPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await listClassroomSessions();
        if (!cancelled) setSessions(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load classroom sessions");
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

  const isStaff = audience === "staff";

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading your classroom…
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={<Video className="size-5" />}
        title="Couldn't load classroom"
        description={error}
        action={{
          label: isStaff ? "Back to staff classroom" : "Back to dashboard",
          href: isStaff ? "/staff" : "/dashboard",
        }}
      />
    );
  }

  const live = sessions.filter((s) => s.phase === "live");
  const upcoming = sessions.filter((s) => s.phase === "upcoming");
  const past = sessions.filter((s) => s.phase === "ended" || s.phase === "cancelled");

  return (
    <div>
      <PageHeader
        title={isStaff ? "Staff classroom" : "Live Classroom"}
        description={
          isStaff
            ? "Join Cohort 9 sessions as instructor. Student seats unlock after payment is confirmed."
            : "Expert-led sessions for your cohort. Join when class is live; review resources anytime."
        }
      />

      {sessions.length === 0 ? (
        <EmptyState
          icon={<Radio className="size-5" />}
          title={isStaff ? "No sessions on the calendar yet" : "No cohort sessions yet"}
          description={
            isStaff
              ? "When Cohort 9 sessions are scheduled, they will show here so you can join as instructor."
              : "You're signed in, but not enrolled in a live cohort yet. Ask an admin to add you, or for local dev run: python scripts/seed_classroom.py --email your@email.com"
          }
          action={
            isStaff
              ? undefined
              : { label: "View live training", href: "/instructor-led" }
          }
        />
      ) : (
        <div className="space-y-10">
          {live.length > 0 && (
            <section>
              <h2 className="mb-4 font-heading text-lg font-semibold">Happening now</h2>
              <div className="grid gap-4">
                {live.map((session) => (
                  <SessionCard key={session.id} session={session} highlight />
                ))}
              </div>
            </section>
          )}

          {upcoming.length > 0 && (
            <section>
              <h2 className="mb-4 font-heading text-lg font-semibold">Upcoming</h2>
              <div className="grid gap-4">
                {upcoming.map((session) => (
                  <SessionCard key={session.id} session={session} />
                ))}
              </div>
            </section>
          )}

          {past.length > 0 && (
            <section>
              <h2 className="mb-4 font-heading text-lg font-semibold">Past sessions</h2>
              <div className="grid gap-4">
                {past.map((session) => (
                  <SessionCard key={session.id} session={session} />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

function SessionCard({
  session,
  highlight = false,
}: {
  session: LiveSessionPublic;
  highlight?: boolean;
}) {
  return (
    <Card
      className={cn(
        "shadow-card",
        highlight && "border-red-500/30 bg-gradient-to-r from-red-500/5 to-brand-orange/5"
      )}
    >
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0 pb-3">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <PhaseBadge phase={session.phase} />
            <span className="text-xs text-muted-foreground">
              {session.cohort_name}
              {session.week_label ? ` · ${session.week_label}` : ""}
              {` · Session ${session.session_number}`}
            </span>
          </div>
          <CardTitle className="font-heading text-xl">{session.title}</CardTitle>
          {session.course_title && (
            <p className="mt-1 text-sm text-muted-foreground">{session.course_title}</p>
          )}
        </div>
        {session.can_join ? (
          <ButtonLink
            href={`/classroom/${session.id}`}
            className="shrink-0 bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            Join live class
          </ButtonLink>
        ) : (
          <ButtonLink href={`/classroom/${session.id}`} variant="outline" className="shrink-0">
            View session
          </ButtonLink>
        )}
      </CardHeader>
      <CardContent className="flex flex-wrap gap-4 text-sm text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Calendar className="size-3.5" />
          {formatWhen(session.starts_at)}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Clock className="size-3.5" />
          Until {formatWhen(session.ends_at)}
        </span>
        {session.resources.length > 0 && (
          <span className="inline-flex items-center gap-1.5">
            <FileText className="size-3.5" />
            {session.resources.length} resource{session.resources.length === 1 ? "" : "s"}
          </span>
        )}
        {session.recording_url && (
          <Link
            href={session.recording_url}
            className="inline-flex items-center gap-1.5 text-brand-navy hover:underline dark:text-brand-orange"
            target="_blank"
            rel="noreferrer"
          >
            <ExternalLink className="size-3.5" />
            Watch recording
          </Link>
        )}
      </CardContent>
    </Card>
  );
}
