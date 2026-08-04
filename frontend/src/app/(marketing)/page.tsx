import { ArrowRight } from "lucide-react";
import { CourseCard } from "@/components/course/course-card";
import { FeaturesSection } from "@/components/marketing/features-section";
import { HeroVisual } from "@/components/marketing/hero-visual";
import { HomeCommunitySection } from "@/components/marketing/home-community-section";
import { HomeCtaSection } from "@/components/marketing/home-cta-section";
import { SectionBackground } from "@/components/marketing/section-background";
import { TrustStats } from "@/components/marketing/trust-stats";
import { ButtonLink } from "@/components/ui/button-link";
import { courses } from "@/lib/mock-data";
import { siteConfig } from "@/config/site";

export default function HomePage() {
  const featuredCourses = courses.slice(0, 3);

  return (
    <>
      {/* Hero — left-aligned copy, floating product preview */}
      <section className="relative flex min-h-[75vh] items-center overflow-hidden border-b bg-background">
        <SectionBackground variant="glow" />
        <SectionBackground variant="lines" />
        <div className="relative mx-auto w-full max-w-screen-2xl px-4 py-20 sm:px-6 sm:py-28 lg:px-10 lg:py-32">
          <div className="grid items-center gap-16 lg:grid-cols-2 lg:gap-24 xl:gap-32">
            <div className="max-w-2xl">
              <p className="mb-5 text-sm font-medium tracking-wide text-brand-orange uppercase">
                {siteConfig.eyebrow}
              </p>
              <h1 className="font-heading text-5xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl xl:text-8xl xl:leading-[1.05]">
                Learn.{" "}
                <span className="text-brand-navy dark:text-brand-orange">Build.</span>
                <br />
                Get Certified.
              </h1>
              <p className="mt-8 max-w-xl text-lg leading-relaxed text-muted-foreground">
                {siteConfig.description}
              </p>
              <div className="mt-12 flex flex-col gap-4 sm:flex-row sm:gap-5">
                <ButtonLink
                  href="/courses"
                  size="lg"
                  className="group h-14 bg-brand-orange px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-float"
                >
                  Explore Courses
                  <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
                </ButtonLink>
                <ButtonLink
                  href="/register"
                  size="lg"
                  variant="outline"
                  className="h-14 px-10 text-base transition-all hover:-translate-y-0.5 hover:shadow-elevated"
                >
                  Start Free
                </ButtonLink>
              </div>
            </div>
            <HeroVisual />
          </div>
        </div>
      </section>

      <TrustStats />

      <FeaturesSection />

      {/* Featured courses — warm tint + dot pattern */}
      <section className="relative overflow-hidden border-y bg-brand-warm py-28 sm:py-32">
        <SectionBackground variant="dots" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-end">
            <div>
              <p className="text-sm font-medium uppercase tracking-wide text-brand-orange">
                Learning paths
              </p>
              <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem]">
                Featured courses
              </h2>
              <p className="mt-4 max-w-xl text-lg text-muted-foreground">
                Start with our most popular programs in blockchain analytics, data engineering, and
                quantitative finance.
              </p>
            </div>
            <ButtonLink
              href="/courses"
              variant="outline"
              className="group shrink-0 transition-all hover:-translate-y-0.5 hover:shadow-elevated"
            >
              View all {courses.length} courses
              <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
            </ButtonLink>
          </div>
          <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-3 lg:gap-10">
            {featuredCourses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        </div>
      </section>

      <HomeCommunitySection />
      <HomeCtaSection />
    </>
  );
}
