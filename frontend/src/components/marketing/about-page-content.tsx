"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { SectionBackground } from "@/components/marketing/section-background";
import { PatternBackground } from "@/components/marketing/pattern-background";
import { ButtonLink } from "@/components/ui/button-link";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { cn } from "@/lib/utils";

const eyebrowClass =
  "text-lg font-bold uppercase tracking-[0.12em] text-brand-orange sm:text-xl lg:text-2xl";

const timeline = [
  {
    year: "2023",
    title: "The beginning",
    body: "Two data enthusiasts saw an opportunity at the intersection of blockchain technology and data analytics. Analytic Sages began as a community created to help people understand and work with blockchain data.",
  },
  {
    year: "2023-24",
    title: "Early cohorts",
    body: "We started with cohort-based learning. Students learned blockchain analytics through practical exercises, real datasets, and hands-on projects.",
  },
  {
    year: "2024-25",
    title: "Growth",
    body: "Interest grew. More learners joined from different backgrounds and countries, creating a community around blockchain data, analytics, and technical learning.",
  },
  {
    year: "Today",
    title: "The platform",
    body: "Analytic Sages is evolving into a full technology education platform. Our learning paths now extend beyond blockchain analytics into data engineering, AI, and quantitative finance.",
  },
  {
    year: "Next",
    title: "What we're building",
    body: "A place where learners can learn, build, practice, get mentored, collaborate, earn credentials, and advance their careers progressively, as each capability is ready.",
  },
];

const approach = [
  {
    number: "01",
    title: "Real tools",
    body: "Dune, SQL, Python, APIs, RPCs, and modern cloud & data tooling. The same stack used in real analytics and engineering work.",
  },
  {
    number: "02",
    title: "Real projects",
    body: "Students work on practical projects that demonstrate what they can actually build. Portfolios, not just completed checklists.",
  },
  {
    number: "03",
    title: "Real skills",
    body: "The goal isn't simply finishing lessons. The goal is becoming capable of doing the work.",
  },
];

const principles = [
  {
    number: "01",
    title: "Practical",
    body: "Real datasets. Real tools. Real projects.",
  },
  {
    number: "02",
    title: "Technical",
    body: "We go beyond surface-level introductions and teach the foundations behind the tools.",
  },
  {
    number: "03",
    title: "Community-driven",
    body: "Learning becomes more powerful when people learn, build, and solve problems together.",
  },
  {
    number: "04",
    title: "Career-oriented",
    body: "We focus on skills and projects that help learners become more capable professionals.",
  },
];

/** Stats already used on the homepage trust strip. */
const communityStats = [
  { value: "2,000+", label: "Community members" },
  { value: "18+", label: "Countries represented" },
  { value: "450+", label: "Blockchain analysts trained" },
  { value: "8", label: "Successful cohorts" },
];

const platformItems = [
  { label: "Instructor-Led & Self-Paced paths", status: "live" as const },
  { label: "Student dashboard & enrollments", status: "live" as const },
  { label: "Instructor-Led live classroom", status: "live" as const },
  { label: "Self-paced course catalog", status: "building" as const },
  { label: "Course player & progress", status: "building" as const },
  { label: "Projects & assessments", status: "soon" as const },
  { label: "Verified certificates", status: "soon" as const },
];

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
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function AboutPageContent() {
  return (
    <div className="pb-8">
      {/* 1. Hero */}
      <section className="relative overflow-hidden border-b bg-background">
        <PatternBackground />
        <SectionBackground variant="glow" />
        <div className="relative mx-auto max-w-screen-2xl px-4 py-24 sm:px-6 sm:py-32 lg:px-10 lg:py-40">
          <FadeIn className="max-w-3xl">
            <p className={eyebrowClass}>About Analytic Sages</p>
            <h1 className="mt-5 font-heading text-5xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl lg:leading-[1.05]">
              Building the people who build the future.
            </h1>
            <p className="mt-8 max-w-2xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
              We help ambitious learners build practical skills in blockchain analytics,
              data engineering, AI, and quantitative finance.
            </p>
            <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:gap-5">
              <ButtonLink
                href="/instructor-led"
                size="lg"
                className="group h-14 bg-brand-orange px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-float"
              >
                Explore Programs
                <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
              </ButtonLink>
              <ButtonLink
                href="/community"
                size="lg"
                variant="outline"
                className="h-14 px-10 text-base transition-all hover:-translate-y-0.5 hover:shadow-elevated"
              >
                Join the Community
              </ButtonLink>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* 2. Who we are */}
      <section className="relative overflow-hidden bg-background py-24 sm:py-32">
        <PatternBackground />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <div className="grid items-center gap-14 lg:grid-cols-12 lg:gap-16">
            <FadeIn className="lg:col-span-5">
              <p className={eyebrowClass}>Who we are</p>
              <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
                Learning technology by actually building with it.
              </h2>
              <div className="mt-6 space-y-5 text-lg leading-relaxed text-muted-foreground">
                <p>
                  Analytic Sages is a technology education and learning community focused on
                  helping people build practical skills for the modern digital economy.
                </p>
                <p>
                  We started with blockchain data analytics and have grown into a broader
                  learning platform covering blockchain analytics, data engineering, AI, and
                  quantitative finance.
                </p>
                <p className="font-medium text-foreground">
                  Learn the fundamentals. Work with real tools. Build real projects. Develop
                  skills you can actually use.
                </p>
              </div>
            </FadeIn>

            <FadeIn delay={0.1} className="relative lg:col-span-7">
              <div
                aria-hidden
                className="absolute -bottom-4 -right-4 h-2/3 w-2/3 rounded-[28px] bg-brand-orange/10"
              />
              <div className="group relative aspect-[4/5] overflow-hidden rounded-[24px] shadow-elevated sm:aspect-[5/4] lg:aspect-[4/3]">
                <Image
                  src="/2.png"
                  alt="Analytic Sages learners collaborating with laptops during a workshop"
                  fill
                  className="object-cover object-[center_30%] transition-transform duration-500 ease-out group-hover:scale-[1.015]"
                  sizes="(max-width: 1024px) 100vw, 55vw"
                  priority
                />
              </div>
              <p className="mt-4 text-sm text-muted-foreground">
                From classroom workshops to online learning, we learn by building together.
              </p>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* 3. Journey timeline */}
      <section className="relative overflow-hidden border-y bg-brand-surface py-24 sm:py-32">
        <SectionBackground variant="dots" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <FadeIn className="mx-auto max-w-2xl text-center">
            <p className={eyebrowClass}>Our journey</p>
            <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
              From a small idea to a growing learning community.
            </h2>
          </FadeIn>

          <div className="relative mx-auto mt-16 max-w-3xl">
            <div
              aria-hidden
              className="absolute top-2 bottom-2 left-[11px] w-px bg-border sm:left-[15px]"
            />
            <ol className="space-y-10">
              {timeline.map((item, index) => (
                <FadeIn key={item.title} delay={index * 0.05}>
                  <li className="relative flex gap-5 sm:gap-8">
                    <span className="relative z-10 mt-1.5 flex size-6 shrink-0 items-center justify-center rounded-full border-2 border-brand-orange bg-brand-surface sm:size-8">
                      <span className="size-2 rounded-full bg-brand-orange sm:size-2.5" />
                    </span>
                    <div className="min-w-0 pb-2">
                      <p className="font-mono text-xs font-semibold tracking-wide text-brand-orange uppercase sm:text-sm">
                        {item.year}
                      </p>
                      <h3 className="mt-1 font-heading text-xl font-bold sm:text-2xl">
                        {item.title}
                      </h3>
                      <p className="mt-2 text-base leading-relaxed text-muted-foreground sm:text-lg">
                        {item.body}
                      </p>
                    </div>
                  </li>
                </FadeIn>
              ))}
            </ol>
          </div>
        </div>
      </section>

      {/* 4. Learn by doing */}
      <section className="relative overflow-hidden bg-background py-24 sm:py-32">
        <PatternBackground />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <FadeIn className="max-w-2xl">
            <p className={eyebrowClass}>Our approach</p>
            <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
              We don&apos;t believe in learning just to finish a course.
            </h2>
            <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
              Technology skills are built through practice. That&apos;s why our courses are
              designed around real tools, real datasets, and practical projects.
            </p>
          </FadeIn>

          <div className="mt-14 grid gap-6 lg:grid-cols-3">
            {approach.map((item, index) => (
              <FadeIn key={item.number} delay={index * 0.08}>
                <div className="flex h-full flex-col border-t-2 border-brand-orange/80 pt-8">
                  <span className="font-mono text-sm font-semibold text-brand-orange">
                    {item.number}
                  </span>
                  <h3 className="mt-3 font-heading text-2xl font-bold">{item.title}</h3>
                  <p className="mt-4 text-base leading-relaxed text-muted-foreground">
                    {item.body}
                  </p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* 5. Community */}
      <section className="relative overflow-hidden border-y bg-brand-surface py-24 sm:py-32">
        <SectionBackground variant="dots" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <div className="grid items-center gap-14 lg:grid-cols-12 lg:gap-12 xl:gap-16">
            <FadeIn className="order-2 lg:order-1 lg:col-span-7">
              <div className="relative xl:-ml-2">
                <div
                  aria-hidden
                  className="absolute -top-5 -left-5 h-1/2 w-1/2 rounded-[28px] bg-brand-navy/10 dark:bg-brand-orange/10"
                />
                <div className="group relative aspect-[4/3] overflow-hidden rounded-[24px] shadow-elevated">
                  <Image
                    src="/4.png"
                    alt="Analytic Sages community members gathered at an in-person workshop"
                    fill
                    className="object-cover object-center transition-transform duration-500 ease-out group-hover:scale-[1.015]"
                    sizes="(max-width: 1024px) 100vw, 58vw"
                  />
                </div>
              </div>
            </FadeIn>

            <FadeIn delay={0.1} className="order-1 lg:order-2 lg:col-span-5">
              <p className={eyebrowClass}>The people behind Analytic Sages</p>
              <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
                You don&apos;t have to build alone.
              </h2>
              <div className="mt-6 space-y-4 text-lg leading-relaxed text-muted-foreground">
                <p>
                  Analytic Sages started as a learning community. That spirit remains at the
                  heart of everything we do.
                </p>
                <p>
                  From physical workshops to online cohorts, our learners learn from one
                  another, work through problems together, and build relationships that
                  continue beyond the classroom.
                </p>
              </div>

              <dl className="mt-10 grid grid-cols-2 gap-6">
                {communityStats.map((stat) => (
                  <div key={stat.label}>
                    <dt className="font-heading text-3xl font-bold text-brand-navy dark:text-brand-orange sm:text-4xl">
                      {stat.value}
                    </dt>
                    <dd className="mt-1 text-sm text-muted-foreground">{stat.label}</dd>
                  </div>
                ))}
              </dl>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* 6. What makes us different */}
      <section className="relative overflow-hidden bg-background py-24 sm:py-32">
        <PatternBackground />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <FadeIn className="max-w-2xl">
            <p className={eyebrowClass}>Why Analytic Sages</p>
            <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
              Built for people who want to do the work.
            </h2>
          </FadeIn>

          <div className="mt-14 grid gap-x-12 gap-y-12 sm:grid-cols-2">
            {principles.map((item, index) => (
              <FadeIn key={item.number} delay={(index % 2) * 0.06}>
                <div
                  className={cn(
                    "border-l-2 border-brand-navy/20 pl-6 dark:border-brand-orange/30",
                    index % 2 === 1 && "sm:mt-10"
                  )}
                >
                  <span className="font-mono text-sm font-semibold text-brand-orange">
                    {item.number}
                  </span>
                  <h3 className="mt-2 font-heading text-2xl font-bold sm:text-3xl">
                    {item.title}
                  </h3>
                  <p className="mt-3 text-lg leading-relaxed text-muted-foreground">
                    {item.body}
                  </p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* 7. Where we're going: belief statement */}
      <section className="relative overflow-hidden border-y bg-brand-navy py-24 sm:py-32">
        <SectionBackground variant="glow" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <FadeIn className="mx-auto max-w-3xl text-center">
            <p className={eyebrowClass}>Where we&apos;re going</p>
            <p className="mt-6 font-heading text-3xl font-bold leading-snug text-white sm:text-4xl lg:text-5xl">
              We believe access to practical technology education should not depend on where
              you were born or where you started.
            </p>
          </FadeIn>
        </div>
      </section>

      {/* 7b. Mission + Vision: standalone */}
      <section className="relative overflow-hidden bg-background py-24 sm:py-32">
        <PatternBackground />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <FadeIn className="mx-auto max-w-2xl text-center">
            <p className={eyebrowClass}>Mission &amp; vision</p>
            <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
              What we stand for.
            </h2>
          </FadeIn>

          <div className="mx-auto mt-14 grid max-w-5xl gap-8 lg:grid-cols-2 lg:gap-10">
            <FadeIn delay={0.05}>
              <div className="flex h-full flex-col rounded-[24px] border border-brand-navy/15 bg-brand-surface p-8 sm:p-10">
                <p className="font-mono text-sm font-semibold tracking-wide text-brand-orange uppercase">
                  01
                </p>
                <h3 className="mt-3 font-heading text-3xl font-bold text-brand-navy dark:text-brand-orange sm:text-4xl">
                  Our mission
                </h3>
                <p className="mt-5 text-xl leading-relaxed text-foreground/90 sm:text-2xl">
                  To provide practical, accessible, and technically rigorous education that helps
                  people build skills for the evolving digital economy.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.1}>
              <div className="flex h-full flex-col rounded-[24px] border border-brand-orange/25 bg-brand-navy p-8 sm:p-10">
                <p className="font-mono text-sm font-semibold tracking-wide text-brand-orange uppercase">
                  02
                </p>
                <h3 className="mt-3 font-heading text-3xl font-bold text-brand-orange sm:text-4xl">
                  Our vision
                </h3>
                <p className="mt-5 text-xl leading-relaxed text-white/90 sm:text-2xl">
                  A world where more people can understand, build with, and create opportunities
                  from emerging technologies.
                </p>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* 8. Future / platform */}
      <section className="relative overflow-hidden bg-background py-24 sm:py-32">
        <PatternBackground />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <div className="grid items-start gap-14 lg:grid-cols-2 lg:gap-20">
            <FadeIn>
              <p className={eyebrowClass}>What we&apos;re building</p>
              <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
                From learning community to technology education platform.
              </h2>
              <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
                Analytic Sages is evolving beyond cohort-based education. We are building a
                learning platform where students can discover courses, learn at their own
                pace, track progress, work on projects, connect with peers, and earn
                credentials, unlocking each capability as it becomes ready.
              </p>
            </FadeIn>

            <FadeIn delay={0.1}>
              <ul className="divide-y rounded-2xl border bg-card shadow-card">
                {platformItems.map((item) => (
                  <li
                    key={item.label}
                    className="flex items-center justify-between gap-4 px-5 py-4 sm:px-6"
                  >
                    <span className="text-base font-medium">{item.label}</span>
                    <span
                      className={cn(
                        "shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold",
                        item.status === "live" && "bg-success/10 text-success",
                        item.status === "building" &&
                          "bg-brand-orange/10 text-brand-orange",
                        item.status === "soon" && "bg-muted text-muted-foreground"
                      )}
                    >
                      {item.status === "live" && "Live"}
                      {item.status === "building" && "In progress"}
                      {item.status === "soon" && "Coming soon"}
                    </span>
                  </li>
                ))}
              </ul>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* 9. Final CTA */}
      <section className="relative py-20 sm:py-28">
        <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <FadeIn>
            <div className="relative overflow-hidden rounded-3xl bg-brand-navy px-8 py-16 sm:px-16 sm:py-20">
              <SectionBackground variant="glow" className="opacity-80" />
              <div className="relative mx-auto max-w-2xl text-center">
                <h2 className="font-heading text-4xl font-bold text-white sm:text-5xl">
                  Ready to build what&apos;s next?
                </h2>
                <p className="mx-auto mt-6 max-w-xl text-base text-white/90 sm:text-lg">
                  Explore our programs, join the community, and start building practical
                  technology skills.
                </p>
                <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                  <ButtonLink
                    href="/instructor-led"
                    size="lg"
                    className="group h-14 bg-brand-orange px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-float"
                  >
                    Explore Programs
                    <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
                  </ButtonLink>
                  <ButtonLink
                    href="/community"
                    size="lg"
                    variant="outline"
                    className="h-14 border-white/30 bg-transparent px-10 text-base text-white transition-all hover:-translate-y-0.5 hover:bg-white/10 hover:text-white"
                  >
                    Join the Community
                  </ButtonLink>
                </div>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>
    </div>
  );
}
