import type { Metadata } from "next";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { EventDetail } from "@/components/events/event-detail";
import { ApiError, getPublicEvent, type EventPublic } from "@/lib/api";
import { pageMetadata } from "@/lib/seo";

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

  return (
    <Suspense>
      <EventDetail initialEvent={event} />
    </Suspense>
  );
}
