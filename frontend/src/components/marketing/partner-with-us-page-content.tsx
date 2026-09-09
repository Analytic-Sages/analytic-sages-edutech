"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { PartnershipInquiryForm } from "@/components/marketing/partnership-inquiry-form";
import { SectionBackground } from "@/components/marketing/section-background";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { ButtonLink } from "@/components/ui/button-link";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import {
  contributionPipeline,
  partnerCapabilities,
  partnerCaseStudies,
  partnerContributions,
  partnerFaqs,
  partnerHeroProofMetrics,
  partnerImpactMetrics,
  partnerOutcomes,
  partnershipModes,
  talentPipelineSteps,
  whyAnalyticSages,
} from "@/lib/partner-with-us";
import { cn } from "@/lib/utils";

const eyebrowClass =
  "text-sm font-bold uppercase tracking-[0.14em] text-brand-orange sm:text-base";

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
  if (reducedMotion) return <div className={className}>{children}</div>;
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

function SectionShell({
  children,
  className,
  id,
  variant = "none",
  dark = false,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
  variant?: "none" | "glow" | "lines" | "dots" | "diamonds" | "grid";
  dark?: boolean;
}) {
  return (
    <section
      id={id}
      className={cn(
        "relative overflow-hidden border-b py-20 sm:py-24 lg:py-28",
        dark ? "border-brand-navy bg-brand-navy text-white" : "bg-background",
        className
      )}
    >
      {!dark ? <SectionBackground variant={variant} /> : null}
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">{children}</div>
    </section>
  );
}

export function PartnerWithUsPageContent() {
  const reducedMotion = useReducedMotion();

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b bg-background">
        <SectionBackground variant="diamonds" />
        <SectionBackground variant="glow" />
        <div className="relative mx-auto grid max-w-screen-2xl items-center gap-12 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-[1.15fr_0.85fr] lg:gap-16 lg:px-10 lg:py-24">
          <FadeIn>
            <p className={eyebrowClass}>
              For protocols · Ecosystems · Foundations · Web3 companies
            </p>
            <h1 className="mt-5 font-heading text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl xl:text-[3.75rem] xl:leading-[1.05]">
              Build the talent
              <br />
              behind your blockchain ecosystem.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
              Analytic Sages helps blockchain ecosystems develop the data, intelligence and
              technical talent needed to understand, build and grow.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <ButtonLink
                href="#partner-inquiry"
                size="lg"
                className="h-12 bg-brand-orange px-8 text-base text-white hover:bg-brand-orange/90"
              >
                Partner With Us
                <ArrowRight className="ml-2 size-4" />
              </ButtonLink>
              <ButtonLink
                href="#our-work"
                size="lg"
                variant="outline"
                className="h-12 border-brand-navy/20 px-8 text-base dark:border-white/20"
              >
                Explore Our Work
              </ButtonLink>
            </div>
          </FadeIn>

          <FadeIn delay={0.1}>
            <aside className="rounded-2xl border bg-card p-6 shadow-card sm:p-8">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-brand-orange">
                Our track record
              </p>
              <dl className="mt-6 grid grid-cols-2 gap-6">
                {partnerHeroProofMetrics.map((stat) => (
                  <div key={stat.label}>
                    <dt className="sr-only">{stat.label}</dt>
                    <dd className="font-heading text-3xl font-bold tracking-tight text-brand-navy dark:text-brand-orange sm:text-4xl">
                      {stat.value}
                    </dd>
                    <p className="mt-1 text-sm text-muted-foreground">{stat.label}</p>
                  </div>
                ))}
              </dl>
              <p className="mt-8 border-t pt-6 text-sm leading-relaxed text-muted-foreground">
                Since 2023, Analytic Sages has built a global community around blockchain data,
                analytics and technical education.
              </p>
            </aside>
          </FadeIn>
        </div>
      </section>

      {/* Core value */}
      <SectionShell variant="lines">
        <FadeIn className="max-w-3xl">
          <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Understand your ecosystem.
            <br />
            Build the talent behind it.
          </h2>
          <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
            Every blockchain ecosystem generates data. Understanding that data, and developing
            the people capable of working with it, is essential to long-term ecosystem growth.
          </p>
          <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
            Analytic Sages connects blockchain data education, technical training and practical
            project development to help ecosystems build deeper capabilities around their own
            technology.
          </p>
        </FadeIn>
        <div className="mt-14 grid gap-8 lg:grid-cols-2">
          <FadeIn className="rounded-2xl border bg-brand-surface p-6 sm:p-8">
            <p className={eyebrowClass}>Ecosystem intelligence</p>
            <div className="mt-6 flex flex-wrap items-center gap-2 text-sm font-semibold uppercase tracking-wide text-brand-navy dark:text-foreground sm:gap-3 sm:text-base">
              {["Ecosystem data", "Analytics", "Intelligence"].map((step, i) => (
                <span key={step} className="inline-flex items-center gap-2 sm:gap-3">
                  {i > 0 ? <span className="text-brand-orange">→</span> : null}
                  {step}
                </span>
              ))}
            </div>
          </FadeIn>
          <FadeIn delay={0.08} className="rounded-2xl border bg-brand-warm p-6 sm:p-8">
            <p className={eyebrowClass}>Talent development</p>
            <div className="mt-6 flex flex-wrap items-center gap-2 text-sm font-semibold uppercase tracking-wide text-brand-navy dark:text-foreground sm:gap-3 sm:text-base">
              {["Learning", "Skills", "Talent", "Contribution"].map((step, i) => (
                <span key={step} className="inline-flex items-center gap-2 sm:gap-3">
                  {i > 0 ? <span className="text-brand-orange">→</span> : null}
                  {step}
                </span>
              ))}
            </div>
          </FadeIn>
        </div>
      </SectionShell>

      {/* What we build */}
      <SectionShell id="our-work" variant="dots">
        <FadeIn className="max-w-3xl">
          <p className={eyebrowClass}>What we build with partners</p>
          <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            From blockchain data to
            <br />
            ecosystem contribution.
          </h2>
        </FadeIn>
        <div className="mt-14 grid gap-8 md:grid-cols-2 xl:grid-cols-3">
          {partnerCapabilities.map((cap, index) => (
            <FadeIn key={cap.number} delay={Math.min(index * 0.04, 0.2)}>
              <article className="h-full border-t-2 border-brand-orange/80 pt-6">
                <p className="font-heading text-sm font-bold text-brand-orange">{cap.number}</p>
                <h3 className="mt-3 font-heading text-xl font-bold tracking-tight sm:text-2xl">
                  {cap.title}
                </h3>
                <p className="mt-3 text-muted-foreground">{cap.summary}</p>
                <ul className="mt-5 space-y-1.5 text-sm text-foreground/90">
                  {cap.items.map((item) => (
                    <li key={item} className="flex gap-2">
                      <span className="text-brand-orange">·</span>
                      {item}
                    </li>
                  ))}
                </ul>
                <p className="mt-5 text-sm font-medium text-brand-navy dark:text-brand-orange">
                  {cap.outcome}
                </p>
              </article>
            </FadeIn>
          ))}
        </div>
      </SectionShell>

      {/* Signature pipeline */}
      <SectionShell dark className="border-b-0">
        <FadeIn className="max-w-3xl">
          <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Understand the data
            <br />
            behind blockchain ecosystems.
          </h2>
          <p className="mt-6 text-lg leading-relaxed text-white/75">
            Blockchain ecosystems produce enormous amounts of data. The opportunity is not simply
            to collect it, but to develop the people, tools and intelligence needed to understand
            it.
          </p>
        </FadeIn>
        <div className="mt-14">
          <ol className="flex flex-col gap-0 lg:flex-row lg:items-stretch lg:justify-between lg:gap-2">
            {contributionPipeline.map((step, index) => (
              <li key={step} className="flex flex-1 flex-col items-start lg:items-center lg:text-center">
                <motion.div
                  className="flex w-full items-center gap-4 lg:flex-col lg:gap-3"
                  initial={reducedMotion ? false : { opacity: 0, y: 12 }}
                  whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.06, duration: 0.45 }}
                >
                  <span className="inline-flex size-11 shrink-0 items-center justify-center rounded-full border border-brand-orange/60 bg-brand-orange/10 font-heading text-sm font-bold text-brand-orange">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="font-heading text-base font-semibold tracking-wide sm:text-lg">
                    {step}
                  </span>
                </motion.div>
                {index < contributionPipeline.length - 1 ? (
                  <div
                    className="ml-5 h-8 w-px bg-white/20 lg:ml-0 lg:mt-3 lg:h-px lg:w-full lg:bg-gradient-to-r lg:from-brand-orange/40 lg:to-transparent"
                    aria-hidden
                  />
                ) : null}
              </li>
            ))}
          </ol>
        </div>
        <p className="mt-12 max-w-2xl text-base text-white/70">
          We don&apos;t just teach people about blockchain ecosystems. We help them understand,
          build and contribute to them.
        </p>
      </SectionShell>

      {/* Talent pipeline */}
      <SectionShell variant="grid">
        <FadeIn className="max-w-3xl">
          <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Build your
            <br />
            ecosystem talent pipeline.
          </h2>
          <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
            From first exposure to real contribution, we create structured pathways that help
            ecosystems develop and discover technical talent.
          </p>
        </FadeIn>
        <ol className="mt-14 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {talentPipelineSteps.map((step, index) => (
            <FadeIn key={step.number} delay={Math.min(index * 0.03, 0.18)}>
              <li className="h-full rounded-xl border bg-card p-5 sm:p-6">
                <p className="font-heading text-sm font-bold text-brand-orange">{step.number}</p>
                <h3 className="mt-2 font-heading text-lg font-bold uppercase tracking-wide">
                  {step.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </li>
            </FadeIn>
          ))}
        </ol>
      </SectionShell>

      {/* Ways to partner */}
      <SectionShell variant="lines" className="bg-brand-surface">
        <FadeIn className="max-w-3xl">
          <p className={eyebrowClass}>Ways to partner</p>
          <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            A partnership built around
            <br />
            your ecosystem&apos;s goals.
          </h2>
        </FadeIn>
        <div className="mt-14 grid gap-x-10 gap-y-10 md:grid-cols-2 lg:grid-cols-3">
          {partnershipModes.map((mode) => (
            <FadeIn key={mode.number}>
              <article>
                <p className="font-heading text-sm font-bold text-brand-orange">{mode.number}</p>
                <h3 className="mt-2 font-heading text-xl font-bold">{mode.title}</h3>
                <p className="mt-3 text-muted-foreground">{mode.body}</p>
              </article>
            </FadeIn>
          ))}
        </div>
        <p className="mt-12 max-w-2xl text-base text-muted-foreground">
          Every partnership is designed around the ecosystem&apos;s goals, audience, technical
          stack and stage of growth.
        </p>
        <div className="mt-8">
          <ButtonLink
            href="#partner-inquiry"
            className="h-12 bg-brand-navy px-8 text-base text-white hover:bg-brand-navy/90"
          >
            Discuss a Partnership
            <ArrowRight className="ml-2 size-4" />
          </ButtonLink>
        </div>
      </SectionShell>

      {/* What partners get */}
      <SectionShell>
        <FadeIn>
          <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            What you get from the partnership
          </h2>
        </FadeIn>
        <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {partnerOutcomes.map((item) => (
            <FadeIn key={item.title}>
              <article className="border-l-2 border-brand-orange pl-5">
                <h3 className="font-heading text-lg font-bold uppercase tracking-wide">
                  {item.title}
                </h3>
                <p className="mt-3 text-muted-foreground">{item.body}</p>
              </article>
            </FadeIn>
          ))}
        </div>
      </SectionShell>

      {/* What partners contribute */}
      <SectionShell variant="dots">
        <FadeIn className="max-w-3xl">
          <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Bring your ecosystem into the experience.
          </h2>
          <p className="mt-6 text-lg text-muted-foreground">
            Partners can contribute resources and expertise where it strengthens the learning
            experience and pathways into the ecosystem.
          </p>
        </FadeIn>
        <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {partnerContributions.map((block) => (
            <FadeIn key={block.title}>
              <article>
                <h3 className="font-heading text-base font-bold uppercase tracking-wide text-brand-navy dark:text-brand-orange">
                  {block.title}
                </h3>
                <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                  {block.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            </FadeIn>
          ))}
        </div>
      </SectionShell>

      {/* Proven impact */}
      <SectionShell dark>
        <FadeIn>
          <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Built around real outcomes.
          </h2>
        </FadeIn>
        <dl className="mt-14 grid grid-cols-2 gap-8 lg:grid-cols-5">
          {partnerImpactMetrics.map((metric) => (
            <FadeIn key={metric.label}>
              <div>
                <dt className="sr-only">{metric.label}</dt>
                <dd className="font-heading text-4xl font-bold tracking-tight text-brand-orange sm:text-5xl">
                  {metric.value}
                </dd>
                <p className="mt-2 text-sm text-white/70 sm:text-base">{metric.label}</p>
              </div>
            </FadeIn>
          ))}
        </dl>
      </SectionShell>

      {/* Case studies (verified only) */}
      <SectionShell className="bg-brand-surface">
        <FadeIn className="max-w-3xl">
          <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            From partnership
            <br />
            to real-world outputs.
          </h2>
          <p className="mt-6 text-lg text-muted-foreground">
            Case studies appear here when we can share verified partnership outcomes. Until then,
            discuss how a program could map to your ecosystem.
          </p>
        </FadeIn>
        {partnerCaseStudies.length > 0 ? (
          <div className="mt-12 space-y-10">
            {partnerCaseStudies.map((study) => (
              <article key={study.id} className="rounded-2xl border bg-card p-6 sm:p-8">
                <h3 className="font-heading text-2xl font-bold">{study.partnerName}</h3>
                <div className="mt-6 grid gap-6 md:grid-cols-2">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-brand-orange">
                      The challenge
                    </p>
                    <p className="mt-2 text-muted-foreground">{study.challenge}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-brand-orange">
                      What we did
                    </p>
                    <p className="mt-2 text-muted-foreground">{study.whatWeDid}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-brand-orange">
                      What participants built
                    </p>
                    <p className="mt-2 text-muted-foreground">{study.whatParticipantsBuilt}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-brand-orange">
                      Outcome
                    </p>
                    <p className="mt-2 text-muted-foreground">{study.outcome}</p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="mt-10 rounded-2xl border border-dashed bg-card/60 p-6 sm:p-8">
            <p className="text-sm leading-relaxed text-muted-foreground">
              Verified partnership case studies will be published here as programs complete and
              outcomes can be shared publicly.
            </p>
            <ButtonLink href="#partner-inquiry" className="mt-5 h-11 bg-brand-navy text-white hover:bg-brand-navy/90">
              Discuss a Partnership
              <ArrowRight className="ml-2 size-4" />
            </ButtonLink>
          </div>
        )}
      </SectionShell>

      {/* Why AS */}
      <SectionShell variant="glow">
        <FadeIn>
          <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Why Analytic Sages
          </h2>
        </FadeIn>
        <div className="mt-14 grid gap-8 sm:grid-cols-2">
          {whyAnalyticSages.map((pillar, i) => (
            <FadeIn key={pillar.title} delay={i * 0.05}>
              <article className="rounded-xl border bg-card p-6">
                <p className="font-heading text-sm font-bold text-brand-orange">
                  {String(i + 1).padStart(2, "0")}
                </p>
                <h3 className="mt-3 font-heading text-xl font-bold uppercase tracking-wide">
                  {pillar.title}
                </h3>
                <p className="mt-3 text-muted-foreground">{pillar.body}</p>
              </article>
            </FadeIn>
          ))}
        </div>
      </SectionShell>

      {/* FAQ */}
      <SectionShell variant="lines">
        <FadeIn className="mx-auto max-w-2xl text-center">
          <p className={eyebrowClass}>FAQ</p>
          <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl">
            Partnership questions
          </h2>
        </FadeIn>
        <div className="mx-auto mt-12 max-w-3xl rounded-2xl border bg-card px-4 py-2 shadow-card sm:px-6">
          <Accordion>
            {partnerFaqs.map((faq) => (
              <AccordionItem key={faq.question} value={faq.question}>
                <AccordionTrigger className="py-5 text-base font-semibold hover:no-underline sm:text-lg">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="pb-5 text-base leading-relaxed text-muted-foreground">
                  <p>{faq.answer}</p>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </SectionShell>

      {/* Final CTA + form */}
      <section className="relative overflow-hidden bg-brand-navy py-20 text-white sm:py-24 lg:py-28">
        <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <div className="grid gap-14 lg:grid-cols-[0.95fr_1.05fr] lg:gap-16">
            <FadeIn>
              <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
                Build the next generation
                <br />
                of your ecosystem.
              </h2>
              <p className="mt-6 text-lg leading-relaxed text-white/75">
                Whether you&apos;re looking to develop technical talent, deepen ecosystem
                intelligence, launch a learning track or create a pathway from education to
                contribution, let&apos;s build it together.
              </p>
              <div className="mt-8 flex flex-wrap gap-4">
                <ButtonLink
                  href="#partner-inquiry"
                  className="h-12 bg-brand-orange px-8 text-base text-white hover:bg-brand-orange/90"
                >
                  Partner With Analytic Sages
                  <ArrowRight className="ml-2 size-4" />
                </ButtonLink>
                <ButtonLink
                  href="/programs"
                  variant="outline"
                  className="h-12 border-white/30 bg-transparent px-8 text-base text-white hover:bg-white/10"
                >
                  Explore Our Programs
                </ButtonLink>
              </div>
              <p className="mt-8 text-sm text-white/55">
                Protocols · Foundations · Infrastructure Companies · Ecosystem Teams
              </p>
            </FadeIn>
            <FadeIn delay={0.08}>
              <div className="rounded-2xl border border-white/15 bg-white/5 p-6 sm:p-8">
                <h3 className="font-heading text-xl font-semibold">Start a partnership conversation</h3>
                <p className="mt-2 text-sm text-white/65">
                  Tell us about your ecosystem goals. We&apos;ll follow up to explore fit.
                </p>
                <div className="mt-6">
                  <PartnershipInquiryForm />
                </div>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>
    </>
  );
}
