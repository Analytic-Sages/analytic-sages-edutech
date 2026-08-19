import type { EventCardPublic, EventPublic } from "@/lib/api";
import { PUBLIC_SITE_ORIGIN } from "@/lib/program-pages";

export const FEATURED_EVENT_SLUG = "dune-analytics-building-your-first-defi-dashboard";

export const EVENT_TYPE_LABELS: Record<string, string> = {
  workshop: "Workshop",
  webinar: "Webinar",
  masterclass: "Masterclass",
  ama: "AMA",
  community: "Community",
  career: "Career",
  other: "Event",
};

export const EVENT_LIFECYCLE_LABELS: Record<string, string> = {
  draft: "Draft",
  coming_soon: "Coming soon",
  upcoming: "Upcoming",
  registration_closed: "Registration closed",
  live: "Live now",
  completed: "Completed",
  cancelled: "Cancelled",
};

export function eventTypeLabel(type: string) {
  return EVENT_TYPE_LABELS[type] ?? "Event";
}

export function eventLifecycleLabel(lifecycle: string) {
  return EVENT_LIFECYCLE_LABELS[lifecycle] ?? lifecycle;
}

export function formatEventWhen(event: Pick<EventCardPublic, "starts_at" | "ends_at" | "timezone">) {
  if (!event.starts_at || !event.ends_at) return "Date coming soon";
  const start = new Date(event.starts_at);
  const end = new Date(event.ends_at);
  const date = new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: event.timezone,
  }).format(start);
  const time = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: event.timezone,
  });
  return `${date} · ${time.format(start)}–${time.format(end)} ${shortTimezone(event.timezone)}`;
}

export function shortTimezone(timezone: string) {
  if (timezone === "Africa/Lagos") return "WAT";
  return timezone.replace("_", " ");
}

export function registerLoginPath(slug: string) {
  return `/login?next=${encodeURIComponent(`/events/${slug}?register=1`)}`;
}

function icsUtc(value: string) {
  return new Date(value).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

export function eventPageUrl(slug: string) {
  return `${PUBLIC_SITE_ORIGIN}/events/${slug}`;
}

function eventCalendarDetails(event: EventCardPublic | EventPublic) {
  const summary = event.short_description || event.title;
  return `${summary}\n\n${eventPageUrl(event.slug)}`;
}

export function hasEventSchedule(event: Pick<EventCardPublic, "starts_at" | "ends_at">) {
  return Boolean(event.starts_at && event.ends_at);
}

export function googleCalendarUrl(event: EventCardPublic | EventPublic) {
  if (!hasEventSchedule(event) || !event.starts_at || !event.ends_at) return null;
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: event.title,
    dates: `${icsUtc(event.starts_at)}/${icsUtc(event.ends_at)}`,
    details: eventCalendarDetails(event),
    location: eventPageUrl(event.slug),
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export function outlookCalendarUrl(event: EventCardPublic | EventPublic) {
  if (!hasEventSchedule(event) || !event.starts_at || !event.ends_at) return null;
  const params = new URLSearchParams({
    path: "/calendar/action/compose",
    rru: "addevent",
    subject: event.title,
    startdt: new Date(event.starts_at).toISOString(),
    enddt: new Date(event.ends_at).toISOString(),
    body: eventCalendarDetails(event),
    location: eventPageUrl(event.slug),
  });
  return `https://outlook.live.com/calendar/0/deeplink/compose?${params.toString()}`;
}

export function downloadEventIcs(event: EventCardPublic | EventPublic) {
  if (!hasEventSchedule(event) || !event.starts_at || !event.ends_at) return;
  const url = eventPageUrl(event.slug);
  const description = eventCalendarDetails(event);
  const ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Analytic Sages//Events//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "BEGIN:VEVENT",
    `UID:event-${event.id}@analyticsages.io`,
    `DTSTAMP:${icsUtc(new Date().toISOString())}`,
    `DTSTART:${icsUtc(event.starts_at)}`,
    `DTEND:${icsUtc(event.ends_at)}`,
    `SUMMARY:${escapeIcs(event.title)}`,
    `DESCRIPTION:${escapeIcs(description)}`,
    `URL:${url}`,
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");

  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = `${event.slug}.ics`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(href);
}

function escapeIcs(value: string) {
  return value.replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/,/g, "\\,").replace(/;/g, "\\;");
}

export function splitEvents(events: EventCardPublic[]) {
  const upcoming: EventCardPublic[] = [];
  const past: EventCardPublic[] = [];
  for (const event of events) {
    if (event.lifecycle === "completed" || event.lifecycle === "cancelled") {
      past.push(event);
    } else {
      upcoming.push(event);
    }
  }
  upcoming.sort((a, b) => {
    if (!a.starts_at && !b.starts_at) return 0;
    if (!a.starts_at) return -1;
    if (!b.starts_at) return 1;
    return a.starts_at.localeCompare(b.starts_at);
  });
  past.sort((a, b) => (b.starts_at || "").localeCompare(a.starts_at || ""));
  return { upcoming, past };
}
