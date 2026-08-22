"use client";

import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { CourseCard } from "@/components/course/course-card";
import { SelfPacedCatalogCard } from "@/components/course/self-paced-catalog-card";
import { ButtonLink } from "@/components/ui/button-link";
import { listSelfPacedCourses, type SelfPacedCourseCard } from "@/lib/api";
import { getSelfPacedCourses } from "@/lib/mock-data";
import { mergeFreeCatalog } from "@/lib/self-paced";

export function HomeSelfPacedSection() {
  const [freeCourses, setFreeCourses] = useState<SelfPacedCourseCard[]>(() => mergeFreeCatalog([]));
  const paidSoon = getSelfPacedCourses().slice(0, 3);

  useEffect(() => {
    let cancelled = false;
    listSelfPacedCourses()
      .then((rows) => {
        if (!cancelled) setFreeCourses(mergeFreeCatalog(rows.filter((course) => course.is_free)));
      })
      .catch(() => {
        if (!cancelled) setFreeCourses(mergeFreeCatalog([]));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="relative py-20 sm:py-28">
      <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-orange">
              Self-Paced Learning
            </p>
            <h2 className="mt-3 font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
              Learn at your own pace
            </h2>
            <p className="mt-3 max-w-xl text-lg text-muted-foreground">
              Start free. Paid on-demand courses show their price up front and stay Launching soon
              until the player is ready.
            </p>
          </div>
          <ButtonLink href="/courses" variant="outline" className="shrink-0">
            Browse self-paced
            <ArrowRight className="ml-2 size-4" />
          </ButtonLink>
        </div>

        <div className="mt-12 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h3 className="font-heading text-2xl font-bold tracking-tight">Free to start</h3>
            <p className="mt-1 text-sm text-muted-foreground">Enroll now at no cost.</p>
          </div>
          <ButtonLink href="/courses?price=free" variant="ghost" className="shrink-0 text-brand-orange">
            All free courses
            <ArrowRight className="ml-1 size-4" />
          </ButtonLink>
        </div>
        <div className="mt-6 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {freeCourses.map((course) => (
            <SelfPacedCatalogCard key={course.id} course={course} />
          ))}
        </div>

        <div className="mt-16 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h3 className="font-heading text-2xl font-bold tracking-tight">Paid self-paced</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Price on every card. Not open for enrollment until the player is ready.
            </p>
          </div>
          <ButtonLink href="/courses?price=paid" variant="ghost" className="shrink-0 text-brand-orange">
            All paid courses
            <ArrowRight className="ml-1 size-4" />
          </ButtonLink>
        </div>
        <div className="mt-6 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {paidSoon.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      </div>
    </section>
  );
}
