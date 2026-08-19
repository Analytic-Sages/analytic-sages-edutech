"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";
import { EventCard } from "@/components/events/event-card";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { ApiError, getAccessToken, getMyEvents, type EventRegistrationPublic } from "@/lib/api";

export function MyEventsContent() {
  const [rows, setRows] = useState<EventRegistrationPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authed, setAuthed] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!getAccessToken()) {
        if (!cancelled) {
          setAuthed(false);
          setLoading(false);
        }
        return;
      }
      try {
        const data = await getMyEvents();
        if (!cancelled) setRows(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load events.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <PageHeader
        title="My Events"
        description="Workshops and live sessions you registered for with this account."
      />

      {loading && (
        <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Loading your events…
        </div>
      )}

      {!loading && !authed && (
        <EmptyState
          icon={<CalendarDays className="size-5" />}
          title="Sign in to see your events"
          description="Event registrations are tied to your Analytic Sages account."
          action={{ label: "Sign in", href: "/login?next=/my-events" }}
        />
      )}

      {!loading && authed && error && (
        <EmptyState
          icon={<CalendarDays className="size-5" />}
          title="Couldn't load events"
          description={error}
          action={{ label: "Browse events", href: "/events" }}
        />
      )}

      {!loading && authed && !error && rows.length === 0 && (
        <EmptyState
          icon={<CalendarDays className="size-5" />}
          title="No event registrations yet"
          description="Browse free workshops and register with this account."
          action={{ label: "Browse events", href: "/events" }}
        />
      )}

      {!loading && authed && !error && rows.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((row) => (
            <EventCard key={row.id} event={row.event} />
          ))}
        </div>
      )}
    </div>
  );
}
