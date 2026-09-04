import type { Metadata } from "next";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { EventDetail } from "@/components/events/event-detail";
import { JsonLd } from "@/components/seo/json-ld";
import { ApiError, getPublicEvent, type EventPublic } from "@/lib/api";
import { breadcrumbJsonLd, eventJsonLd, pageMetadata } from "@/lib/seo";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ slug: string }> };

async function loadEvent(slug: string): Promise<EventPublic | null> {
  try {
    return await getPublicEvent(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const event = await loadEvent(slug);
  if (!event) return { title: "Event" };
  return pageMetadata({
    title: event.seo_title || event.title,
    description: event.seo_description || event.short_description || event.description,
    path: `/events/${event.slug}`,
    image: event.cover_image,
  });
}

export default async function EventPage({ params }: Props) {
  const { slug } = await params;
  const event = await loadEvent(slug);
  if (!event) notFound();

  const description =
    event.seo_description || event.short_description || event.description;

  return (
    <>
      <JsonLd
        data={eventJsonLd({
          name: event.title,
          description,
          path: `/events/${event.slug}`,
          image: event.cover_image,
          startDate: event.starts_at,
          endDate: event.ends_at,
          isFree: event.is_free,
          price: event.price,
          currency: event.currency,
          eventStatus: event.cancelled ? "EventCancelled" : "EventScheduled",
        })}
      />
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "Events", path: "/events" },
          { name: event.title, path: `/events/${event.slug}` },
        ])}
      />
      <Suspense>
        <EventDetail initialEvent={event} />
      </Suspense>
    </>
  );
}
