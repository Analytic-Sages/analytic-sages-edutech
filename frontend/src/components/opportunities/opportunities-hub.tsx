"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Briefcase, Loader2, Search } from "lucide-react";
import { OpportunityRow } from "@/components/opportunities/opportunity-card";
import { EmptyState } from "@/components/shared/empty-state";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";
import {
  getOpportunityFilters,
  listOpportunities,
  TYPE_ROUTES,
  type OpportunityCard,
  type OpportunityFilters,
  type OpportunityType,
  type LocationRegion,
  type WorkplaceType,
} from "@/lib/opportunities";
import { cn } from "@/lib/utils";

type Props = {
  initialType?: OpportunityType;
  title?: string;
  description?: string;
};

export function OpportunitiesHub({
  initialType,
  title = "Find your next opportunity",
  description = "Curated opportunities for people building careers in blockchain data, AI, quantitative finance and onchain research.",
}: Props) {
  const searchParams = useSearchParams();
  const skillFromUrl = searchParams.get("skill") || "";

  const [filters, setFilters] = useState<OpportunityFilters | null>(null);
  const [items, setItems] = useState<OpportunityCard[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [careerPath, setCareerPath] = useState("");
  /** null = follow URL; string = user override (including ""). */
  const [skillOverride, setSkillOverride] = useState<string | null>(null);
  const skill = skillOverride ?? skillFromUrl;
  const [workplace, setWorkplace] = useState<WorkplaceType | "">("");
  const [employment, setEmployment] = useState("");
  const [region, setRegion] = useState<LocationRegion | "">("");
  const [sort, setSort] = useState<"newest" | "deadline" | "featured" | "closing_soon" | "matched">(
    "newest",
  );
  const [weekAgoMs] = useState(() => Date.now() - 7 * 24 * 60 * 60 * 1000);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(search.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    getOpportunityFilters()
      .then(setFilters)
      .catch(() => setFilters(null));
  }, []);

  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) setLoading(true);
    });
    listOpportunities({
      q: debounced || undefined,
      opportunity_type: initialType,
      career_path: careerPath || undefined,
      skill: skill || undefined,
      workplace_type: workplace || undefined,
      employment_type: employment || undefined,
      region: region || undefined,
      sort,
      limit: 30,
    })
      .then((data) => {
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.detail : "Could not load opportunities.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [debounced, initialType, careerPath, skill, workplace, employment, region, sort]);

  const typeCounts = useMemo(() => {
    const map = new Map((filters?.types || []).map((item) => [item.value, item.count]));
    return map;
  }, [filters]);

  const newThisWeek = useMemo(() => {
    return items.filter((item) => {
      if (!item.published_at) return false;
      return new Date(item.published_at).getTime() >= weekAgoMs;
    }).length;
  }, [items, weekAgoMs]);

  return (
    <div className="bg-[#F7F9FC] dark:bg-background">
      <div className="border-b border-border/60 bg-gradient-to-br from-[#0B1F3A] via-[#122A4A] to-[#0B1F3A] text-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
          <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-orange">
            Opportunities Hub
          </p>
          <h1 className="mt-3 max-w-3xl font-heading text-3xl font-bold tracking-tight sm:text-5xl">
            {title}
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-white/75 sm:text-lg">
            {description}
          </p>
          {!loading && !error && total > 0 ? (
            <p className="mt-6 text-sm text-white/65">
              {total} active {total === 1 ? "opportunity" : "opportunities"}
              {newThisWeek > 0
                ? ` · ${newThisWeek} new in this result set this week`
                : ""}
            </p>
          ) : null}
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-4">
          <div className="relative max-w-xl">
            <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search opportunities, companies or skills"
              className="h-11 border-border/80 bg-card pl-9"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              href="/opportunities"
              className={cn(
                "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
                !initialType
                  ? "border-brand-navy bg-brand-navy text-white"
                  : "border-border bg-card hover:border-brand-orange hover:text-brand-orange",
              )}
            >
              All
            </Link>
            {TYPE_ROUTES.map((item) => (
              <Link
                key={item.type}
                href={item.href}
                className={cn(
                  "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
                  initialType === item.type
                    ? "border-brand-navy bg-brand-navy text-white"
                    : "border-border bg-card hover:border-brand-orange hover:text-brand-orange",
                )}
              >
                {item.label}
                {typeCounts.has(item.type) ? (
                  <span className="ml-1.5 text-xs opacity-70">{typeCounts.get(item.type)}</span>
                ) : null}
              </Link>
            ))}
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <select
              className="h-10 rounded-lg border border-border/80 bg-card px-3 text-sm sm:w-52"
              value={careerPath}
              onChange={(event) => setCareerPath(event.target.value)}
            >
              <option value="">All career paths</option>
              {(filters?.career_paths || []).map((item) => (
                <option key={item.id} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </select>
            <select
              className="h-10 rounded-lg border border-border/80 bg-card px-3 text-sm sm:w-48"
              value={workplace}
              onChange={(event) => setWorkplace(event.target.value as WorkplaceType | "")}
            >
              <option value="">Any workplace</option>
              {(filters?.workplace_types || []).map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
            <select
              className="h-10 rounded-lg border border-border/80 bg-card px-3 text-sm sm:w-48"
              value={employment}
              onChange={(event) => setEmployment(event.target.value)}
            >
              <option value="">Any employment</option>
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
            </select>
            <select
              className="h-10 rounded-lg border border-border/80 bg-card px-3 text-sm sm:w-48"
              value={region}
              onChange={(event) => setRegion(event.target.value as LocationRegion | "")}
            >
              <option value="">All locations</option>
              {(filters?.regions || []).map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
            <select
              className="h-10 rounded-lg border border-border/80 bg-card px-3 text-sm sm:w-48"
              value={skill}
              onChange={(event) => setSkillOverride(event.target.value)}
            >
              <option value="">All skills</option>
              {(filters?.skills || []).slice(0, 40).map((item) => (
                <option key={item.id} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </select>
            <select
              className="h-10 rounded-lg border border-border/80 bg-card px-3 text-sm sm:w-48"
              value={sort}
              onChange={(event) => setSort(event.target.value as typeof sort)}
            >
              <option value="newest">Recently added</option>
              <option value="deadline">Newest deadline</option>
              <option value="closing_soon">Closing soon</option>
              <option value="featured">Featured first</option>
              <option value="matched">For you</option>
            </select>
          </div>

          {skill ? (
            <p className="text-sm text-muted-foreground">
              Filtering by skill{" "}
              <span className="font-medium text-foreground">{skill}</span>
              {" · "}
              <button
                type="button"
                className="text-brand-orange hover:underline"
                onClick={() => setSkillOverride("")}
              >
                Clear
              </button>
            </p>
          ) : null}

          <p className="text-sm text-muted-foreground">
            Signed in?{" "}
            <Link href="/my-opportunities" className="text-brand-orange hover:underline">
              My saved opportunities
            </Link>
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
            Loading opportunities…
          </div>
        ) : null}

        {!loading && error ? (
          <EmptyState
            icon={<Briefcase className="size-5" />}
            title="Could not load opportunities"
            description={error}
          />
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <EmptyState
            icon={<Briefcase className="size-5" />}
            title="No opportunities listed yet"
            description="Published roles, fellowships, and research openings will appear here when Analytic Sages adds them. Nothing here is a placeholder listing."
          />
        ) : null}

        {!loading && !error && items.length > 0 ? (
          <div>
            <p className="mb-4 text-sm text-muted-foreground">
              {total} {total === 1 ? "opportunity" : "opportunities"}
            </p>
            <div className="space-y-4">
              {items.map((item) => (
                <OpportunityRow key={item.id} opportunity={item} />
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
