"use client";

import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { EventCard } from "@/components/events/event-card";
import { ButtonLink } from "@/components/ui/button-link";
import { listPublicEvents, type EventCardPublic } from "@/lib/api";

export function HomeEventsSection() {
  const [events, setEvents] = useState<EventCardPublic[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    listPublicEvents({ upcoming: true, limit: 3 })
      .then((data) => {
        if (!cancelled) setEvents(data);
      })
      .catch(() => {
        if (!cancelled) setEvents([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!events || events.length === 0) return null;

  return (
    <section className="relative border-y bg-brand-surface/40 py-20 sm:py-28">
      <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-orange">
              Live events
            </p>
            <h2 className="mt-3 font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
              Upcoming workshops
            </h2>
            <p className="mt-3 max-w-xl text-lg text-muted-foreground">
              Free live sessions on YouTube. Register with your Analytic Sages account to get the
              join link.
            </p>
          </div>
          <ButtonLink href="/events" variant="outline" className="shrink-0">
            All events
            <ArrowRight className="ml-2 size-4" />
          </ButtonLink>
        </div>
        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {events.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      </div>
    </section>
  );
}
