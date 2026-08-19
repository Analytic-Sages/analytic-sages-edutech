"use client";

import { useEffect, useState } from "react";
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

const eyebrowClass =
  "text-lg font-bold uppercase tracking-[0.12em] text-brand-orange sm:text-xl";

export function CatalogPageContent() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [level, setLevel] = useState("all");
  const [freeCourses, setFreeCourses] = useState<SelfPacedCourseCard[]>(() => mergeFreeCatalog([]));

  useEffect(() => {
    let cancelled = false;
    listSelfPacedCourses()
      .then((rows) => {
        if (!cancelled) setFreeCourses(mergeFreeCatalog(rows));
      })
      .catch(() => {
        if (!cancelled) setFreeCourses(mergeFreeCatalog([]));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const categories = ["all", ...new Set(courses.map((c) => c.category))];
  const levels = ["all", "Beginner", "Intermediate", "Advanced"];

  const filteredCourses = courses
    .map((c) => ({ ...c, comingSoon: true as const }))
    .filter((course) => {
    const matchesSearch =
      course.title.toLowerCase().includes(search.toLowerCase()) ||
      course.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = category === "all" || course.category === category;
    const matchesLevel = level === "all" || course.difficulty === level;
    return matchesSearch && matchesCategory && matchesLevel;
  });

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
            Start with a free self-paced course, then browse upcoming on-demand programs. Paid
            library paths stay marked Launching soon until the premium player is ready.
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

        <div className="my-10 rounded-2xl border bg-card/80 p-4 shadow-card backdrop-blur">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="relative">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by topic, skill, or keyword..."
                className="bg-background/90 pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <Select value={category} onValueChange={(v) => v && setCategory(v)}>
              <SelectTrigger className="bg-background/90">
                <div className="flex items-center gap-2">
                  <Layers className="size-3.5 text-brand-orange" />
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
              <SelectTrigger className="bg-background/90">
                <div className="flex items-center gap-2">
                  <Filter className="size-3.5 text-brand-navy dark:text-brand-orange" />
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

            <div className="flex items-center justify-between gap-2">
              <Badge variant="outline" className="h-10 px-3 font-mono text-xs">
                <Sparkles className="mr-1.5 size-3.5 text-brand-orange" />
                {filteredCourses.length}{" "}
                {filteredCourses.length === 1 ? "Course" : "Courses"} Found
              </Badge>
              {(search || category !== "all" || level !== "all") && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetFilters}
                  className="h-10 px-3 text-xs text-muted-foreground hover:text-foreground"
                >
                  <RefreshCw className="mr-1.5 size-3" />
                  Reset
                </Button>
              )}
            </div>
          </div>
        </div>

        <section className="mb-12">
          <h2 className="font-heading text-2xl font-bold tracking-tight">Free courses</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Enroll at no cost. Watch lessons on Analytic Sages and track your progress.
          </p>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {freeCourses.map((course) => (
              <SelfPacedCatalogCard key={course.id} course={course} />
            ))}
          </div>
        </section>

        <h2 className="mb-4 font-heading text-2xl font-bold tracking-tight">Coming soon</h2>
        {filteredCourses.length === 0 ? (
          <div className="rounded-2xl border border-dashed bg-background/60 py-16 text-center">
            <p className="font-heading text-lg font-semibold">No matching courses found</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Try adjusting your search terms or filter selection.
            </p>
            <Button variant="outline" className="mt-4" onClick={resetFilters}>
              Clear all filters
            </Button>
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredCourses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
