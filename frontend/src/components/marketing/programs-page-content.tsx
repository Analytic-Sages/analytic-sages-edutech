"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { ArrowRight, Database, Rocket, Users } from "lucide-react";
import { CourseCard } from "@/components/course/course-card";
import { SectionBackground } from "@/components/marketing/section-background";
import { ButtonLink } from "@/components/ui/button-link";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { getFeaturedCourses } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

const eyebrowClass =
  "text-lg font-bold uppercase tracking-[0.12em] text-brand-orange sm:text-xl";

const paths = [
  {
    level: "Beginner",
    tagline: "No experience? No problem.",
    body: "Start from ground zero. Learn blockchain basics, core data concepts, and how to navigate the Web3 ecosystem with confidence.",
    accent: "from-brand-orange/20 to-transparent",
    bar: "bg-brand-orange",
    number: "01",
  },
  {
    level: "Intermediate",
    tagline: "Time to level up.",
    body: "Dive deeper into smart contract analysis, DeFi protocols, and real-world datasets. Perfect for those with some knowledge, ready to get hands-on.",
    accent: "from-brand-navy/15 to-transparent",
    bar: "bg-brand-navy",
    number: "02",
  },
  {
    level: "Expert",
    tagline: "Built for the bold.",
    body: "Push boundaries with advanced blockchain analytics, custom dashboards, protocol deep dives, and leadership in data strategy.",
    accent: "from-brand-navy/25 to-transparent",
    bar: "bg-foreground",
    number: "03",
  },
] as const;

const valueProps = [
  {
    icon: Database,
    title: "Practical Blockchain Analytics",
    body: "Learn by doing. Analyse smart contracts, NFT trends, DeFi protocols, and on-chain transactions using real-world datasets.",
  },
  {
    icon: Rocket,
    title: "Beginner-Friendly, Professional-Ready",
    body: "Whether you’re new to Web3 or a seasoned analyst, our content scales with your growth.",
  },
  {
    icon: Users,
    title: "Community & Mentorship",
    body: "Access a network of learners, mentors, and industry professionals shaping the future of decentralized data.",
  },
] as const;

function FadeIn({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const reducedMotion = useReducedMotion();

  if (reducedMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function ProgramsPageContent() {
  const reducedMotion = useReducedMotion();
  const featuredCourses = getFeaturedCourses();
  const flankingLeft = valueProps.slice(0, 2);
  const flankingRight = valueProps[2];
  const RightIcon = flankingRight.icon;

  return (
    <div className="pb-8">
      {/* Hero */}
      <section className="relative min-h-[78vh] overflow-hidden border-b">
        <Image
          src="/4.png"
          alt=""
          fill
          priority
          className="object-cover object-center"
          sizes="100vw"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-brand-navy/95 via-brand-navy/85 to-brand-navy/55" />
        <div className="absolute inset-0 bg-gradient-to-t from-brand-navy/70 via-transparent to-brand-navy/30" />

        <div className="relative mx-auto flex min-h-[78vh] max-w-screen-2xl flex-col justify-center px-4 py-24 sm:px-6 sm:py-32 lg:px-10">
          <FadeIn className="max-w-3xl">
            <p className="text-lg font-bold uppercase tracking-[0.14em] text-brand-orange sm:text-xl">
              Analytic Sages
            </p>
            <h1 className="mt-5 font-heading text-5xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl lg:leading-[1.05]">
              Your Web3 Journey Starts Here!
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/90 sm:text-xl">
              Pick your path, build your stack, and grow with a community built for blockchain
              data careers.
            </p>
            <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:gap-5">
              <ButtonLink
                href="/courses"
                size="lg"
                className="group h-14 bg-brand-orange px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-float"
              >
                Enroll Now
                <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
              </ButtonLink>
              <ButtonLink
                href="/community"
                size="lg"
                variant="outline"
                className="h-14 border-white/40 bg-white/5 px-10 text-base text-white backdrop-blur-sm transition-all hover:-translate-y-0.5 hover:bg-white/10 hover:text-white"
              >
                Join our Community
              </ButtonLink>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Paths */}
      <section id="programs" className="relative overflow-hidden bg-background py-24 sm:py-32">
        <SectionBackground variant="dots" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <FadeIn className="max-w-3xl">
            <p className={eyebrowClass}>Our Programs</p>
            <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              Pick Your Path.
              <span className="mt-2 block text-brand-navy dark:text-brand-orange">
                Build Your Stack.
              </span>
            </h2>
          </FadeIn>

          <div className="mt-16 space-y-0">
            {paths.map((path, index) => (
              <FadeIn key={path.level} delay={index * 0.08}>
                <article
                  className={cn(
                    "group relative grid gap-6 border-t border-border/80 py-10 sm:grid-cols-12 sm:gap-10 sm:py-12",
                    index === paths.length - 1 && "border-b"
                  )}
                >
                  <div
                    className={cn(
                      "absolute inset-y-0 left-0 w-1 origin-top scale-y-100 transition-transform duration-500 sm:w-1.5",
                      path.bar,
                      !reducedMotion && "group-hover:scale-y-110"
                    )}
                  />
                  <div className="sm:col-span-3 sm:pl-6">
                    <span className="font-mono text-sm font-semibold text-muted-foreground">
                      {path.number}
                    </span>
                    <h3 className="mt-2 font-heading text-3xl font-bold tracking-tight sm:text-4xl">
                      {path.level}
                    </h3>
                  </div>
                  <div className="sm:col-span-9 sm:pl-2">
                    <p className="font-heading text-xl font-semibold text-brand-orange sm:text-2xl">
                      {path.tagline}
                    </p>
                    <p className="mt-3 max-w-2xl text-lg leading-relaxed text-muted-foreground">
                      {path.body}
                    </p>
                  </div>
                  <div
                    aria-hidden
                    className={cn(
                      "pointer-events-none absolute inset-0 -z-10 bg-gradient-to-r opacity-0 transition-opacity duration-500 group-hover:opacity-100",
                      path.accent
                    )}
                  />
                </article>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* Featured course preview */}
      <section className="relative overflow-hidden border-y bg-brand-warm py-24 sm:py-32">
        <SectionBackground variant="dots" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <FadeIn className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-end">
            <div className="max-w-2xl">
              <p className={eyebrowClass}>Featured courses</p>
              <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
                A look at what’s live
              </h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Start with these paths, or open the full catalog for every program, including
                ones launching soon.
              </p>
            </div>
          </FadeIn>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:max-w-4xl lg:gap-8">
            {featuredCourses.map((course, index) => (
              <FadeIn key={course.id} delay={Math.min(index * 0.08, 0.2)}>
                <CourseCard course={course} variant="path" />
              </FadeIn>
            ))}
          </div>

          <FadeIn delay={0.15} className="mt-12 flex flex-col items-center gap-3 text-center sm:mt-14">
            <ButtonLink
              href="/courses"
              size="lg"
              className="group h-14 bg-brand-orange px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-float"
            >
              Explore more courses in our course catalog
              <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
            </ButtonLink>
            <p className="text-sm text-muted-foreground">
              Filter by level, category, and what’s open for enrollment.
            </p>
          </FadeIn>
        </div>
      </section>

      {/* Value props */}
      <section className="relative overflow-hidden bg-background py-24 sm:py-32">
        <SectionBackground variant="glow" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <FadeIn className="mx-auto max-w-3xl text-center">
            <p className={eyebrowClass}>Value Propositions</p>
            <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
              From Basics to Breakthroughs
            </h2>
            <p className="mt-5 text-lg leading-relaxed text-muted-foreground">
              Master blockchain analytics through real-world practice, guided growth, and a
              community that’s got your back.
            </p>
          </FadeIn>

          {/* Image framed by value props */}
          <div className="mt-16 grid items-stretch gap-10 lg:grid-cols-12 lg:gap-8 xl:gap-12">
            <div className="flex flex-col justify-between gap-10 lg:col-span-3 lg:py-2">
              {flankingLeft.map((item, index) => {
                const Icon = item.icon;
                return (
                  <FadeIn key={item.title} delay={0.08 + index * 0.08}>
                    <div className="lg:text-right">
                      <div className="flex items-center gap-3 lg:flex-row-reverse">
                        <Icon className="size-5 shrink-0 text-brand-orange" />
                        <h3 className="font-heading text-xl font-bold tracking-tight sm:text-2xl">
                          {item.title}
                        </h3>
                      </div>
                      <p className="mt-3 text-base leading-relaxed text-muted-foreground sm:text-lg">
                        {item.body}
                      </p>
                    </div>
                  </FadeIn>
                );
              })}
            </div>

            <FadeIn delay={0.1} className="lg:col-span-6">
              <div className="relative mx-auto aspect-[4/5] max-w-lg overflow-hidden rounded-2xl sm:aspect-[5/6] lg:mx-0 lg:max-w-none lg:h-full lg:min-h-[28rem] lg:aspect-auto">
                <Image
                  src="/2.png"
                  alt="Analytic Sages learners in a workshop"
                  fill
                  className="object-cover"
                  sizes="(max-width: 1024px) 100vw, 50vw"
                />
              </div>
            </FadeIn>

            <div className="flex flex-col justify-center lg:col-span-3 lg:py-2">
              <FadeIn delay={0.2}>
                <div>
                  <div className="flex items-center gap-3">
                    <RightIcon className="size-5 shrink-0 text-brand-orange" />
                    <h3 className="font-heading text-xl font-bold tracking-tight sm:text-2xl">
                      {flankingRight.title}
                    </h3>
                  </div>
                  <p className="mt-3 text-base leading-relaxed text-muted-foreground sm:text-lg">
                    {flankingRight.body}
                  </p>
                </div>
              </FadeIn>
            </div>
          </div>

          <FadeIn delay={0.2} className="mt-16 text-center">
            <ButtonLink
              href="/courses"
              size="lg"
              variant="outline"
              className="group h-14 px-10 text-base transition-all hover:-translate-y-0.5 hover:shadow-elevated"
            >
              Explore more courses in our course catalog
              <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
            </ButtonLink>
          </FadeIn>
        </div>
      </section>
    </div>
  );
}
