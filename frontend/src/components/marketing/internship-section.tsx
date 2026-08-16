import { ArrowRight } from "lucide-react";
import { SectionBackground } from "@/components/marketing/section-background";
import { ButtonLink } from "@/components/ui/button-link";

export function InternshipSection() {
  return (
    <section className="relative py-28 sm:py-32">
      <SectionBackground variant="grid" />
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-3xl rounded-3xl border bg-brand-surface p-10 text-center shadow-card sm:p-14">
          <p className="text-base font-semibold uppercase tracking-wide text-brand-orange sm:text-lg">
            Internship program
          </p>
          <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
            Learn. Prove yourself. Get selected.
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground">
            Outstanding students may receive opportunities to join our internship program
            where they work on real blockchain research, data engineering, and analytics
            projects.
          </p>
          <p className="mt-4 font-heading text-lg font-semibold text-brand-navy dark:text-brand-orange">
            No promises. Just merit.
          </p>
          <ButtonLink
            href="/instructor-led"
            size="lg"
            className="group mt-10 h-14 bg-brand-navy px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-navy/90 hover:shadow-float"
          >
            Explore learning paths
            <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
          </ButtonLink>
        </div>
      </div>
    </section>
  );
}
