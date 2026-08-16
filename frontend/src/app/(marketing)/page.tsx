import { ArrowRight } from "lucide-react";
import { FeaturesSection } from "@/components/marketing/features-section";
import { HeroVisual } from "@/components/marketing/hero-visual";
import { HomeCommunitySection } from "@/components/marketing/home-community-section";
import { HomeCtaSection } from "@/components/marketing/home-cta-section";
import { HomeInstructorLedSection } from "@/components/marketing/home-instructor-led-section";
import { HomeSelfPacedSection } from "@/components/marketing/home-self-paced-section";
import { HomeTestimonialsSection } from "@/components/marketing/home-testimonials-section";
import { InternshipSection } from "@/components/marketing/internship-section";
import { LearningPathsSection } from "@/components/marketing/learning-paths-section";
import { SectionBackground } from "@/components/marketing/section-background";
import { TrustStats } from "@/components/marketing/trust-stats";
import { WhySection } from "@/components/marketing/why-section";
import { ButtonLink } from "@/components/ui/button-link";

export default function HomePage() {
  return (
    <>
      <section className="relative flex min-h-[75vh] items-center overflow-hidden border-b bg-background">
        <SectionBackground variant="diamonds" />
        <SectionBackground variant="glow" />
        <div className="relative mx-auto w-full max-w-screen-2xl px-4 py-20 sm:px-6 sm:py-28 lg:px-10 lg:py-32">
          <div className="grid items-center gap-16 lg:grid-cols-2 lg:gap-24 xl:gap-32">
            <div className="max-w-2xl">
              <p className="mb-5 text-base font-semibold tracking-wide text-brand-orange uppercase sm:text-lg">
                Analytic Sages
              </p>
              <h1 className="font-heading text-5xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl xl:text-8xl xl:leading-[1.05]">
                Build the Skills That Power the Future of Blockchain.
              </h1>
              <p className="mt-8 max-w-xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
                Learn through live expert-led cohorts or flexible self-paced programs in
                blockchain data, analytics, and AI.
              </p>
              <div className="mt-12 flex flex-col gap-4 sm:flex-row sm:gap-5">
                <ButtonLink
                  href="/instructor-led"
                  size="lg"
                  className="group h-14 bg-brand-orange px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-float"
                >
                  View live training
                  <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
                </ButtonLink>
                <ButtonLink
                  href="/courses"
                  size="lg"
                  variant="outline"
                  className="h-14 px-10 text-base transition-all hover:-translate-y-0.5 hover:shadow-elevated"
                >
                  Explore self-paced
                </ButtonLink>
              </div>
            </div>
            <HeroVisual />
          </div>
        </div>
      </section>

      <TrustStats />

      <LearningPathsSection />

      <HomeInstructorLedSection />

      <HomeSelfPacedSection />

      <FeaturesSection />

      <WhySection />

      <InternshipSection />

      <HomeCommunitySection />

      <HomeTestimonialsSection />

      <HomeCtaSection />
    </>
  );
}
