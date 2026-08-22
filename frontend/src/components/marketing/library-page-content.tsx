"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { EventCard } from "@/components/events/event-card";
import { SectionBackground } from "@/components/marketing/section-background";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { siteConfig } from "@/config/site";
import { listPublicEvents, type EventCardPublic } from "@/lib/api";
import {
  LIBRARY_CATEGORIES,
  LIBRARY_CATEGORY_LABELS,
  STATIC_LIBRARY_ITEMS,
  libraryItemsForCategory,
  parseLibraryCategory,
  type LibraryCategory,
  type LibraryItem,
} from "@/lib/library";
import { cn } from "@/lib/utils";

const eyebrowClass =
  "text-lg font-bold uppercase tracking-[0.12em] text-brand-orange sm:text-xl";

function eventMatchesCategory(event: EventCardPublic, category: LibraryCategory | "all") {
  if (category === "all") return event.event_type === "workshop" || event.event_type === "webinar";
  if (category === "workshops") return event.event_type === "workshop";
  if (category === "webinars") return event.event_type === "webinar";
  return false;
}

function LibraryResourceCard({ item }: { item: LibraryItem }) {
  const external = item.href.startsWith("http");
  const thumb = item.thumbnail;

  return (
    <Card className="overflow-hidden rounded-2xl shadow-card transition-all duration-300 hover:-translate-y-1.5 hover:shadow-float">
      <div className="relative aspect-video overflow-hidden bg-brand-navy">
        {thumb ? (
          <Image
            src={thumb}
            alt={item.title}
            fill
            className="object-cover"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-brand-navy to-brand-navy/70" />
        )}
        <div className="absolute top-3 left-3 flex flex-wrap gap-2">
          <Badge className="bg-brand-orange text-white">
            {LIBRARY_CATEGORY_LABELS[item.category]}
          </Badge>
          {item.comingSoon ? (
            <Badge className="bg-brand-navy text-white">Coming soon</Badge>
          ) : item.badge ? (
            <Badge className="bg-brand-navy text-white">{item.badge}</Badge>
          ) : null}
        </div>
      </div>
      <CardHeader>
        <CardTitle className="line-clamp-2 text-xl leading-snug">
          {external ? (
            <a href={item.href} target="_blank" rel="noopener noreferrer">
              {item.title}
            </a>
          ) : (
            <Link href={item.href}>{item.title}</Link>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="line-clamp-3 text-base text-muted-foreground">{item.description}</p>
        {item.duration ? <p className="text-sm text-muted-foreground">{item.duration}</p> : null}
      </CardContent>
      <CardFooter className="justify-end border-t">
        <ButtonLink
          href={item.href}
          size="sm"
          className="bg-brand-orange text-white hover:bg-brand-orange/90"
          {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
        >
          {item.cta}
          {external ? <ArrowUpRight className="ml-1 size-3.5" /> : null}
        </ButtonLink>
      </CardFooter>
    </Card>
  );
}

export function LibraryPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const category = parseLibraryCategory(searchParams.get("category"));
  const [events, setEvents] = useState<EventCardPublic[]>([]);

  useEffect(() => {
    let cancelled = false;
    listPublicEvents()
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

  function setCategory(value: LibraryCategory | "all") {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "all") params.delete("category");
    else params.set("category", value);
    const query = params.toString();
    router.replace(query ? `/library?${query}` : "/library", { scroll: false });
  }

  const hideWebinarPlaceholder = events.some((event) => event.event_type === "webinar");
  const resources = useMemo(() => {
    return libraryItemsForCategory(STATIC_LIBRARY_ITEMS, category).filter(
      (item) => item.id !== "webinars:recordings" || !hideWebinarPlaceholder,
    );
  }, [category, hideWebinarPlaceholder]);
  const liveEvents = events.filter((event) => eventMatchesCategory(event, category));
  const showEvents = category === "all" || category === "workshops" || category === "webinars";
  const empty = resources.length === 0 && (!showEvents || liveEvents.length === 0);

  return (
    <div className="relative overflow-hidden pb-16">
      <SectionBackground variant="glow" />
      <div className="relative mx-auto max-w-screen-2xl px-4 py-12 sm:px-6 sm:py-16 lg:px-10">
        <div className="max-w-3xl">
          <p className={eyebrowClass}>Learning Library</p>
          <h1 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Courses, tutorials, and resources.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
            Structured courses stay in the catalog. This library is for free lessons, research,
            career sessions, and event recordings so the course list stays clear.
          </p>
          <p className="mt-4 text-sm text-muted-foreground">
            Want the full enrollable catalog?{" "}
            <ButtonLink href="/courses" variant="link" className="h-auto px-0 text-brand-orange">
              Browse self-paced courses
            </ButtonLink>
            {" · "}
            <a
              href={siteConfig.links.youtube}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-brand-orange hover:underline"
            >
              YouTube channel
            </a>
          </p>
        </div>

        <div className="mt-8 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setCategory("all")}
            className={cn(
              "rounded-full border px-4 py-2 text-sm font-semibold",
              category === "all"
                ? "border-brand-navy bg-brand-navy text-white"
                : "border-border bg-background text-foreground hover:border-brand-orange/50",
            )}
          >
            All
          </button>
          {LIBRARY_CATEGORIES.map((id) => (
            <button
              key={id}
              type="button"
              onClick={() => setCategory(id)}
              className={cn(
                "rounded-full border px-4 py-2 text-sm font-semibold",
                category === id
                  ? "border-brand-navy bg-brand-navy text-white"
                  : "border-border bg-background text-foreground hover:border-brand-orange/50",
              )}
            >
              {LIBRARY_CATEGORY_LABELS[id]}
            </button>
          ))}
        </div>

        {empty ? (
          <p className="mt-12 text-muted-foreground">Nothing in this category yet.</p>
        ) : (
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {resources.map((item) => (
              <LibraryResourceCard key={item.id} item={item} />
            ))}
            {showEvents
              ? liveEvents.map((event) => <EventCard key={event.id} event={event} />)
              : null}
          </div>
        )}
      </div>
    </div>
  );
}
