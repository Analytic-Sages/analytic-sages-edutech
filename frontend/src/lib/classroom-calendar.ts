import type { LiveSessionPublic } from "@/lib/api";
import {
  buildCalendar,
  downloadIcsFile,
  googleCalendarUrl,
  outlookCalendarUrl,
  type IcsEventInput,
} from "@/lib/calendar-ics";
import { PUBLIC_SITE_ORIGIN } from "@/lib/program-pages";

export function sessionPageUrl(sessionId: string): string {
  return `${PUBLIC_SITE_ORIGIN}/classroom/${sessionId}`;
}

export function sessionContextLabel(session: LiveSessionPublic): string {
  if (session.session_type === "office_hour") {
    return `${session.cohort_name} · ${session.week_label} · Office Hour`;
  }
  return `${session.cohort_name} · ${session.week_label} · Session ${session.session_number}`;
}

export function sessionCalendarDetails(session: LiveSessionPublic): string {
  const parts = [sessionContextLabel(session)];
  if (session.objectives.length > 0) {
    parts.push("", ...session.objectives.map((objective) => `- ${objective}`));
  }
  if (session.assignment_summary) {
    parts.push("", `Assignment: ${session.assignment_summary}`);
  }
  return parts.join("\n");
}

function toIcsEvent(session: LiveSessionPublic): IcsEventInput {
  return {
    uid: `session-${session.id}@analyticsages.io`,
    startsAt: session.starts_at,
    endsAt: session.ends_at,
    summary: session.title,
    description: sessionCalendarDetails(session),
    location: sessionPageUrl(session.id),
    url: sessionPageUrl(session.id),
  };
}

export function googleSessionCalendarUrl(session: LiveSessionPublic): string {
  return googleCalendarUrl({
    title: session.title,
    startsAt: session.starts_at,
    endsAt: session.ends_at,
    details: sessionCalendarDetails(session),
    location: sessionPageUrl(session.id),
  });
}

export function outlookSessionCalendarUrl(session: LiveSessionPublic): string {
  return outlookCalendarUrl({
    title: session.title,
    startsAt: session.starts_at,
    endsAt: session.ends_at,
    details: sessionCalendarDetails(session),
    location: sessionPageUrl(session.id),
  });
}

function sessionFileName(session: LiveSessionPublic): string {
  const slug = session.cohort_slug || "classroom";
  const kind = session.session_type === "office_hour" ? "office-hour" : "session";
  return `${slug}-${kind}-${session.session_number}.ics`;
}

export function downloadSessionIcs(session: LiveSessionPublic): void {
  downloadIcsFile(
    sessionFileName(session),
    buildCalendar([toIcsEvent(session)], { calendarName: session.cohort_name })
  );
}

export function downloadAllSessionsIcs(
  sessions: LiveSessionPublic[],
  calendarName = "Analytic Sages Classroom"
): void {
  if (sessions.length === 0) return;
  downloadIcsFile(
    "analytic-sages-classroom.ics",
    buildCalendar(sessions.map(toIcsEvent), { calendarName })
  );
}

export function nextUpcomingSession(
  sessions: LiveSessionPublic[]
): LiveSessionPublic | undefined {
  return sessions.find((session) => session.phase === "upcoming" || session.phase === "live");
}