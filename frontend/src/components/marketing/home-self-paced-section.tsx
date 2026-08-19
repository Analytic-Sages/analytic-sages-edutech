import { ArrowRight } from "lucide-react";
import { CourseCard } from "@/components/course/course-card";
import { ButtonLink } from "@/components/ui/button-link";
import { getSelfPacedCourses } from "@/lib/mock-data";
import { catalogCardFromApi, FEATURED_FREE_COURSE } from "@/lib/self-paced";

const freeCourse = {
  ...catalogCardFromApi(FEATURED_FREE_COURSE),
  skills: ["Dune SQL", "Dashboard parameters", "On-chain analytics"],
};

export function HomeSelfPacedSection() {
  const comingSoon = getSelfPacedCourses().slice(0, 2);

  return (
    <section className="relative py-20 sm:py-28">
      <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-orange">
              Self-Paced Learning
            </p>
            <h2 className="mt-3 font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
              Learn on your schedule
            </h2>
            <p className="mt-3 max-w-xl text-lg text-muted-foreground">
              Start with a free Dune course. Additional on-demand programs are marked Coming soon
              until the premium player is ready.
            </p>
          </div>
          <ButtonLink href="/courses" variant="outline" className="shrink-0">
            Browse self-paced
            <ArrowRight className="ml-2 size-4" />
          </ButtonLink>
        </div>
        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <CourseCard course={freeCourse} />
          {comingSoon.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      </div>
    </section>
  );
}
