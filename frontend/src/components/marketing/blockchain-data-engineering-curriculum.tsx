import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import { ButtonLink } from "@/components/ui/button-link";
import type { EngineeringProgramPageContent } from "@/lib/blockchain-data-engineering-program";

export function BlockchainDataEngineeringCurriculum({
  program,
}: {
  program: EngineeringProgramPageContent;
}) {
  const { curriculum } = program;
  const checkoutHref = `/checkout/cohort/${program.cohortSlug}`;

  return (
    <div className="bg-background pb-20 text-foreground">
      <section className="border-b border-border/60 bg-[#0B1F3A] text-white">
        <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6 sm:py-20 lg:px-8">
          <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-orange">
            Full curriculum · {program.learningMode}
          </p>
          <h1 className="mt-3 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
            {program.h1} Curriculum
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-white/80">{curriculum.intro}</p>
          <p className="mt-6 text-sm font-medium tracking-wide text-brand-orange">
            {program.programSignal}
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <ButtonLink
              href={checkoutHref}
              className="h-11 bg-brand-orange text-white hover:bg-brand-orange/90"
            >
              Join the Next Cohort
              <ArrowRight className="ml-2 size-4" />
            </ButtonLink>
            <ButtonLink
              href={program.canonicalPath}
              variant="outline"
              className="h-11 border-white/30 bg-transparent text-white hover:bg-white/10"
            >
              Back to programme overview
            </ButtonLink>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
        <h2 className="font-heading text-2xl font-bold sm:text-3xl">Modules</h2>
        <div className="mt-8 space-y-10">
          {curriculum.modules.map((mod) => (
            <article key={mod.number} className="border-t border-border/70 pt-8">
              <p className="font-mono text-sm font-semibold text-brand-orange">{mod.number}</p>
              <h3 className="mt-2 font-heading text-xl font-bold sm:text-2xl">{mod.title}</h3>
              <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                {mod.body}
              </p>
              <ul className="mt-5 grid gap-2 sm:grid-cols-2">
                {mod.topics.map((topic) => (
                  <li key={topic} className="flex gap-2 text-sm">
                    <Check className="mt-0.5 size-4 shrink-0 text-brand-orange" strokeWidth={2.5} />
                    {topic}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section className="border-y border-border/60 bg-[#F7F9FC] dark:bg-transparent">
        <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
          <h2 className="font-heading text-2xl font-bold sm:text-3xl">Technology stack</h2>
          <div className="mt-8 space-y-6">
            {program.stackTiers.map((tier) => (
              <div key={tier.label}>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">
                  {tier.label}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {tier.tools.map((tool) => (
                    <span
                      key={tool}
                      className="border border-[#0B1F3A]/15 bg-background px-3 py-1.5 font-mono text-sm dark:border-white/15"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
        <h2 className="font-heading text-2xl font-bold sm:text-3xl">10-week curriculum</h2>
        <p className="mt-3 max-w-2xl text-muted-foreground">
          {program.programSignal}. Each week includes live sessions, practical exercises and
          progressive project work.
        </p>
        <div className="mt-10 space-y-14">
          {curriculum.weeks.map((week) => (
            <article key={week.week} id={`week-${week.week}`} className="scroll-mt-24">
              <div className="border-t border-border/70 pt-8">
                <p className="font-mono text-sm font-semibold text-brand-orange">
                  Week {week.week}
                </p>
                <h3 className="mt-2 font-heading text-2xl font-bold">{week.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{week.focus}</p>
                <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Tools: {week.tools.join(" · ")}
                </p>

                <h4 className="mt-8 text-sm font-semibold uppercase tracking-wide text-[#0B1F3A] dark:text-foreground">
                  Learning objectives
                </h4>
                <ul className="mt-3 space-y-2">
                  {week.objectives.map((item) => (
                    <li key={item} className="flex gap-2 text-sm text-muted-foreground">
                      <Check className="mt-0.5 size-4 shrink-0 text-brand-orange" strokeWidth={2.5} />
                      {item}
                    </li>
                  ))}
                </ul>

                <h4 className="mt-8 text-sm font-semibold uppercase tracking-wide text-[#0B1F3A] dark:text-foreground">
                  Sessions
                </h4>
                <ol className="mt-3 divide-y divide-border/60 border-y border-border/60">
                  {week.sessions.map((session) => (
                    <li key={session.number} className="grid gap-1 py-4 sm:grid-cols-[4.5rem_1fr]">
                      <span className="font-mono text-xs font-semibold text-brand-orange">
                        S{session.number}
                      </span>
                      <div>
                        <p className="text-sm font-semibold">{session.title}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{session.summary}</p>
                      </div>
                    </li>
                  ))}
                </ol>

                <h4 className="mt-8 text-sm font-semibold uppercase tracking-wide text-[#0B1F3A] dark:text-foreground">
                  Practical exercises
                </h4>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {week.exercises.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>

                {week.project ? (
                  <p className="mt-6 border-l-2 border-brand-orange/50 pl-4 text-sm">
                    <span className="font-semibold text-foreground">Project: </span>
                    <span className="text-muted-foreground">{week.project}</span>
                  </p>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="border-t border-border/60 bg-[#0B1F3A] text-white">
        <div className="mx-auto max-w-3xl px-4 py-14 text-center sm:px-6 sm:py-16">
          <h2 className="font-heading text-2xl font-bold sm:text-3xl">Facilitator structure</h2>
          <p className="mt-2 text-sm font-semibold uppercase tracking-wide text-brand-orange">
            {program.learningMode}
          </p>
          <p className="mt-4 text-sm leading-relaxed text-white/75">{curriculum.facilitatorNote}</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink
              href={checkoutHref}
              className="h-11 bg-brand-orange text-white hover:bg-brand-orange/90"
            >
              Join the Next Cohort
              <ArrowRight className="ml-2 size-4" />
            </ButtonLink>
            <Link
              href={program.canonicalPath}
              className="inline-flex h-11 items-center px-4 text-sm text-white/80 underline-offset-4 hover:underline"
            >
              Programme overview
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
