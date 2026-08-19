"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CalendarPlus, ChevronDown, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ButtonAnchor } from "@/components/ui/button-anchor";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ApiError,
  getAccessToken,
  getPublicEvent,
  joinEvent,
  registerForEvent,
  type EventPublic,
} from "@/lib/api";
import {
  downloadEventIcs,
  googleCalendarUrl,
  hasEventSchedule,
  outlookCalendarUrl,
  registerLoginPath,
} from "@/lib/events";

type Props = {
  event: EventPublic;
  onUpdated?: (event: EventPublic) => void;
};

export function EventRegisterCta({ event, onUpdated }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const registerLock = useRef(false);

  useEffect(() => {
    if (searchParams.get("register") !== "1") return;
    if (!getAccessToken()) return;
    if (event.registered) {
      router.replace(`/events/${event.slug}`);
      return;
    }
    if (registerLock.current) return;
    registerLock.current = true;
    setWorking(true);
    registerForEvent(event.slug, "login-return")
      .then(async () => {
        const next = await getPublicEvent(event.slug);
        onUpdated?.(next);
        router.replace(`/events/${event.slug}`);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.detail : "Could not complete registration.");
        registerLock.current = false;
      })
      .finally(() => setWorking(false));
  }, [event.registered, event.slug, onUpdated, router, searchParams]);

  async function handleRegister() {
    if (!getAccessToken()) {
      router.push(registerLoginPath(event.slug));
      return;
    }
    setWorking(true);
    setError(null);
    try {
      await registerForEvent(event.slug, "event-page");
      const next = await getPublicEvent(event.slug);
      onUpdated?.(next);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not complete registration.");
    } finally {
      setWorking(false);
    }
  }

  async function handleJoin() {
    setWorking(true);
    setError(null);
    try {
      const result = await joinEvent(event.slug);
      window.open(result.youtube_live_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not open the live link.");
    } finally {
      setWorking(false);
    }
  }

  const primary = (() => {
    if (event.lifecycle === "cancelled") {
      return (
        <Button disabled className="w-full">
          Event cancelled
        </Button>
      );
    }
    if (event.lifecycle === "coming_soon") {
      return (
        <Button disabled className="w-full">
          Coming soon
        </Button>
      );
    }
    if (event.can_watch_recording && event.recording_url) {
      return (
                <ButtonAnchor
                  href={event.recording_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full bg-brand-orange text-white hover:bg-brand-orange/90"
                >
                  Watch recording
                </ButtonAnchor>
      );
    }
    if (event.lifecycle === "completed") {
      return (
        <Button disabled className="w-full">
          Event ended
        </Button>
      );
    }
    if (event.can_join) {
      return (
        <Button
          onClick={handleJoin}
          disabled={working}
          className="w-full bg-brand-orange text-white hover:bg-brand-orange/90"
        >
          {working ? <Loader2 className="size-4 animate-spin" /> : "Join event"}
        </Button>
      );
    }
    if (event.registered) {
      return (
        <Button disabled className="w-full bg-brand-navy text-white">
          You&apos;re registered
        </Button>
      );
    }
    if (event.can_register) {
      return (
        <Button
          onClick={handleRegister}
          disabled={working}
          className="w-full bg-brand-orange text-white hover:bg-brand-orange/90"
        >
          {working ? <Loader2 className="size-4 animate-spin" /> : "Register for Free"}
        </Button>
      );
    }
    return (
      <Button disabled className="w-full">
        Registration closed
      </Button>
    );
  })();

  return (
    <div className="space-y-3">
      {primary}
      {event.registered && event.lifecycle !== "cancelled" && hasEventSchedule(event) && (
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button type="button" variant="outline" className="w-full gap-2" />
            }
          >
            <CalendarPlus className="size-4" />
            Add to calendar
            <ChevronDown className="size-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="min-w-56">
            <DropdownMenuItem className="p-0">
              <a
                href={googleCalendarUrl(event) ?? "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center px-1.5 py-1"
              >
                Google Calendar
              </a>
            </DropdownMenuItem>
            <DropdownMenuItem className="p-0">
              <a
                href={outlookCalendarUrl(event) ?? "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center px-1.5 py-1"
              >
                Outlook
              </a>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => downloadEventIcs(event)}>
              Apple Calendar / other (.ics)
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
      {event.lifecycle === "coming_soon" && (
        <p className="text-xs text-muted-foreground">
          Date to be announced. Registration will open here when the session is scheduled.
        </p>
      )}
      {!event.registered && event.can_register && (
        <p className="text-xs text-muted-foreground">
          Use your Analytic Sages account. Guests can browse; registration requires sign-in.
        </p>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
