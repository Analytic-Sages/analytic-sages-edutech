"use client";

import { useRef, useState } from "react";
import Image from "next/image";
import { ChevronLeft, ChevronRight, Play } from "lucide-react";
import { ButtonLink } from "@/components/ui/button-link";
import {
  toYouTubeEmbedSrc,
  toYouTubeThumbnail,
  type TestimonialVideo,
} from "@/lib/testimonials";
import { cn } from "@/lib/utils";

export function ProgramTestimonialCarousel({
  items,
  moreUrl,
}: {
  items: TestimonialVideo[];
  moreUrl: string;
}) {
  const scrollerRef = useRef<HTMLDivElement>(null);
  const [playingId, setPlayingId] = useState<string | null>(null);

  const visible = items.filter((item) => item.youtubeUrl.trim() || item.name);
  if (visible.length === 0) return null;

  function scrollByCard(direction: -1 | 1) {
    const node = scrollerRef.current;
    if (!node) return;
    const card = node.querySelector("[data-testimonial-card]");
    const width = card instanceof HTMLElement ? card.offsetWidth + 24 : node.clientWidth * 0.8;
    node.scrollBy({ left: direction * width, behavior: "smooth" });
  }

  return (
    <div className="relative">
      <button
        type="button"
        aria-label="Previous testimonials"
        onClick={() => scrollByCard(-1)}
        className="absolute top-1/3 left-0 z-10 hidden size-10 -translate-x-1/2 items-center justify-center rounded-full border bg-white shadow-card sm:flex"
      >
        <ChevronLeft className="size-5" />
      </button>
      <button
        type="button"
        aria-label="Next testimonials"
        onClick={() => scrollByCard(1)}
        className="absolute top-1/3 right-0 z-10 hidden size-10 translate-x-1/2 items-center justify-center rounded-full border bg-white shadow-card sm:flex"
      >
        <ChevronRight className="size-5" />
      </button>

      <div
        ref={scrollerRef}
        className="-mx-4 flex snap-x snap-mandatory gap-6 overflow-x-auto px-4 pb-4 sm:mx-0 sm:px-0"
      >
        {visible.map((item) => {
          const embedSrc = toYouTubeEmbedSrc(item.youtubeUrl);
          const thumb = toYouTubeThumbnail(item.youtubeUrl);
          const playing = playingId === item.id && embedSrc;

          return (
            <article
              key={item.id}
              data-testimonial-card
              className="w-[85%] shrink-0 snap-center sm:w-[calc((100%-3rem)/3)]"
            >
              <div className="relative aspect-video overflow-hidden rounded-xl border bg-brand-navy">
                {playing ? (
                  <iframe
                    src={`${embedSrc}?autoplay=1`}
                    title={`${item.name}: Analytic Sages testimonial`}
                    className="absolute inset-0 size-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowFullScreen
                  />
                ) : (
                  <button
                    type="button"
                    onClick={() => embedSrc && setPlayingId(item.id)}
                    className="group absolute inset-0"
                    aria-label={`Play testimonial from ${item.name}`}
                  >
                    {thumb ? (
                      <Image
                        src={thumb}
                        alt=""
                        fill
                        className="object-cover"
                        sizes="(max-width: 640px) 85vw, 33vw"
                      />
                    ) : (
                      <div className="absolute inset-0 bg-brand-navy" />
                    )}
                    <span
                      className={cn(
                        "absolute inset-0 bg-black/25 transition-colors group-hover:bg-black/35",
                      )}
                    />
                    <span className="absolute inset-0 flex items-center justify-center">
                      <span className="flex size-14 items-center justify-center rounded-full bg-white text-brand-navy shadow-elevated sm:size-16">
                        <Play className="size-6 fill-current sm:size-7" />
                      </span>
                    </span>
                  </button>
                )}
              </div>
              <p className="mt-3 font-heading text-sm font-bold sm:text-base">{item.name}</p>
              <p className="text-sm text-brand-orange">{item.role}</p>
            </article>
          );
        })}
      </div>

      <div className="mt-8 flex justify-center">
        <ButtonLink
          href={moreUrl}
          target="_blank"
          rel="noopener noreferrer"
          size="lg"
          className="h-12 rounded-full bg-brand-orange px-8 text-base text-white hover:bg-brand-orange/90"
        >
          Watch More Testimonials
          <span className="ml-2 flex size-6 items-center justify-center rounded-full bg-white text-brand-orange">
            <ChevronRight className="size-4" />
          </span>
        </ButtonLink>
      </div>
    </div>
  );
}
