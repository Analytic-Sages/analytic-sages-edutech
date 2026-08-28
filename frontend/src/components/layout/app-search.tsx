"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import {
  listPublicCohorts,
  listPublicEvents,
  listSelfPacedCourses,
  type EventCardPublic,
  type PublicCohortCard,
  type SelfPacedCourseCard,
} from "@/lib/api";
import { listInsights, type InsightCard } from "@/lib/insights";
import { listOpportunities, type OpportunityCard } from "@/lib/opportunities";
import { searchCatalog, searchKindLabel, type SearchHit } from "@/lib/site-search";
import { cn } from "@/lib/utils";

function useSearchIndex() {
  const [courses, setCourses] = useState<SelfPacedCourseCard[]>([]);
  const [cohorts, setCohorts] = useState<PublicCohortCard[]>([]);
  const [events, setEvents] = useState<EventCardPublic[]>([]);
  const [insights, setInsights] = useState<InsightCard[]>([]);
  const [opportunities, setOpportunities] = useState<OpportunityCard[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([
      listSelfPacedCourses(),
      listPublicCohorts(),
      listPublicEvents(),
      listInsights(),
      listOpportunities({ limit: 50 }),
    ]).then(([courseResult, cohortResult, eventResult, insightResult, opportunityResult]) => {
      if (cancelled) return;
      if (courseResult.status === "fulfilled") setCourses(courseResult.value);
      if (cohortResult.status === "fulfilled") setCohorts(cohortResult.value);
      if (eventResult.status === "fulfilled") setEvents(eventResult.value);
      if (insightResult.status === "fulfilled") setInsights(insightResult.value);
      if (opportunityResult.status === "fulfilled") setOpportunities(opportunityResult.value.items);
      setReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return { courses, cohorts, events, insights, opportunities, ready };
}

function SearchResults({
  query,
  hits,
  loading,
  onSelect,
}: {
  query: string;
  hits: SearchHit[];
  loading: boolean;
  onSelect: (hit: SearchHit) => void;
}) {
  if (query.trim().length < 2) {
    return <p className="px-3 py-4 text-sm text-muted-foreground">Type at least 2 characters.</p>;
  }
  if (loading) {
    return (
      <p className="flex items-center gap-2 px-3 py-4 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Searching…
      </p>
    );
  }
  if (hits.length === 0) {
    return (
      <p className="px-3 py-4 text-sm text-muted-foreground">
        No matches. Try a course, program, event, opportunity, or Insights topic.
      </p>
    );
  }
  return (
    <ul className="max-h-80 overflow-y-auto py-1">
      {hits.map((hit) => (
        <li key={hit.id}>
          <button
            type="button"
            onClick={() => onSelect(hit)}
            className="flex w-full flex-col gap-0.5 px-3 py-2.5 text-left hover:bg-muted"
          >
            <span className="text-[11px] font-semibold uppercase tracking-wide text-brand-orange">
              {searchKindLabel(hit.kind)}
            </span>
            <span className="text-sm font-medium">{hit.title}</span>
            <span className="line-clamp-2 text-xs text-muted-foreground">{hit.description}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function SearchField({
  autoFocus,
  className,
}: {
  autoFocus?: boolean;
  className?: string;
}) {
  const router = useRouter();
  const { courses, cohorts, events, insights, opportunities, ready } = useSearchIndex();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  const hits = useMemo(
    () => searchCatalog(query, { courses, cohorts, events, insights, opportunities }),
    [query, courses, cohorts, events, insights, opportunities]
  );

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (!wrapRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  function selectHit(hit: SearchHit) {
    setOpen(false);
    setQuery("");
    if (hit.href.startsWith("http")) {
      window.open(hit.href, "_blank", "noopener,noreferrer");
      return;
    }
    router.push(hit.href);
  }

  return (
    <div ref={wrapRef} className={cn("relative w-full", className)}>
      <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        value={query}
        autoFocus={autoFocus}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder="Search courses, programs, events…"
        className="h-9 pl-9"
        aria-label="Search courses, programs, and events"
      />
      {open && (
        <div className="absolute z-50 mt-1 w-full overflow-hidden rounded-lg border bg-background shadow-elevated">
          <SearchResults query={query} hits={hits} loading={!ready && query.trim().length >= 2} onSelect={selectHit} />
        </div>
      )}
    </div>
  );
}

export function AppSearch() {
  return (
    <>
      <SearchField className="hidden max-w-md flex-1 lg:block" />
      <Sheet>
        <SheetTrigger
          render={<Button variant="ghost" size="icon" className="lg:hidden" />}
        >
          <Search className="size-4" />
          <span className="sr-only">Search</span>
        </SheetTrigger>
        <SheetContent side="top" className="gap-0 p-4">
          <SheetTitle className="sr-only">Search</SheetTitle>
          <SearchField autoFocus className="mt-8" />
        </SheetContent>
      </Sheet>
    </>
  );
}
