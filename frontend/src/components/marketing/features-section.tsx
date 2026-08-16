"use client";

import { BookOpen, Brain, Check, Rocket, Users } from "lucide-react";
import { FeatureCard } from "@/components/marketing/feature-card";
import { PatternBackground } from "@/components/marketing/pattern-background";
import { ButtonLink } from "@/components/ui/button-link";

const features = [
  {
    icon: BookOpen,
    title: "Learn by Building",
    description:
      "Every course is built around real blockchain datasets, APIs, smart contracts, and production-grade projects, not theoretical slides.",
    stat: "40+ hands-on projects",
    href: "/instructor-led",
  },
  {
    icon: Brain,
    title: "Industry-Focused Curriculum",
    description:
      "Master SQL, Python, Blockchain Data Engineering, AI, Quantitative Finance, and Onchain Analytics using the same tools professionals use.",
    stat: "5 learning paths",
    href: "/courses",
  },
  {
    icon: Users,
    title: "Mentorship & Community",
    description:
      "Learn alongside researchers, engineers, and analysts worldwide inside an active community built for collaboration and accountability.",
    stat: "Global learner network",
    href: "/community",
  },
  {
    icon: Rocket,
    title: "From Learning to Employment",
    description:
      "Top-performing students gain access to internships, advanced programs, research opportunities, and hiring networks.",
    stat: "Career pipeline",
    href: "/instructor-led",
  },
] as const;

const outcomes = [
  "Portfolio projects",
  "Real blockchain datasets",
  "Case studies",
  "Industry mentorship",
  "Internship opportunities",
  "Career support",
];

export function FeaturesSection() {
  return (
    <section className="relative py-28 sm:py-32">
      <PatternBackground />
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="max-w-2xl">
          <p className="text-sm font-medium uppercase tracking-wide text-brand-orange">
            Why Analytic Sages
          </p>
          <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem]">
            Built for careers,
            <br className="hidden sm:block" />
            not just content
          </h2>
          <p className="mt-6 text-lg text-muted-foreground">
            A global Blockchain Data Engineering school designed to take you from
            first lesson to industry-ready professional.
          </p>
        </div>

        <div className="mt-16 grid gap-8 lg:grid-cols-12 lg:gap-10">
          <div className="grid gap-8 sm:grid-cols-2 lg:col-span-8 lg:grid-cols-2">
            {features.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
          <div className="flex flex-col justify-center rounded-2xl border border-brand-navy/20 bg-gradient-to-br from-brand-navy to-brand-navy/90 p-10 text-white shadow-float dark:border-white/10 lg:col-span-4">
            <p className="text-sm font-medium text-white/90">Graduate with experience</p>
            <h3 className="mt-3 font-heading text-2xl font-bold sm:text-3xl">
              You won&apos;t just finish another online course.
            </h3>
            <p className="mt-2 text-base text-white/95">You&apos;ll graduate with experience.</p>
            <ul className="mt-8 space-y-4 text-sm text-white/95 sm:text-base">
              {outcomes.map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <Check className="mt-0.5 size-4 shrink-0 text-brand-orange" />
                  {item}
                </li>
              ))}
            </ul>
            <ButtonLink
              href="/register"
              className="group mt-10 h-12 bg-brand-orange text-white transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-elevated"
            >
              Start learning
            </ButtonLink>
          </div>
        </div>
      </div>
    </section>
  );
}
