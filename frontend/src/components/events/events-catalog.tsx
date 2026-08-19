"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";
import { EventCard } from "@/components/events/event-card";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { ApiError, listPublicEvents, type EventCardPublic } from "@/lib/api";
import { splitEvents } from "@/lib/events";

export function EventsCatalog() {
  const [events, setEvents] = useState<EventCardPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listPublicEvents()
      .then((data) => {
        if (!cancelled) setEvents(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load events.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const { upcoming, past } = splitEvents(events);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="Events"
        description="Free workshops, webinars, and live sessions. Browse without an account; register with the same Analytic Sages login you use for courses."
      />

      {loading && (
        <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Loading events…
        </div>
      )}

      {!loading && error && (
        <EmptyState
          icon={<CalendarDays className="size-5" />}
          title="Couldn't load events"
          description={error}
        />
      )}

      {!loading && !error && upcoming.length === 0 && past.length === 0 && (
        <EmptyState
          icon={<CalendarDays className="size-5" />}
          title="No events listed yet"
          description="Check back soon. Upcoming workshops and live sessions will appear here when they are published."
        />
      )}

      {!loading && !error && upcoming.length > 0 && (
        <section className="mb-12">
          <h2 className="mb-6 font-heading text-xl font-semibold">Upcoming</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {upcoming.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        </section>
      )}

      {!loading && !error && past.length > 0 && (
        <section>
          <h2 className="mb-6 font-heading text-xl font-semibold">Past events</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {past.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
