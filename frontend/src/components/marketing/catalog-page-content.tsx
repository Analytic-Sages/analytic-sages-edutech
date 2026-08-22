"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Filter, Layers, RefreshCw, Search, Sparkles } from "lucide-react";
import { CourseCard } from "@/components/course/course-card";
import { SelfPacedCatalogCard } from "@/components/course/self-paced-catalog-card";
import { SectionBackground } from "@/components/marketing/section-background";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { courses } from "@/lib/mock-data";
import { listSelfPacedCourses, type SelfPacedCourseCard } from "@/lib/api";
import { mergeFreeCatalog } from "@/lib/self-paced";
import { cn } from "@/lib/utils";
import type { Course } from "@/types/course";

const eyebrowClass =
  "text-lg font-bold uppercase tracking-[0.12em] text-brand-orange sm:text-xl";

type PriceFilter = "all" | "free" | "paid";

function parsePriceFilter(value: string | null): PriceFilter {
  if (value === "free" || value === "paid") return value;
  return "all";
}

function CatalogGrid({
  live,
  soon,
}: {
  live: SelfPacedCourseCard[];
  soon: Course[];
}) {
  if (live.length === 0 && soon.length === 0) return null;
  return (
    <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {live.map((course) => (
        <SelfPacedCatalogCard key={course.id} course={course} />
      ))}
      {soon.map((course) => (
        <CourseCard key={course.id} course={course} />
      ))}
    </div>
  );
}

function PriceChips({
  value,
  onChange,
}: {
  value: PriceFilter;
  onChange: (value: PriceFilter) => void;
}) {
  const chips: { id: PriceFilter; label: string }[] = [
    { id: "all", label: "All" },
    { id: "free", label: "Free" },
    { id: "paid", label: "Paid" },
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {chips.map((chip) => (
        <button
          key={chip.id}
          type="button"
          onClick={() => onChange(chip.id)}
          className={cn(
            "rounded-full border px-4 py-2 text-sm font-semibold",
            value === chip.id
              ? "border-brand-navy bg-brand-navy text-white"
              : "border-border bg-background text-foreground hover:border-brand-orange/50"
          )}
        >
          {chip.label}
        </button>
      ))}
    </div>
  );
}

export function CatalogPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const priceFilter = parsePriceFilter(searchParams.get("price"));
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [level, setLevel] = useState("all");
  const [liveCourses, setLiveCourses] = useState<SelfPacedCourseCard[]>(() => mergeFreeCatalog([]));

  useEffect(() => {
    let cancelled = false;
    listSelfPacedCourses()
      .then((rows) => {
        if (!cancelled) setLiveCourses(rows);
      })
      .catch(() => {
        if (!cancelled) setLiveCourses([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const freeCourses = mergeFreeCatalog(liveCourses.filter((course) => course.is_free));
  const paidLive = liveCourses.filter((course) => !course.is_free);
  const liveSlugs = useMemo(() => new Set(liveCourses.map((course) => course.slug)), [liveCourses]);
  const paidSoon = useMemo(
    () =>
      courses
        .filter((course) => !liveSlugs.has(course.slug))
        .map((course) => ({ ...course, comingSoon: true as const })),
    [liveSlugs],
  );

  const categories = ["all", ...new Set(courses.map((c) => c.category))];
  const levels = ["all", "Beginner", "Intermediate", "Advanced"];

  const query = search.toLowerCase();
  const matchesQuery = (title: string, description: string, cat: string, difficulty: string) => {
    const matchesSearch =
      !query ||
      title.toLowerCase().includes(query) ||
      description.toLowerCase().includes(query);
    const matchesCategory = category === "all" || cat === category;
    const matchesLevel =
      level === "all" || difficulty === level || difficulty.toLowerCase().includes(level.toLowerCase());
    return matchesSearch && matchesCategory && matchesLevel;
  };

  const filteredFree = freeCourses.filter((course) =>
    matchesQuery(course.title, course.description, course.category, course.difficulty)
  );
  const filteredPaidLive = paidLive.filter((course) =>
    matchesQuery(course.title, course.description, course.category, course.difficulty)
  );
  const filteredPaidSoon = paidSoon.filter((course) =>
    matchesQuery(course.title, course.description, course.category, course.difficulty)
  );

  const showFree = priceFilter !== "paid";
  const showPaid = priceFilter !== "free";
  const visibleFree = showFree ? filteredFree : [];
  const visiblePaidLive = showPaid ? filteredPaidLive : [];
  const visiblePaidSoon = showPaid ? filteredPaidSoon : [];
  const visibleCount = visibleFree.length + visiblePaidLive.length + visiblePaidSoon.length;
  const catalogueEmpty = visibleCount === 0;

  function setPriceFilter(value: PriceFilter) {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "all") params.delete("price");
    else params.set("price", value);
    const queryString = params.toString();
    router.replace(queryString ? `/courses?${queryString}` : "/courses", { scroll: false });
  }

  const resetFilters = () => {
    setSearch("");
    setCategory("all");
    setLevel("all");
  };

  return (
    <div className="relative overflow-hidden pb-16">
      <SectionBackground variant="glow" />
      <div className="relative mx-auto max-w-screen-2xl px-4 py-12 sm:px-6 sm:py-16 lg:px-10">
        <div className="max-w-3xl">
          <p className={eyebrowClass}>Self-paced learning</p>
          <h1 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Learn on your schedule.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
            Free courses to get started. Paid courses for deeper, structured learning.
          </p>
          <p className="mt-4 text-sm text-muted-foreground">
            Want to learn live with experts now?{" "}
            <ButtonLink
              href="/instructor-led"
              variant="link"
              className="h-auto px-0 text-brand-orange"
            >
              View Instructor-Led Training
            </ButtonLink>
          </p>
        </div>

        <div className="mt-8">
          <PriceChips value={priceFilter} onChange={setPriceFilter} />
        </div>

        <section id="all-courses" className="mt-12">
          <h2 className="font-heading text-2xl font-bold tracking-tight sm:text-3xl">All courses</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Search and filter the full catalogue by topic or level.
          </p>

          <div className="mt-6 rounded-2xl border bg-card/80 p-4 shadow-card">
            <div className="grid min-w-0 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div className="relative min-w-0">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by topic, skill, or keyword..."
                  className="w-full bg-background/90 pl-9"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>

              <Select value={category} onValueChange={(v) => v && setCategory(v)}>
                <SelectTrigger className="min-w-0 bg-background/90">
                  <div className="flex min-w-0 items-center gap-2">
                    <Layers className="size-3.5 shrink-0 text-brand-orange" />
                    <SelectValue placeholder="Category" />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat === "all" ? "All Categories" : cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={level} onValueChange={(v) => v && setLevel(v)}>
                <SelectTrigger className="min-w-0 bg-background/90">
                  <div className="flex min-w-0 items-center gap-2">
                    <Filter className="size-3.5 shrink-0 text-brand-navy dark:text-brand-orange" />
                    <SelectValue placeholder="Difficulty Level" />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  {levels.map((lvl) => (
                    <SelectItem key={lvl} value={lvl}>
                      {lvl === "all" ? "All Levels" : lvl}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <div className="flex min-w-0 items-center justify-between gap-2">
                <Badge variant="outline" className="h-10 min-w-0 px-3 font-mono text-xs">
                  <Sparkles className="mr-1.5 size-3.5 shrink-0 text-brand-orange" />
                  {visibleCount} {visibleCount === 1 ? "Course" : "Courses"} Found
                </Badge>
                {(search || category !== "all" || level !== "all") && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={resetFilters}
                    className="h-10 shrink-0 px-3 text-xs text-muted-foreground hover:text-foreground"
                  >
                    <RefreshCw className="mr-1.5 size-3" />
                    Reset
                  </Button>
                )}
              </div>
            </div>
          </div>
        </section>

        {catalogueEmpty ? (
          <div className="mt-10 rounded-2xl border border-dashed bg-background/60 py-12 text-center">
            <p className="font-heading text-lg font-semibold">No matching courses</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Try adjusting your search terms or filter selection.
            </p>
            <Button variant="outline" className="mt-4" onClick={resetFilters}>
              Clear search filters
            </Button>
          </div>
        ) : (
          <>
            {visibleFree.length > 0 ? (
              <section className="mt-12">
                <h2 className="font-heading text-2xl font-bold tracking-tight">Start learning for free</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  No payment required. Create an account and start learning.
                </p>
                <CatalogGrid live={visibleFree} soon={[]} />
              </section>
            ) : null}

            {visiblePaidLive.length > 0 || visiblePaidSoon.length > 0 ? (
              <section className="mt-14">
                <h2 className="font-heading text-2xl font-bold tracking-tight">Go deeper</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Structured courses for learners ready to build deeper, practical expertise.
                </p>
                <CatalogGrid live={visiblePaidLive} soon={visiblePaidSoon} />
              </section>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
