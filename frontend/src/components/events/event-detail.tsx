"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { CalendarDays, Clock, UserRound } from "lucide-react";
import { EventKeepLearning } from "@/components/events/event-keep-learning";
import { EventRegisterCta } from "@/components/events/event-register-cta";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { ButtonAnchor } from "@/components/ui/button-anchor";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getPublicEvent, type EventPublic } from "@/lib/api";
import {
  eventLifecycleLabel,
  eventTypeLabel,
  eventVenueSummary,
  formatEventWhen,
  isBundledEventCover,
  resolveEventCoverSrc,
  SESSION_RECORDING_CTA,
} from "@/lib/events";

type Props = {
  initialEvent: EventPublic;
};

export function EventDetail({ initialEvent }: Props) {
  const [event, setEvent] = useState(initialEvent);

  useEffect(() => {
    let cancelled = false;
    getPublicEvent(initialEvent.slug)
      .then((next) => {
        if (!cancelled) setEvent(next);
      })
      .catch(() => {
        /* keep SSR payload */
      });
    return () => {
      cancelled = true;
    };
  }, [initialEvent.slug]);

  const cover = resolveEventCoverSrc(event.cover_image);

  return (
    <div className="pb-16">
      <div className="border-b bg-brand-surface">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
            <div>
              <PageHeader
                breadcrumbs={[{ label: "Events", href: "/events" }, { label: event.title }]}
                title={event.title}
                description={event.short_description}
              />
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Badge>{eventTypeLabel(event.event_type)}</Badge>
                <Badge variant={event.lifecycle === "live" ? "default" : "outline"}>
                  {eventLifecycleLabel(event.lifecycle)}
                </Badge>
                {event.is_free && <Badge className="bg-brand-orange text-white">Free</Badge>}
              </div>
              <div className="mt-6 space-y-2 text-sm text-muted-foreground">
                <p className="flex items-center gap-2">
                  <CalendarDays className="size-4" />
                  {formatEventWhen(event)}
                </p>
                {event.host_name && (
                  <p className="flex items-center gap-2">
                    <UserRound className="size-4" />
                    Hosted by {event.host_name}
                  </p>
                )}
                <p className="flex items-center gap-2">
                  <Clock className="size-4 shrink-0" />
                  <span>{eventVenueSummary(event)}</span>
                </p>
                {event.can_watch_recording && event.recording_url ? (
                  <div className="pt-2">
                    <ButtonAnchor
                      href={event.recording_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-brand-orange text-white hover:bg-brand-orange/90"
                    >
                      {SESSION_RECORDING_CTA}
                    </ButtonAnchor>
                  </div>
                ) : null}
              </div>
            </div>
            {cover && (
              <div className="relative aspect-video overflow-hidden rounded-2xl border bg-background shadow-card">
                {isBundledEventCover(cover) ? (
                  <Image
                    src={cover}
                    alt={event.title}
                    fill
                    className="object-cover"
                    sizes="(max-width: 1024px) 100vw, 50vw"
                  />
                ) : (
                  // eslint-disable-next-line @next/next/no-img-element -- uploaded media and remote covers
                  <img src={cover} alt={event.title} className="size-full object-cover" />
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-3 lg:px-8">
        <div className="space-y-8 lg:col-span-2">
          <section>
            <h2 className="font-heading text-xl font-semibold">About this event</h2>
            <p className="mt-3 whitespace-pre-line text-muted-foreground">{event.description}</p>
          </section>
          {event.learn_topics.length > 0 && (
            <section>
              <h2 className="font-heading text-xl font-semibold">What you will cover</h2>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-muted-foreground">
                {event.learn_topics.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          )}
          {event.audience.length > 0 && (
            <section>
              <h2 className="font-heading text-xl font-semibold">Who it is for</h2>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-muted-foreground">
                {event.audience.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          )}
          {event.prerequisites && (
            <section>
              <h2 className="font-heading text-xl font-semibold">Prerequisites</h2>
              <p className="mt-3 text-muted-foreground">{event.prerequisites}</p>
            </section>
          )}
        </div>
        <aside className="space-y-4">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="text-lg">Registration</CardTitle>
            </CardHeader>
            <CardContent>
              <EventRegisterCta event={event} onUpdated={setEvent} />
            </CardContent>
          </Card>
          <EventKeepLearning relatedCourseSlug={event.related_course_slug} />
        </aside>
      </div>
    </div>
  );
}
