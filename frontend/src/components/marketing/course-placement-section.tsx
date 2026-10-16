"use client";

/* eslint-disable @next/next/no-img-element */

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, Loader2 } from "lucide-react";
import { getPublicCoursePlacements, type CoursePlacementRow } from "@/lib/api";

type Props = { pageKey: string; sectionKey?: string; title?: string; description?: string };

export function CoursePlacementSection({ pageKey, sectionKey = "main", title, description }: Props) {
  const [items, setItems] = useState<CoursePlacementRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getPublicCoursePlacements(pageKey, sectionKey)
      .then((rows) => { if (!cancelled) setItems(rows); })
      .catch(() => { if (!cancelled) setItems([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [pageKey, sectionKey]);

  if (loading) return <section aria-label={title ?? "Featured courses"} className="mx-auto max-w-screen-2xl px-4 py-8 sm:px-6 lg:px-10"><div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" />Loading courses…</div></section>;
  if (items.length === 0) return null;

  return (
    <section className="mx-auto w-full max-w-screen-2xl px-4 py-14 sm:px-6 lg:px-10">
      {(title || description) && <div className="mb-7 max-w-2xl">{title && <h2 className="font-heading text-2xl font-bold tracking-tight sm:text-3xl">{title}</h2>}{description && <p className="mt-2 text-muted-foreground">{description}</p>}</div>}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {items.map((item) => (
          <Link key={item.course_id} href={`/courses/${item.course_slug}`} className="group overflow-hidden rounded-xl border bg-card transition hover:-translate-y-0.5 hover:shadow-md">
            <div className="aspect-[16/9] overflow-hidden bg-muted">
              {item.thumbnail ? <><img src={item.thumbnail} alt="" loading="lazy" className="size-full object-cover transition-transform group-hover:scale-[1.02]" /></> : <div className="flex size-full items-center justify-center"><BookOpen className="size-8 text-muted-foreground" /></div>}
            </div>
            <div className="p-5"><p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">{item.delivery_type.replace(/_/g, " ")}</p><h3 className="mt-2 line-clamp-2 font-heading text-lg font-semibold">{item.title}</h3><span className="mt-4 inline-flex items-center gap-2 text-sm font-medium">View course <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" /></span></div>
          </Link>
        ))}
      </div>
    </section>
  );
}
