import Image from "next/image";
import Link from "next/link";
import { CalendarDays, UserRound } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import type { EventCardPublic } from "@/lib/api";
import { eventLifecycleLabel, eventTypeLabel, formatEventWhen } from "@/lib/events";

function Cover({ src, alt }: { src: string | null; alt: string }) {
  if (src && src.startsWith("/")) {
    return (
      <Image
        src={src}
        alt={alt}
        fill
        className="object-cover"
        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
      />
    );
  }
  return <div className="size-full bg-brand-navy/10" aria-hidden />;
}

export function EventCard({ event }: { event: EventCardPublic }) {
  const href = `/events/${event.slug}`;
  const live = event.lifecycle === "live";

  return (
    <Card className="overflow-hidden rounded-2xl shadow-card transition-all duration-300 hover:-translate-y-1.5 hover:shadow-float">
      <div className="relative aspect-video overflow-hidden bg-brand-surface">
        <Cover src={event.cover_image} alt={event.title} />
        <div className="absolute top-3 left-3 flex flex-wrap gap-2">
          <Badge className="bg-brand-orange text-white">{event.is_free ? "Free" : eventTypeLabel(event.event_type)}</Badge>
          {live && <Badge className="bg-brand-navy text-white">Live now</Badge>}
          {event.lifecycle === "coming_soon" && (
            <Badge className="bg-brand-navy text-white">Coming soon</Badge>
          )}
        </div>
      </div>
      <CardHeader>
        <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">
          {eventTypeLabel(event.event_type)}
        </p>
        <CardTitle className="line-clamp-2 text-xl leading-snug">
          <Link href={href}>{event.title}</Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="line-clamp-3 text-base text-muted-foreground">{event.short_description}</p>
        <div className="space-y-1.5 text-sm text-muted-foreground">
          <p className="inline-flex items-center gap-1.5">
            <CalendarDays className="size-3.5 shrink-0" />
            {formatEventWhen(event)}
          </p>
          {event.host_name && (
            <p className="inline-flex items-center gap-1.5">
              <UserRound className="size-3.5 shrink-0" />
              {event.host_name}
            </p>
          )}
        </div>
      </CardContent>
      <CardFooter className="justify-between border-t">
        <span className="text-sm font-medium text-brand-navy dark:text-brand-orange">
          {event.registered ? "Registered" : eventLifecycleLabel(event.lifecycle)}
        </span>
        <ButtonLink href={href} size="sm" className="bg-brand-orange text-white hover:bg-brand-orange/90">
          {event.registered ? "View event" : "View details"}
        </ButtonLink>
      </CardFooter>
    </Card>
  );
}
