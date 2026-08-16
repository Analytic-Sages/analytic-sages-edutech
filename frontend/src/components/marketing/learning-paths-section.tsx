"use client";

import Link from "next/link";
import { ArrowRight, BookOpen, Radio } from "lucide-react";
import { ButtonLink } from "@/components/ui/button-link";

export function LearningPathsSection() {
  return (
    <section className="relative border-y py-20 sm:py-28">
      <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-wide text-brand-orange">
            Choose how you learn
          </p>
          <h2 className="mt-3 font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Two paths. One Analytic Sages platform.
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Join live expert-led cohorts now, or explore our on-demand library as it launches.
          </p>
        </div>

        <div className="mt-12 grid gap-6 lg:grid-cols-2 lg:gap-8">
          <PathCard
            eyebrow="01 — Instructor-Led"
            title="Learn live with experts"
            body="Scheduled cohorts, live classroom sessions, projects, and mentorship with your peer group."
            points={["Live classes", "Cohort community", "Mentorship"]}
            href="/instructor-led"
            cta="View upcoming training"
            icon={Radio}
            accent
          />
          <PathCard
            eyebrow="02 — Self-Paced"
            title="Learn on your schedule"
            body="On-demand lessons and projects you can complete anytime. Catalog is open; playback is launching soon."
            points={["On-demand lessons", "Hands-on projects", "Learn anytime"]}
            href="/courses"
            cta="Explore self-paced courses"
            icon={BookOpen}
          />
        </div>
      </div>
    </section>
  );
}

function PathCard({
  eyebrow,
  title,
  body,
  points,
  href,
  cta,
  icon: Icon,
  accent = false,
}: {
  eyebrow: string;
  title: string;
  body: string;
  points: string[];
  href: string;
  cta: string;
  icon: typeof Radio;
  accent?: boolean;
}) {
  return (
    <div
      className={
        accent
          ? "flex flex-col rounded-2xl border border-brand-navy/20 bg-gradient-to-br from-brand-navy to-brand-navy/90 p-8 text-white shadow-float sm:p-10"
          : "flex flex-col rounded-2xl border bg-card p-8 shadow-card sm:p-10"
      }
    >
      <div className="flex items-start justify-between gap-4">
        <p
          className={
            accent
              ? "font-heading text-2xl font-bold tracking-tight text-brand-orange sm:text-3xl lg:text-4xl"
              : "font-heading text-2xl font-bold tracking-tight text-brand-orange sm:text-3xl lg:text-4xl"
          }
        >
          {eyebrow}
        </p>
        <Icon className={accent ? "size-8 shrink-0 text-white/70 sm:size-10" : "size-8 shrink-0 text-muted-foreground sm:size-10"} />
      </div>
      <h3 className="mt-4 font-heading text-2xl font-bold sm:text-3xl">{title}</h3>
      <p className={accent ? "mt-3 text-white/85" : "mt-3 text-muted-foreground"}>{body}</p>
      <ul className="mt-6 space-y-2">
        {points.map((p) => (
          <li key={p} className={accent ? "text-sm text-white/90" : "text-sm text-foreground/90"}>
            · {p}
          </li>
        ))}
      </ul>
      <div className="mt-8">
        {accent ? (
          <ButtonLink
            href={href}
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            {cta}
            <ArrowRight className="ml-2 size-4" />
          </ButtonLink>
        ) : (
          <Link
            href={href}
            className="inline-flex items-center text-sm font-semibold text-brand-orange hover:underline"
          >
            {cta}
            <ArrowRight className="ml-1 size-4" />
          </Link>
        )}
      </div>
    </div>
  );
}
