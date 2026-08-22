"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { ArrowRight, Check, ChevronUp, Database, Loader2, X } from "lucide-react";
import { ProgramDuneGrid } from "@/components/marketing/program-dune-grid";
import { InstructorRoster } from "@/components/marketing/instructor-roster";
import { ProgramTestimonialCarousel } from "@/components/marketing/program-testimonial-carousel";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { ButtonLink } from "@/components/ui/button-link";
import { listPublicCohorts, type PublicCohortCard } from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";
import type { ProgramPageContent } from "@/lib/program-pages";

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

  const details: [string, string | null][] = [
    ["Duration", program.duration],
    ["Registration Deadline", deadline],
    ["Start Date", startDate],
    ["Format", program.format],
    ["Time Commitment", program.timeCommitment],
    ["Price", priceLabel ? `${priceLabel} one-time payment` : null],
    ["Payment", program.paymentOptions],
  ];

  return (
    <div className="bg-background pb-24 text-foreground md:pb-0">
      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8 lg:py-20">
        <div className="grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="text-center lg:text-left">
            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-orange">
              {program.eyebrow}
            </p>
            <h1 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              {program.headline}
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground sm:text-xl lg:mx-0">
              {program.support}
            </p>
            {loading ? (
              <p className="mt-6 inline-flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Loading cohort dates…
              </p>
            ) : (
              <p className="mt-6 text-sm text-muted-foreground sm:text-base">
                {[
                  deadline ? `Registration closes: ${deadline}` : null,
                  startDate ? `Classes start: ${startDate}` : null,
                  "Fully remote",
                  "Live sessions",
                ]
                  .filter(Boolean)
                  .join("  ·  ")}
              </p>
            )}
            <div className="mt-8">
              <ButtonLink
                href={checkoutHref}
                size="lg"
                className="h-12 rounded-full bg-brand-orange px-10 text-base text-white hover:bg-brand-orange/90"
              >
                Register for Cohort 9
                <ArrowRight className="ml-2 size-4" />
              </ButtonLink>
            </div>
          </div>
          <div className="relative aspect-[16/10] overflow-hidden rounded-2xl border bg-brand-surface shadow-card">
            <Image
              src={program.postcardImage}
              alt={`${program.headline} course postcard`}
              fill
              className="object-cover"
              priority
              sizes="(max-width: 1024px) 100vw, 50vw"
            />
          </div>
        </div>
      </section>

      <InstructorRoster instructors={cohort?.instructors} />

      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 className="text-center font-heading text-3xl font-bold sm:text-4xl">
          What You&apos;ll Learn
        </h2>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {program.learnTopics.map((topic) => (
            <div
              key={topic.title}
              className="rounded-xl border border-brand-navy/25 px-6 py-8 text-center dark:border-white/15"
            >
              <h3 className="font-heading text-lg font-bold">{topic.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{topic.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 className="text-center font-heading text-3xl font-bold sm:text-4xl">Who This Is For</h2>
        <div className="mt-10 grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-brand-navy/20 p-6 sm:p-8 dark:border-white/15">
            <h3 className="font-heading text-xl font-bold">This is for you if..</h3>
            <ul className="mt-6 space-y-4">
              {program.audienceFor.map((item) => (
                <li key={item} className="flex gap-3 text-base leading-relaxed">
                  <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-sm bg-emerald-500 text-white">
                    <Check className="size-3.5" strokeWidth={3} />
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl border border-brand-navy/20 p-6 sm:p-8 dark:border-white/15">
            <h3 className="font-heading text-xl font-bold">Not for you if..</h3>
            <ul className="mt-6 space-y-4">
              {program.audienceNotFor.map((item) => (
                <li key={item} className="flex gap-3 text-base leading-relaxed">
                  <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center text-red-500">
                    <X className="size-5" strokeWidth={2.5} />
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 className="text-center font-heading text-3xl font-bold sm:text-4xl">
          What You&apos;ll Achieve
        </h2>
        <div className="mt-10 grid items-center gap-10 lg:grid-cols-2">
          <div>
            <p className="font-heading text-xl font-semibold">{program.outcomesIntro}</p>
            <ul className="mt-6 list-disc space-y-3 pl-5 text-base leading-relaxed">
              {program.outcomes.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <p className="mt-6 font-semibold">{program.outcomeBonus}</p>
          </div>
          <div className="flex min-h-[260px] items-center justify-center rounded-2xl bg-brand-orange p-8">
            <div className="w-full max-w-xs overflow-hidden rounded-xl bg-card text-center text-card-foreground shadow-elevated">
              <div className="flex items-center justify-center gap-2 px-6 py-8">
                <Database className="size-8 text-brand-orange" />
                <span className="font-heading text-3xl font-bold">SQL</span>
              </div>
              <div className="bg-brand-navy px-4 py-3 text-sm font-semibold text-white">
                Blockchain Data Analytics
              </div>
            </div>
          </div>
        </div>

        <div id="work" className="mt-16 scroll-mt-24">
          <ProgramDuneGrid items={program.duneDashboards} />
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 className="text-center font-heading text-3xl font-bold sm:text-4xl">Testimonials</h2>
        <p className="mt-3 text-center text-muted-foreground">Real students. Real results.</p>
        <div className="mt-10">
          <ProgramTestimonialCarousel
            items={program.testimonials}
            moreUrl={program.moreTestimonialsUrl}
          />
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20">
        <h2 className="text-center font-heading text-3xl font-bold sm:text-4xl">Program Details</h2>
        <p className="mt-3 text-center text-muted-foreground">
          Everything you need to know about this blockchain data analyst course.
        </p>
        <dl className="mt-10 divide-y">
          {details.map(([label, value]) => (
            <div
              key={label}
              className="grid gap-1 py-4 sm:grid-cols-[12rem_1fr] sm:gap-8"
            >
              <dt className="font-semibold">{label}</dt>
              <dd className="text-muted-foreground">
                {value ?? (loading ? "Loading…" : "Published with the live cohort listing")}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20">
        <h2 className="text-center font-heading text-3xl font-bold sm:text-4xl">
          Frequently Asked Questions
        </h2>
        <Accordion className="mt-10">
          {program.faqs.map((faq) => (
            <AccordionItem key={faq.question} value={faq.question} className="border-0">
              <AccordionTrigger className="my-1 rounded-none bg-muted px-4 py-4 text-left text-base font-medium hover:no-underline">
                {faq.question}
              </AccordionTrigger>
              <AccordionContent className="px-4 pb-4 pt-2 text-base leading-relaxed text-muted-foreground">
                <p>{faq.answer}</p>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>

      <section id="register" className="scroll-mt-24 px-4 py-20 text-center sm:py-24">
        <h2 className="font-heading text-3xl font-bold sm:text-4xl">
          Your blockchain data journey starts here.
        </h2>
        <p className="mt-4 text-muted-foreground">
          {deadline
            ? `Cohort 9 registration closes ${deadline}.`
            : "Join Cohort 9 for structured, instructor-led SQL blockchain analytics."}
        </p>
        <ButtonLink
          href={checkoutHref}
          size="lg"
          className="mt-8 h-12 rounded-full bg-brand-orange px-10 text-base text-white hover:bg-brand-orange/90"
        >
          Register Now
          <span className="ml-2 flex size-6 items-center justify-center rounded-full bg-white text-brand-orange">
            <ArrowRight className="size-3.5" />
          </span>
        </ButtonLink>
      </section>

      <button
        type="button"
        aria-label="Back to top"
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        className="fixed right-5 bottom-24 z-40 flex size-11 items-center justify-center rounded-full bg-brand-navy text-white shadow-elevated md:bottom-24"
      >
        <ChevronUp className="size-5" />
      </button>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/95 p-3 backdrop-blur md:hidden">
        <ButtonLink
          href={checkoutHref}
          className="h-12 w-full rounded-full bg-brand-orange text-white hover:bg-brand-orange/90"
        >
          Register for Cohort 9
          {priceLabel ? ` · ${priceLabel}` : ""}
        </ButtonLink>
      </div>
    </div>
  );
}
