"use client";

import { useEffect, useState } from "react";
import {
  ArrowRight,
  Calendar,
  Check,
  Clock,
  Loader2,
  Radio,
  Users,
  X,
} from "lucide-react";
import { SectionBackground } from "@/components/marketing/section-background";
import {
  ProgramProjectShowcase,
  ProgramTestimonialGrid,
} from "@/components/marketing/program-project-showcase";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent } from "@/components/ui/card";
import { listPublicCohorts, type PublicCohortCard } from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";
import type { ProgramPageContent } from "@/lib/program-pages";
import { cn } from "@/lib/utils";

function formatDate(iso: string | null) {
  if (!iso) return null;
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "long",
      day: "numeric",
      year: "numeric",
      timeZone: "UTC",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function formatDuration(startsAt: string | null, endsAt: string | null) {
  if (!startsAt || !endsAt) return null;
  const start = new Date(startsAt).getTime();
  const end = new Date(endsAt).getTime();
  if (Number.isNaN(start) || Number.isNaN(end) || end <= start) return null;
  const weeks = Math.max(1, Math.round((end - start) / (7 * 24 * 60 * 60 * 1000)));
  return `${weeks} weeks`;
}

const eyebrow =
  "text-lg font-bold uppercase tracking-[0.12em] text-brand-orange sm:text-xl";

export function ProgramLandingPage({ program }: { program: ProgramPageContent }) {
  const [cohort, setCohort] = useState<PublicCohortCard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    listPublicCohorts()
      .then((rows) => {
        if (!cancelled) {
          setCohort(rows.find((row) => row.slug === program.cohortSlug) ?? null);
        }
      })
      .catch(() => {
        if (!cancelled) setCohort(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [program.cohortSlug]);

  const checkoutHref = `/checkout/cohort/${program.cohortSlug}`;
  const priceLabel =
    cohort && cohort.price > 0 ? formatPrice(cohort.price, cohort.currency) : null;
  const startDate = formatDate(cohort?.starts_at ?? null);
  const deadline = formatDate(cohort?.registration_deadline ?? null);
  const duration = formatDuration(cohort?.starts_at ?? null, cohort?.ends_at ?? null);
  const sessions = cohort?.sessions_count;

  const facts = [
    duration ? { label: "Duration", value: duration } : null,
    startDate ? { label: "Start date", value: startDate } : null,
    { label: "Format", value: program.format },
    { label: "Weekly commitment", value: program.timeCommitmentShort },
    sessions != null
      ? {
          label: "Live sessions",
          value: `${sessions} scheduled session${sessions === 1 ? "" : "s"}`,
        }
      : { label: "Live sessions", value: "Instructor-led live classes" },
    { label: "Community", value: program.community },
    priceLabel ? { label: "Price", value: priceLabel } : null,
  ].filter((item): item is { label: string; value: string } => item !== null);

  return (
    <div className="pb-24 md:pb-8">
      <section className="relative overflow-hidden border-b">
        <SectionBackground variant="diamonds" />
        <SectionBackground variant="glow" />
        <div className="relative mx-auto max-w-screen-2xl px-4 py-16 sm:px-6 sm:py-24 lg:px-10 lg:py-28">
          <p className={eyebrow}>{program.eyebrow}</p>
          <h1 className="mt-5 max-w-4xl font-heading text-4xl font-bold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[1.05]">
            {program.headline}
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
            {program.support}
          </p>
          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:gap-5">
            <ButtonLink
              href="#register"
              size="lg"
              className="group h-14 bg-brand-orange px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-float"
            >
              Register for Cohort 9
              <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
            </ButtonLink>
            <ButtonLink
              href="#curriculum"
              size="lg"
              variant="outline"
              className="h-14 px-10 text-base transition-all hover:-translate-y-0.5 hover:shadow-elevated"
            >
              Explore the Curriculum
            </ButtonLink>
          </div>

          <dl className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {loading && facts.length < 3 ? (
              <div className="col-span-full flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Loading live cohort dates…
              </div>
            ) : (
              facts.map((fact) => (
                <div key={fact.label} className="rounded-xl border bg-card/80 p-4 shadow-card">
                  <dt className="text-xs font-semibold uppercase tracking-wide text-brand-orange">
                    {fact.label}
                  </dt>
                  <dd className="mt-1 text-sm font-medium leading-relaxed text-foreground">
                    {fact.value}
                  </dd>
                </div>
              ))
            )}
          </dl>
        </div>
      </section>

      <section className="relative overflow-hidden border-b py-20 sm:py-28">
        <SectionBackground variant="lines" />
        <div className="relative mx-auto grid max-w-screen-2xl gap-10 px-4 sm:px-6 lg:grid-cols-2 lg:gap-16 lg:px-10">
          <div>
            <p className={eyebrow}>Who this is for</p>
            <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl">
              This program is for you if…
            </h2>
            <ul className="mt-8 space-y-3">
              {program.audienceFor.map((item) => (
                <li key={item} className="flex gap-3 text-base leading-relaxed">
                  <Check className="mt-0.5 size-5 shrink-0 text-brand-orange" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className={eyebrow}>Be honest with yourself</p>
            <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl">
              Not for you if…
            </h2>
            <ul className="mt-8 space-y-3">
              {program.audienceNotFor.map((item) => (
                <li key={item} className="flex gap-3 text-base leading-relaxed text-muted-foreground">
                  <X className="mt-0.5 size-5 shrink-0 text-destructive" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section id="curriculum" className="scroll-mt-24 border-b bg-brand-surface py-20 sm:py-28">
        <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <p className={eyebrow}>Curriculum</p>
          <h2 className="mt-4 max-w-3xl font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            What you will learn
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            Four modules from the Cohort 9 SQL blockchain analytics curriculum — foundations
            through a capstone dashboard.
          </p>
          <Accordion className="mt-12 rounded-2xl border bg-card px-4 py-2 shadow-card sm:px-6">
            {program.modules.map((module) => (
              <AccordionItem key={module.id} value={module.id}>
                <AccordionTrigger className="py-5 text-left hover:no-underline">
                  <span className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:gap-4">
                    <span className="font-heading text-sm font-bold tracking-wide text-brand-orange">
                      Module {module.number}
                    </span>
                    <span className="font-heading text-lg font-semibold sm:text-xl">
                      {module.title}
                    </span>
                  </span>
                </AccordionTrigger>
                <AccordionContent className="pb-6 text-base leading-relaxed text-muted-foreground">
                  <p>{module.summary}</p>
                  <p className="mt-4 font-medium text-foreground">What you learn</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5">
                    {module.learn.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                  <p className="mt-4 text-sm">
                    <span className="font-medium text-foreground">Tools: </span>
                    {module.tools.join(", ")}
                  </p>
                  <p className="mt-2 text-sm">
                    <span className="font-medium text-foreground">Practical outcome: </span>
                    {module.outcome}
                  </p>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      <section className="relative overflow-hidden border-b py-20 sm:py-28">
        <SectionBackground variant="dots" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <p className={eyebrow}>Projects</p>
          <h2 className="mt-4 max-w-3xl font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Build real projects. Not just watch lessons.
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            These are the project types in the Cohort 9 curriculum. They are assignments, not
            invented student results.
          </p>
          <div className="mt-12 grid gap-6 md:grid-cols-2">
            {program.projects.map((project) => (
              <Card key={project.id} className="shadow-card">
                <CardContent className="space-y-3 pt-2">
                  <h3 className="font-heading text-xl font-semibold">{project.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium text-foreground">Analyzes: </span>
                    {project.analyzes}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium text-foreground">Tools: </span>
                    {project.tools.join(", ")}
                  </p>
                  <p className="text-sm leading-relaxed">{project.demonstrates}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b bg-brand-warm py-20 sm:py-28">
        <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <p className={eyebrow}>Student work</p>
          <h2 className="mt-4 max-w-3xl font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            What our students have built
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            Real Analytic Sages workshop photos. We do not publish fake dashboards or invented
            project stats. Video stories from earlier cohorts are in the next section.
          </p>
          <ProgramProjectShowcase items={program.studentWork} className="mt-12" />
        </div>
      </section>

      <section className="relative overflow-hidden border-b py-20 sm:py-28">
        <SectionBackground variant="grid" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <p className={eyebrow}>Testimonials</p>
          <h2 className="mt-4 max-w-3xl font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Learn from the experience of others
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            Video stories from Analytic Sages learners in earlier cohorts.
          </p>
          <div className="mt-12">
            <ProgramTestimonialGrid items={program.testimonials} />
          </div>
        </div>
      </section>

      <section className="border-b bg-brand-surface py-20 sm:py-28">
        <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <p className={eyebrow}>Outcomes</p>
          <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            What you&apos;ll achieve
          </h2>
          <ul className="mt-10 grid gap-4 sm:grid-cols-2">
            {program.outcomes.map((item) => (
              <li
                key={item}
                className="flex gap-3 rounded-xl border bg-card p-5 text-base leading-relaxed shadow-card"
              >
                <Check className="mt-0.5 size-5 shrink-0 text-brand-orange" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="relative overflow-hidden border-b py-20 sm:py-28">
        <SectionBackground variant="dots" />
        <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <p className={eyebrow}>Stack</p>
          <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Tools you&apos;ll work with
          </h2>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {program.tools.map((tool) => (
              <div key={tool.id} className="rounded-xl border bg-card p-6 shadow-card">
                <p className="font-heading text-xl font-semibold">{tool.name}</p>
                <p className="mt-2 text-sm text-muted-foreground">{tool.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b py-20 sm:py-28">
        <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <p className={eyebrow}>How it works</p>
          <h2 className="mt-4 max-w-3xl font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            The instructor-led experience
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            This is live cohort training — scheduled classes, projects, and feedback — not the
            self-paced catalog.
          </p>
          <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {program.experience.map((item) => (
              <Card key={item.title} className="shadow-card">
                <CardContent className="space-y-2 pt-2">
                  <h3 className="font-heading text-lg font-semibold uppercase tracking-wide text-brand-navy dark:text-brand-orange">
                    {item.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">{item.body}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="details" className="scroll-mt-24 border-b bg-brand-surface py-20 sm:py-28">
        <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <p className={eyebrow}>Program details</p>
          <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl">
            Cohort 9 at a glance
          </h2>
          <p className="mt-4 max-w-2xl text-muted-foreground">
            Dates and price come from the live cohort listing. If a field is missing, the
            schedule has not been published yet.
          </p>
          <dl className="mt-10 grid gap-px overflow-hidden rounded-xl border bg-border shadow-card sm:grid-cols-2">
            {[
              ["Duration", duration],
              ["Start date", startDate],
              ["Registration deadline", deadline],
              ["Format", program.format],
              [
                "Live session schedule",
                sessions != null
                  ? `${sessions} session${sessions === 1 ? "" : "s"} on the Classroom calendar`
                  : null,
              ],
              ["Time commitment", program.timeCommitment],
              ["Price", priceLabel],
              ["Payment options", program.paymentOptions],
              ["Community access", program.community],
              ["Certificate", program.certificate],
            ].map(([label, value]) => (
              <div key={label} className="bg-card px-5 py-4">
                <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {label}
                </dt>
                <dd className="mt-1 text-sm font-medium leading-relaxed">
                  {value ?? "Published with the live cohort listing"}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="border-b py-20 sm:py-28">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-10">
          <p className={cn(eyebrow, "text-center")}>FAQ</p>
          <h2 className="mt-4 text-center font-heading text-3xl font-bold tracking-tight sm:text-4xl">
            Questions about Cohort 9
          </h2>
          <Accordion className="mt-10 rounded-2xl border bg-card px-4 py-2 shadow-card sm:px-6">
            {program.faqs.map((faq) => (
              <AccordionItem key={faq.question} value={faq.question}>
                <AccordionTrigger className="py-5 text-left text-base font-semibold hover:no-underline sm:text-lg">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="pb-5 text-base leading-relaxed text-muted-foreground">
                  <p>{faq.answer}</p>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      <section id="register" className="scroll-mt-24 relative py-20 sm:py-28">
        <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
          <div className="relative overflow-hidden rounded-3xl bg-brand-navy px-8 py-16 sm:px-16 sm:py-20">
            <SectionBackground variant="glow" className="opacity-60" />
            <div className="relative mx-auto max-w-2xl text-center">
              <h2 className="font-heading text-3xl font-bold text-white sm:text-5xl">
                Ready to build with real blockchain data?
              </h2>
              <p className="mx-auto mt-6 max-w-xl text-base text-white/90 sm:text-lg">
                Join Cohort 9 and develop practical blockchain data analytics skills through
                structured, instructor-led learning.
              </p>
              {priceLabel && (
                <p className="mt-4 text-lg font-semibold text-brand-orange">{priceLabel}</p>
              )}
              {deadline && (
                <p className="mt-2 inline-flex items-center gap-2 text-sm text-white/80">
                  <Calendar className="size-4" />
                  Register by {deadline}
                </p>
              )}
              <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <ButtonLink
                  href={checkoutHref}
                  size="lg"
                  className="group h-14 bg-brand-orange px-10 text-base text-white shadow-elevated hover:bg-brand-orange/90"
                >
                  Register for Cohort 9
                  <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
                </ButtonLink>
                <ButtonLink
                  href="/instructor-led"
                  size="lg"
                  variant="outline"
                  className="h-14 border-white/30 bg-transparent px-10 text-base text-white hover:bg-white/10 hover:text-white"
                >
                  All instructor-led cohorts
                </ButtonLink>
              </div>
              <p className="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs text-white/70">
                <span className="inline-flex items-center gap-1.5">
                  <Radio className="size-3.5" /> Live classroom after payment
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <Users className="size-3.5" /> Sign in required at checkout
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <Clock className="size-3.5" /> Existing Paystack and crypto checkout
                </span>
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/95 p-3 backdrop-blur md:hidden">
        <ButtonLink
          href={checkoutHref}
          className="h-12 w-full bg-brand-orange text-white hover:bg-brand-orange/90"
        >
          Register for Cohort 9
          {priceLabel ? ` · ${priceLabel}` : ""}
        </ButtonLink>
      </div>
    </div>
  );
}
