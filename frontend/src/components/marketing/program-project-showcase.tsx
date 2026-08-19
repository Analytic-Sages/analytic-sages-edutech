"use client";

import Image from "next/image";
import { TestimonialPlayer } from "@/components/marketing/testimonial-player";
import type { ProgramStudentWork } from "@/lib/program-pages";
import type { TestimonialVideo } from "@/lib/testimonials";
import { cn } from "@/lib/utils";

export function ProgramProjectShowcase({
  items,
  className,
}: {
  items: ProgramStudentWork[];
  className?: string;
}) {
  if (items.length === 0) return null;

  return (
    <div className={cn("grid gap-6 sm:grid-cols-2", className)}>
      {items.map((item) => (
        <figure
          key={item.id}
          className="overflow-hidden rounded-xl border bg-card shadow-card"
        >
          <div className="relative aspect-[4/3]">
            <Image
              src={item.image}
              alt={item.alt}
              fill
              className="object-cover"
              sizes="(max-width: 640px) 100vw, 50vw"
            />
          </div>
          <figcaption className="space-y-1 p-5">
            <p className="font-heading text-base font-semibold">{item.title}</p>
            <p className="text-sm leading-relaxed text-muted-foreground">{item.caption}</p>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

export function ProgramTestimonialGrid({
  items,
}: {
  items: TestimonialVideo[];
}) {
  if (items.length === 0) return null;

  const [featured, ...rest] = items;

  return (
    <div className="-mx-4 flex snap-x snap-mandatory gap-6 overflow-x-auto px-4 pb-2 sm:mx-0 sm:grid sm:grid-cols-1 sm:overflow-visible sm:px-0 lg:grid-cols-2 lg:gap-12">
      {featured && (
        <div className="min-w-[85%] snap-center sm:min-w-0">
          <TestimonialPlayer item={featured} featured />
        </div>
      )}
      {rest.map((item) => (
        <div key={item.id} className="min-w-[85%] snap-center sm:min-w-0">
          <TestimonialPlayer item={item} />
        </div>
      ))}
    </div>
  );
}
