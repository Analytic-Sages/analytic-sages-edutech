"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, BookOpen, Clock3 } from "lucide-react";
import { listCourseCardPlacements } from "@/lib/api";
import { MANAGED_COURSE_CARDS } from "@/lib/course-card-registry";

type Props = { pageKey?: string };

export function CourseSidebar({ pageKey = "insights" }: Props) {
  const [cards, setCards] = useState<Array<(typeof MANAGED_COURSE_CARDS)[number]> | null>(null);

  useEffect(() => {
    let cancelled = false;
    listCourseCardPlacements(pageKey, "sidebar")
      .then((placements) => {
        if (cancelled) return;
        if (placements.length === 0) {
          setCards([...MANAGED_COURSE_CARDS]);
          return;
        }
        const byKey = new Map(MANAGED_COURSE_CARDS.map((card) => [card.key, card]));
        setCards(
          placements
            .filter((placement) => placement.visible)
            .sort((a, b) => a.position - b.position)
            .map((placement) => byKey.get(placement.card_key))
            .filter((card): card is (typeof MANAGED_COURSE_CARDS)[number] => Boolean(card)),
        );
      })
      .catch(() => {
        if (!cancelled) {
          // Keep the established cards visible if the placement service is temporarily unavailable.
          setCards([...MANAGED_COURSE_CARDS]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [pageKey]);

  if (cards === null) {
    return (
      <aside aria-label="Analytic Sages courses" className="space-y-4" aria-busy="true">
        <div className="flex items-center gap-2">
          <BookOpen className="size-4 text-brand-orange" />
          <h2 className="font-heading text-sm font-bold uppercase tracking-[0.14em]">Learn with us</h2>
        </div>
        <div className="space-y-3" role="status">
          <p className="text-sm text-muted-foreground">Loading course cards…</p>
          <div className="h-40 animate-pulse rounded-xl border bg-muted/40" />
          <div className="h-40 animate-pulse rounded-xl border bg-muted/40" />
        </div>
      </aside>
    );
  }

  return (
    <aside aria-label="Analytic Sages courses" className="space-y-4">
      <div className="flex items-center gap-2">
        <BookOpen className="size-4 text-brand-orange" />
        <h2 className="font-heading text-sm font-bold uppercase tracking-[0.14em]">Learn with us</h2>
      </div>
      {cards.map((course) => (
        <article key={course.key} className="overflow-hidden rounded-xl border border-border/70 bg-card shadow-sm">
          <Link href={course.href} className="group block">
            <div className="relative aspect-[16/9] overflow-hidden bg-brand-navy">
              <Image src={course.image} alt={course.title} fill sizes="(min-width: 1024px) 300px, 100vw" className="object-cover transition-transform duration-300 group-hover:scale-[1.03]" />
            </div>
            <div className="space-y-3 p-4">
              <span className="inline-flex rounded-full bg-brand-orange/10 px-2.5 py-1 text-[11px] font-semibold text-brand-orange">{course.label}</span>
              <h3 className="font-heading text-base font-bold leading-snug group-hover:text-brand-orange">{course.title}</h3>
              <p className="text-sm leading-5 text-muted-foreground">{course.description}</p>
              <div className="flex items-center justify-between gap-3 border-t pt-3 text-sm">
                <span className="inline-flex items-center gap-1.5 text-muted-foreground"><Clock3 className="size-3.5" />{course.duration}</span>
                <span className="font-semibold">{course.price}</span>
              </div>
              <span className="inline-flex items-center gap-1 text-sm font-semibold text-brand-orange">Explore course <ArrowUpRight className="size-3.5" /></span>
            </div>
          </Link>
        </article>
      ))}
      {cards.length === 0 ? <p className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">No courses are featured here right now.</p> : null}
    </aside>
  );
}
