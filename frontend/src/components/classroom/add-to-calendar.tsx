"use client";

import { useState } from "react";
import { CalendarPlus, Check, ChevronDown, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ApiError, getClassroomCalendarToken, type LiveSessionPublic } from "@/lib/api";
import {
  downloadAllSessionsIcs,
  downloadSessionIcs,
  googleSessionCalendarUrl,
  nextUpcomingSession,
  outlookSessionCalendarUrl,
} from "@/lib/classroom-calendar";
import { cn } from "@/lib/utils";

function CalendarLinks({ url, label }: { url: string; label: string }) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex w-full items-center px-1.5 py-1"
    >
      {label}
    </a>
  );
}

/** Per-session "Add to calendar" menu (Google / Outlook / .ics download). */
export function SessionCalendarMenu({
  session,
  className,
}: {
  session: LiveSessionPublic;
  className?: string;
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={<Button type="button" variant="outline" size="sm" className={cn("gap-2", className)} />}
      >
        <CalendarPlus className="size-4" />
        Add to calendar
        <ChevronDown className="size-4" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-56">
        <DropdownMenuItem className="p-0">
          <CalendarLinks url={googleSessionCalendarUrl(session)} label="Google Calendar" />
        </DropdownMenuItem>
        <DropdownMenuItem className="p-0">
          <CalendarLinks url={outlookSessionCalendarUrl(session)} label="Outlook" />
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => downloadSessionIcs(session)}>
          Apple Calendar / other (.ics)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/**
 * "Add all sessions" menu: bulk .ics download plus a subscribe link so Google /
 * Apple keep the schedule in sync (including reminders) as dates change.
 */
export function AllSessionsCalendarMenu({ sessions }: { sessions: LiveSessionPublic[] }) {
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const next = nextUpcomingSession(sessions);

  if (sessions.length === 0) return null;

  async function handleSubscribe() {
    setError(null);
    try {
      const feed = await getClassroomCalendarToken();
      if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(feed.webcal_url);
        setStatus("Subscribe link copied — paste it into your calendar app.");
      } else {
        window.location.assign(feed.webcal_url);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create your calendar link");
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger
            render={<Button type="button" variant="outline" size="sm" className="gap-2" />}
          >
            <CalendarPlus className="size-4" />
            Add all sessions
            <ChevronDown className="size-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="min-w-64">
            {next && (
              <>
                <DropdownMenuItem className="p-0">
                  <CalendarLinks
                    url={googleSessionCalendarUrl(next)}
                    label="Google Calendar (next session)"
                  />
                </DropdownMenuItem>
                <DropdownMenuItem className="p-0">
                  <CalendarLinks
                    url={outlookSessionCalendarUrl(next)}
                    label="Outlook (next session)"
                  />
                </DropdownMenuItem>
              </>
            )}
            <DropdownMenuItem onClick={() => downloadAllSessionsIcs(sessions)}>
              Download all ({sessions.length}) as .ics
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSubscribe}>
              <Copy className="mr-2 size-4" />
              Copy subscribe link (live updates)
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      {status && (
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <Check className="size-3.5" />
          {status}
        </span>
      )}
      {error && <span className="text-xs text-destructive">{error}</span>}
    </div>
  );
}