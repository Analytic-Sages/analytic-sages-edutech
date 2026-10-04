/**
 * Shared iCalendar (RFC 5545) helpers.
 *
 * Used by both the Events feature and the Live Classroom so "Add to calendar"
 * behaves identically everywhere. Kept dependency-free and pure.
 */

export const DEFAULT_REMINDER_MINUTES = 15;

export type IcsEventInput = {
  uid: string;
  startsAt: string;
  endsAt: string;
  summary: string;
  description?: string;
  location?: string;
  url?: string;
  /** Minutes before start for the pop-up reminder. 0 disables the alarm. */
  reminderMinutes?: number;
};

export type CalendarLinkInput = {
  title: string;
  startsAt: string;
  endsAt: string;
  details?: string;
  location?: string;
};

/** UTC basic-format timestamp, e.g. 20261005T170000Z. */
export function icsUtc(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

export function escapeIcs(value: string): string {
  return value
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r?\n/g, "\\n");
}

function byteLength(value: string): number {
  return new TextEncoder().encode(value).length;
}

/** Fold content lines to the 75-octet limit RFC 5545 requires. */
function foldLine(line: string): string {
  if (byteLength(line) <= 75) return line;
  const parts: string[] = [];
  let current = line;
  while (byteLength(current) > 75) {
    let cut = 75;
    while (cut > 0 && byteLength(current.slice(0, cut)) > 75) cut -= 1;
    parts.push(current.slice(0, cut));
    current = ` ${current.slice(cut)}`;
  }
  parts.push(current);
  return parts.join("\r\n");
}

export function buildCalendar(
  events: IcsEventInput[],
  options?: { calendarName?: string; prodId?: string }
): string {
  const stamp = icsUtc(new Date());
  const lines: string[] = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    `PRODID:${options?.prodId ?? "-//Analytic Sages//Classroom//EN"}`,
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
  ];
  if (options?.calendarName) {
    lines.push(`X-WR-CALNAME:${escapeIcs(options.calendarName)}`);
  }
  lines.push("X-PUBLISHED-TTL:PT1H");

  for (const event of events) {
    const reminder = event.reminderMinutes ?? DEFAULT_REMINDER_MINUTES;
    lines.push(
      "BEGIN:VEVENT",
      `UID:${event.uid}`,
      `DTSTAMP:${stamp}`,
      `DTSTART:${icsUtc(event.startsAt)}`,
      `DTEND:${icsUtc(event.endsAt)}`,
      `SUMMARY:${escapeIcs(event.summary)}`
    );
    if (event.description) lines.push(`DESCRIPTION:${escapeIcs(event.description)}`);
    if (event.location) lines.push(`LOCATION:${escapeIcs(event.location)}`);
    if (event.url) lines.push(`URL:${event.url}`);
    if (reminder > 0) {
      lines.push(
        "BEGIN:VALARM",
        `TRIGGER:-PT${reminder}M`,
        "ACTION:DISPLAY",
        `DESCRIPTION:${escapeIcs(event.summary)}`,
        "END:VALARM"
      );
    }
    lines.push("END:VEVENT");
  }

  lines.push("END:VCALENDAR");
  return `${lines.map(foldLine).join("\r\n")}\r\n`;
}

/** Trigger a client-side download of an .ics payload. */
export function downloadIcsFile(filename: string, ics: string): void {
  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(href);
}

export function googleCalendarUrl(input: CalendarLinkInput): string {
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: input.title,
    dates: `${icsUtc(input.startsAt)}/${icsUtc(input.endsAt)}`,
  });
  if (input.details) params.set("details", input.details);
  if (input.location) params.set("location", input.location);
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export function outlookCalendarUrl(input: CalendarLinkInput): string {
  const params = new URLSearchParams({
    path: "/calendar/action/compose",
    rru: "addevent",
    subject: input.title,
    startdt: new Date(input.startsAt).toISOString(),
    enddt: new Date(input.endsAt).toISOString(),
  });
  if (input.details) params.set("body", input.details);
  if (input.location) params.set("location", input.location);
  return `https://outlook.live.com/calendar/0/deeplink/compose?${params.toString()}`;
}