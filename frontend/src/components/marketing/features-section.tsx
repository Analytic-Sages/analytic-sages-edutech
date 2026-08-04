"use client";

import { Award, BookOpen, Brain, Users } from "lucide-react";
import { FeatureCard } from "@/components/marketing/feature-card";
import { SectionBackground } from "@/components/marketing/section-background";
import { ButtonLink } from "@/components/ui/button-link";

const features = [
  {
    icon: BookOpen,
    title: "Project-Based Learning",
    description:
      "Every course culminates in real projects that become portfolio pieces employers actually want to see.",
    stat: "40+ hands-on projects",
  },
  {
    icon: Brain,
    title: "Technical Depth",
    description:
      "Blockchain analytics, quant finance, data engineering, and ML, taught by practitioners, not theorists.",
    stat: "5 learning paths",
  },
  {
    icon: Award,
    title: "Verified Certificates",
    description:
      "Earn certificates based on demonstrated competence, not just video completion.",
    stat: "Competence-based credentials",
  },
  {
    icon: Users,
    title: "Career Outcomes",
    description:
      "From learning to fellowship to internship. We optimize for jobs, not just course completion.",
    stat: "700+ community members",
    href: "/community",
  },
];

export function FeaturesSection() {
  return (
    <section className="relative py-28 sm:py-32">
      <SectionBackground variant="grid" />
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="max-w-2xl">
          <p className="text-sm font-medium uppercase tracking-wide text-brand-orange">
            Why Analytic Sages
          </p>
          <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem]">
            Built for outcomes,
            <br className="hidden sm:block" />
            not just content
          </h2>
          <p className="mt-6 text-lg text-muted-foreground">
            A premium learning platform designed like modern SaaS, focused on
            completing real learning journeys.
          </p>
        </div>

        <div className="mt-16 grid gap-8 lg:grid-cols-12 lg:gap-10">
          <div className="grid gap-8 sm:grid-cols-2 lg:col-span-8 lg:grid-cols-2">
            {features.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
          <div className="flex flex-col justify-center rounded-2xl border border-brand-navy/20 bg-gradient-to-br from-brand-navy to-brand-navy/90 p-10 text-white shadow-float dark:border-white/10 lg:col-span-4">
            <p className="text-sm font-medium text-white/70">Student outcomes</p>
            <h3 className="mt-3 font-heading text-2xl font-bold sm:text-3xl">
              From curiosity to career
            </h3>
            <ul className="mt-8 space-y-5 text-sm text-white/85 sm:text-base">
              <li className="flex items-start gap-3">
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-brand-orange" />
                Complete portfolio-ready blockchain projects
              </li>
              <li className="flex items-start gap-3">
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-brand-orange" />
                Earn verified certificates employers trust
              </li>
              <li className="flex items-start gap-3">
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-brand-orange" />
                Join a community of 700+ analysts & builders
              </li>
            </ul>
            <ButtonLink
              href="/courses"
              className="group mt-10 h-12 bg-brand-orange text-white transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-elevated"
            >
              Browse courses
            </ButtonLink>
          </div>
        </div>
      </div>
    </section>
  );
}
