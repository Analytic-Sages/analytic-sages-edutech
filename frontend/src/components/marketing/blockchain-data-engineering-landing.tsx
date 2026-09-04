"use client";

import Image from "next/image";
import { ArrowRight, Check, ChevronUp, Loader2 } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { ButtonLink } from "@/components/ui/button-link";
import { BlockchainDataEngineeringStackExplorer } from "@/components/marketing/blockchain-data-engineering-stack-explorer";
import { useCohortRegistration } from "@/hooks/use-cohort-registration";
import type { EngineeringProgramPageContent } from "@/lib/blockchain-data-engineering-program";

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

export function BlockchainDataEngineeringLanding({
  program,
}: {
  program: EngineeringProgramPageContent;
}) {
  const { cohort, loading, open, checkoutHref, priceLabel, tuitionSummary } =
    useCohortRegistration(program.cohortSlug, program.tuitionSummary);

  const curriculumHref = program.curriculumPath;
  const startDate = formatDate(cohort?.starts_at ?? null);
  const deadline = formatDate(cohort?.registration_deadline ?? null);
  const primaryHref = open ? checkoutHref : curriculumHref;
  const primaryLabel = open ? program.applyLabel : "View Curriculum";

  return (
    <div className="bg-background pb-24 text-foreground md:pb-0">
      {/* 1. Hero */}
      <section className="relative overflow-hidden border-b border-[#0B1F3A]/10">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-[#0B1F3A] via-[#122A4A] to-[#0B1F3A]" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(241,90,36,0.22),transparent_45%)]" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:py-24">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-orange">
              {program.eyebrow}
            </p>
            <h1 className="mt-4 font-heading text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-[3.15rem] lg:leading-[1.1]">
              {program.h1}
            </h1>
            <h2 className="mt-4 font-heading text-2xl font-semibold tracking-tight text-white/95 sm:text-3xl">
              {program.salesHeadline}
            </h2>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-white/80">
              {program.heroBody}
            </p>
            <p className="mt-5 text-sm font-medium tracking-wide text-brand-orange">
              {program.programSignal}
            </p>
            <p className="mt-2 text-sm text-white/65">{program.learningMode}</p>

            <div className="mt-8 max-w-md rounded-lg border border-white/15 bg-white/5 px-4 py-4 backdrop-blur-sm">
              {loading ? (
                <p className="inline-flex items-center gap-2 text-sm text-white/70">
                  <Loader2 className="size-4 animate-spin" />
                  Checking registration…
                </p>
              ) : (
                <>
                  <p className="font-heading text-3xl font-bold tracking-tight text-white sm:text-4xl">
                    {priceLabel}
                  </p>
                  {open ? (
                    <>
                      <p className="mt-1 text-sm font-medium text-brand-orange">
                        Open for registration
                      </p>
                      {tuitionSummary ? (
                        <p className="mt-2 text-sm leading-relaxed text-white/80">
                          {tuitionSummary}
                        </p>
                      ) : (
                        <p className="mt-2 text-sm text-white/75">
                          One-time payment at checkout via Paystack or crypto.
                        </p>
                      )}
                      {deadline ? (
                        <p className="mt-2 text-xs text-white/55">
                          Registration deadline: {deadline}
                          {startDate ? ` · Starts ${startDate}` : null}
                        </p>
                      ) : null}
                    </>
                  ) : (
                    <p className="mt-2 text-sm leading-relaxed text-white/75">
                      Registration isn&apos;t open for this cohort right now. You can still review
                      the curriculum — checkout unlocks when seats are available.
                    </p>
                  )}
                </>
              )}
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink
                href={primaryHref}
                size="lg"
                className="h-12 bg-brand-orange px-8 text-base text-white hover:bg-brand-orange/90"
              >
                {primaryLabel}
                <ArrowRight className="ml-2 size-4" />
              </ButtonLink>
              {open ? (
                <ButtonLink
                  href={curriculumHref}
                  size="lg"
                  variant="outline"
                  className="h-12 border-white/30 bg-transparent px-8 text-base text-white hover:bg-white/10"
                >
                  View Curriculum
                </ButtonLink>
              ) : (
                <ButtonLink
                  href="/instructor-led"
                  size="lg"
                  variant="outline"
                  className="h-12 border-white/30 bg-transparent px-8 text-base text-white hover:bg-white/10"
                >
                  Instructor-Led programmes
                </ButtonLink>
              )}
            </div>
          </div>
          <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
            <div className="relative aspect-[16/10] overflow-hidden border border-white/10 shadow-float">
              <Image
                src={program.postcardImage}
                alt="Blockchain Data Engineering programme"
                fill
                className="object-cover"
                priority
                sizes="(max-width: 1024px) 100vw, 45vw"
              />
            </div>
          </div>
        </div>
      </section>

      {/* 2. Problem / opportunity */}
      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl">
          {program.problemTitle}
        </h2>
        <p className="mt-4 max-w-3xl text-base leading-relaxed text-muted-foreground">
          {program.problemSupport}
        </p>
        <p className="mt-8 text-sm font-semibold uppercase tracking-wide text-brand-orange">
          {program.processChain.join(" → ")}
        </p>
        <p className="mt-6 max-w-3xl font-heading text-xl font-semibold text-[#0B1F3A] dark:text-foreground">
          Blockchain Data Engineers build the systems that make this possible.
        </p>
      </section>

      {/* 3. Definition */}
      <section className="border-y border-border/60 bg-[#F7F9FC] dark:bg-transparent">
        <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
          <h2 className="font-heading text-3xl font-bold sm:text-4xl">{program.definitionTitle}</h2>
          <p className="mt-4 max-w-3xl text-base leading-relaxed text-muted-foreground">
            {program.definitionBody}
          </p>
          <ul className="mt-8 grid gap-3 sm:grid-cols-2">
            {program.definitionItems.map((item) => (
              <li key={item} className="flex gap-3 text-sm leading-relaxed">
                <Check className="mt-0.5 size-4 shrink-0 text-brand-orange" strokeWidth={2.5} />
                {item}
              </li>
            ))}
          </ul>
          <p className="mt-10 max-w-3xl font-heading text-lg font-semibold text-[#0B1F3A] dark:text-foreground">
            {program.positioningPhrase}
          </p>
        </div>
      </section>

      {/* 4. Systems flow */}
      <section className="bg-[#0B1F3A] text-white">
        <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
          <h2 className="font-heading text-3xl font-bold sm:text-4xl">{program.systemsTitle}</h2>
          <p className="mt-2 text-sm font-semibold uppercase tracking-wide text-brand-orange">
            {program.learningMode}
          </p>
          <p className="mt-4 max-w-2xl text-white/75">{program.systemsIntro}</p>
          <ol className="mt-12 space-y-0">
            {program.systemsFlow.map((layer, index) => (
              <li key={layer} className="flex gap-4">
                <div className="flex w-10 flex-col items-center">
                  <span className="flex size-10 items-center justify-center rounded-full border border-brand-orange/50 bg-brand-orange/15 text-sm font-semibold text-brand-orange">
                    {index + 1}
                  </span>
                  {index < program.systemsFlow.length - 1 ? (
                    <span className="my-1 w-px flex-1 bg-white/20" />
                  ) : null}
                </div>
                <p className="pb-6 pt-2 font-heading text-lg font-semibold tracking-wide">
                  {layer}
                </p>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-sm font-semibold uppercase tracking-wide text-brand-orange">
            {program.journey.join(" → ")}
          </p>
        </div>
      </section>

      {/* 5. What you'll build */}
      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 className="font-heading text-3xl font-bold sm:text-4xl">{program.buildsTitle}</h2>
        <p className="mt-3 max-w-2xl text-muted-foreground">{program.support}</p>
        <ul className="mt-10 divide-y divide-border/70 border-y border-border/70">
          {program.builds.map((item) => (
            <li key={item.title} className="grid gap-2 py-5 sm:grid-cols-[16rem_1fr] sm:gap-8">
              <p className="font-heading text-lg font-semibold">{item.title}</p>
              <p className="text-sm leading-relaxed text-muted-foreground">{item.body}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* 6. Stack */}
      <BlockchainDataEngineeringStackExplorer
        title={program.stackTitle}
        intro={program.stackIntro}
        curriculumHref={program.curriculumPath}
      />

      {/* 7. Who for */}
      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 className="font-heading text-3xl font-bold sm:text-4xl">{program.personasTitle}</h2>
        <ul className="mt-8 grid gap-3 sm:grid-cols-2">
          {program.personas.map((persona) => (
            <li key={persona} className="flex gap-3 text-sm leading-relaxed">
              <Check className="mt-0.5 size-4 shrink-0 text-brand-orange" strokeWidth={2.5} />
              {persona}
            </li>
          ))}
        </ul>
      </section>

      {/* 8. Careers */}
      <section className="border-y border-border/60 bg-[#F7F9FC] dark:bg-transparent">
        <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
          <h2 className="font-heading text-3xl font-bold sm:text-4xl">{program.careersTitle}</h2>
          <p className="mt-3 max-w-2xl text-muted-foreground">{program.careersIntro}</p>
          <ul className="mt-8 grid gap-3 sm:grid-cols-2">
            {program.careers.map((role) => (
              <li key={role} className="flex gap-3 text-sm leading-relaxed">
                <Check className="mt-0.5 size-4 shrink-0 text-brand-orange" strokeWidth={2.5} />
                {role}
              </li>
            ))}
          </ul>
          <p className="mt-8 max-w-3xl text-sm leading-relaxed text-muted-foreground">
            {program.careersNote}
          </p>
        </div>
      </section>

      {/* 9. Outcomes */}
      <section className="bg-[#0B1F3A] text-white">
        <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
          <h2 className="font-heading text-3xl font-bold sm:text-4xl">{program.outcomesTitle}</h2>
          <p className="mt-3 max-w-2xl text-white/75">
            By the end of the programme, you should have practical experience with:
          </p>
          <ul className="mt-8 grid gap-3 sm:grid-cols-2">
            {program.outcomes.map((item) => (
              <li key={item} className="flex gap-3 text-sm leading-relaxed text-white/90">
                <Check className="mt-0.5 size-4 shrink-0 text-brand-orange" strokeWidth={2.5} />
                {item}
              </li>
            ))}
          </ul>
          <p className="mt-10 font-heading text-xl font-semibold">
            Most importantly: you&apos;ll have built things.
          </p>
        </div>
      </section>

      {/* 10. Curriculum preview */}
      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 className="font-heading text-3xl font-bold sm:text-4xl">
          {program.curriculumPreviewTitle}
        </h2>
        <p className="mt-3 max-w-2xl text-sm font-medium text-[#0B1F3A] dark:text-foreground">
          {program.programSignal}
        </p>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          {program.learningMode} — each module builds on the last until you can ship a connected
          system.
        </p>
        <ol className="mt-10 divide-y divide-border/70 border-y border-border/70">
          {program.curriculumPreview.map((item) => (
            <li
              key={item.range}
              className="grid gap-1 py-5 sm:grid-cols-[8rem_1fr] sm:items-baseline sm:gap-8"
            >
              <span className="font-mono text-sm font-semibold text-brand-orange">{item.range}</span>
              <span className="font-heading text-lg font-semibold">{item.title}</span>
            </li>
          ))}
        </ol>
        <p className="mt-6 font-heading text-lg font-semibold text-[#0B1F3A] dark:text-foreground">
          {program.curriculumPreviewClose}
        </p>
        <ButtonLink
          href={curriculumHref}
          className="mt-6 bg-transparent px-0 text-brand-orange hover:bg-transparent hover:underline"
        >
          View Full Curriculum
          <ArrowRight className="ml-2 size-4" />
        </ButtonLink>
      </section>

      {/* 11. Pricing */}
      <section id="register" className="scroll-mt-24 border-t border-border/60 bg-[#F7F9FC] dark:bg-transparent">
        <div className="mx-auto max-w-3xl px-4 py-16 text-center sm:px-6 sm:py-20">
          <h2 className="font-heading text-3xl font-bold sm:text-4xl">Pricing & payment</h2>
          {loading ? (
            <p className="mt-8 inline-flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Loading cohort pricing…
            </p>
          ) : (
            <div className="mt-10 border border-border/70 bg-background px-6 py-8 sm:px-10">
              <p className="font-heading text-4xl font-bold text-[#0B1F3A] dark:text-foreground">
                {priceLabel}
              </p>
              <p className="mt-2 text-sm font-medium text-[#0B1F3A]/80 dark:text-foreground/80">
                {program.programSignal}
              </p>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                {tuitionSummary ?? program.tuitionSummary}
              </p>
              <p className="mt-3 text-sm text-muted-foreground">{program.paymentOptions}</p>
              <p className="mt-4 text-sm text-muted-foreground">
                {[
                  open ? "Open for registration" : "Registration not open yet",
                  deadline ? `Closes ${deadline}` : null,
                  startDate ? `Starts ${startDate}` : null,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              <ButtonLink
                href={primaryHref}
                size="lg"
                className="mt-8 h-12 bg-brand-orange px-10 text-base text-white hover:bg-brand-orange/90"
              >
                {primaryLabel}
                <ArrowRight className="ml-2 size-4" />
              </ButtonLink>
              {open ? (
                <p className="mt-4 text-xs text-muted-foreground">
                  Choose your tuition plan and pay with Paystack or crypto on the checkout page.
                </p>
              ) : null}
            </div>
          )}
        </div>
      </section>

      {/* FAQ */}
      <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20">
        <h2 className="text-center font-heading text-3xl font-bold sm:text-4xl">FAQ</h2>
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

      {/* Final CTA */}
      <section className="px-4 py-20 text-center sm:py-24">
        <p className="text-sm font-semibold uppercase tracking-wide text-brand-orange">
          Don&apos;t just analyse the blockchain.
        </p>
        <h2 className="mt-3 font-heading text-3xl font-bold sm:text-4xl">
          Build the infrastructure behind it.
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-muted-foreground">{program.positioningPhrase}</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <ButtonLink
            href={primaryHref}
            size="lg"
            className="h-12 bg-brand-orange px-10 text-base text-white hover:bg-brand-orange/90"
          >
            {primaryLabel}
            <ArrowRight className="ml-2 size-4" />
          </ButtonLink>
          {open ? (
            <ButtonLink href={curriculumHref} size="lg" variant="outline" className="h-12 px-8">
              View Curriculum
            </ButtonLink>
          ) : (
            <ButtonLink href="/instructor-led" size="lg" variant="outline" className="h-12 px-8">
              Instructor-Led programmes
            </ButtonLink>
          )}
        </div>
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
          href={primaryHref}
          className="h-12 w-full bg-brand-orange text-white hover:bg-brand-orange/90"
        >
          {open ? `Join cohort · ${priceLabel}` : "View Curriculum"}
        </ButtonLink>
      </div>
    </div>
  );
}
