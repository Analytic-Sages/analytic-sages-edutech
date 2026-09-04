"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Calendar, Loader2, Radio, Users } from "lucide-react";
import { SectionBackground } from "@/components/marketing/section-background";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, listPublicCohorts, type PublicCohortCard } from "@/lib/api";
import {
  BDE_COHORT_SLUG,
  blockchainDataEngineeringProgram,
} from "@/lib/blockchain-data-engineering-program";
import { formatPrice } from "@/lib/mock-data";
import {
  comingSoonCohortSlugs,
  getProgramPageHref,
  getProgramPostcard,
  listComingSoonPrograms,
  type ProgramPageContent,
} from "@/lib/program-pages";
import { cn } from "@/lib/utils";

function formatWhen(iso: string | null) {
  if (!iso) return null;
  try {
    return new Intl.DateTimeFormat(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

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

export function InstructorLedPageContent() {
  const [cohorts, setCohorts] = useState<PublicCohortCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const comingSoonPrograms = listComingSoonPrograms();
  const sortedCohorts = sortedOpenCohorts(cohorts);
  const hasBdeFromApi = cohorts.some((cohort) => cohort.slug === BDE_COHORT_SLUG);
  const showBdeFallback = !loading && !hasBdeFromApi;
  const hasProgrammes =
    sortedCohorts.length > 0 || comingSoonPrograms.length > 0 || showBdeFallback;

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await listPublicCohorts();
        if (!cancelled) {
          const blocked = comingSoonCohortSlugs();
          setCohorts(data.filter((cohort) => !blocked.has(cohort.slug)));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load upcoming cohorts");
          setCohorts([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="pb-16">
      <section className="relative overflow-hidden border-b">
        <SectionBackground variant="diamonds" />
        <div className="relative mx-auto max-w-screen-2xl px-4 py-16 sm:px-6 sm:py-24 lg:px-10">
          <p className="text-lg font-bold uppercase tracking-[0.12em] text-brand-orange">
            Instructor-Led Training
          </p>
          <h1 className="mt-4 max-w-3xl font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Learn live. Build together. Get mentored.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-muted-foreground sm:text-xl">
            Join scheduled expert-led cohorts with live classroom sessions, projects, and a learning
            community. Browse open programmes below. Each opens independently.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <ButtonLink href="/classroom" className="bg-brand-orange text-white hover:bg-brand-orange/90">
              Go to Classroom
            </ButtonLink>
            <ButtonLink href="/courses" variant="outline">
              Prefer self-paced?
            </ButtonLink>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-screen-2xl px-4 py-14 sm:px-6 lg:px-10">
        <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="font-heading text-2xl font-bold sm:text-3xl">Programmes</h2>
            <p className="mt-2 text-muted-foreground">
              Open cohorts and independent programmes marked Coming soon.
            </p>
          </div>
        </div>

        {loading && (
          <div className="flex items-center gap-2 py-16 text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
            Loading cohorts…
          </div>
        )}

        {!loading && error && (
          <p className="mb-6 text-sm text-muted-foreground">
            Live cohort details are temporarily unavailable. Open programmes below still reflect what
            we are offering.
          </p>
        )}

        {!loading && !hasProgrammes && (
          <Card>
            <CardContent className="py-10 text-center">
              <p className="font-heading text-lg font-semibold">New cohorts coming soon</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Check back shortly, or explore self-paced programs marked Launching soon.
              </p>
              <ButtonLink href="/courses" className="mt-6" variant="outline">
                Browse self-paced
              </ButtonLink>
            </CardContent>
          </Card>
        )}

        {!loading && hasProgrammes && (
          <div className="grid gap-6 lg:grid-cols-2">
            {showBdeFallback ? <OpenEngineeringProgramCard /> : null}
            {sortedCohorts.map((cohort) => (
              <CohortCard key={cohort.id} cohort={cohort} />
            ))}
            {comingSoonPrograms.map((program) => (
              <ComingSoonProgramCard key={program.pageSlug} program={program} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function sortedOpenCohorts(cohorts: PublicCohortCard[]) {
  return [...cohorts].sort((a, b) => {
    if (a.slug === BDE_COHORT_SLUG) return -1;
    if (b.slug === BDE_COHORT_SLUG) return 1;
    return 0;
  });
}

/** Shown when the live BDE cohort is not yet returned by the public API. */
function OpenEngineeringProgramCard() {
  const program = blockchainDataEngineeringProgram;
  return (
    <Card className="overflow-hidden shadow-card">
      <div className="relative aspect-[16/10] bg-brand-surface">
        <Image
          src={program.postcardImage}
          alt={`${program.h1} postcard`}
          fill
          className="object-cover"
          sizes="(max-width: 1024px) 100vw, 50vw"
        />
      </div>
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-brand-orange/15 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-brand-orange">
            Open for registration
          </span>
        </div>
        <CardTitle className="font-heading text-2xl">{program.h1}</CardTitle>
        <p className="text-base font-medium text-foreground/80">{program.support}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
          <p>
            <span className="font-medium text-foreground">Duration:</span> {program.duration}
          </p>
          <p>
            <span className="font-medium text-foreground">Time:</span> {program.timeCommitment}
          </p>
          <p>
            <span className="font-medium text-foreground">Tuition:</span> From $200
          </p>
          <p>
            <span className="font-medium text-foreground">Format:</span> {program.learningMode}
          </p>
        </div>
        <div className="flex flex-wrap gap-3 pt-2">
          <ButtonLink
            href={program.canonicalPath}
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            View program
            <ArrowRight className="ml-1 size-4" />
          </ButtonLink>
          <ButtonLink href="/classroom" variant="outline">
            Open Classroom
          </ButtonLink>
        </div>
      </CardContent>
    </Card>
  );
}

function ComingSoonProgramCard({ program }: { program: ProgramPageContent }) {
  return (
    <Card className="overflow-hidden shadow-card">
      <div className="relative aspect-[16/10] bg-brand-surface">
        <Image
          src={program.postcardImage}
          alt={`${program.headline} postcard`}
          fill
          className="object-cover"
          sizes="(max-width: 1024px) 100vw, 50vw"
        />
      </div>
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Coming soon
          </span>
          <span className="rounded-md bg-brand-orange/15 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-brand-orange">
            Instructor-Led
          </span>
        </div>
        <CardTitle className="font-heading text-2xl">{program.headline}</CardTitle>
        <p className="text-base font-medium text-foreground/80">{program.support}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
          <p>
            <span className="font-medium text-foreground">Duration:</span> {program.duration}
          </p>
          <p>
            <span className="font-medium text-foreground">Time:</span> {program.timeCommitment}
          </p>
        </div>
        <ButtonLink href={`/programs/${program.pageSlug}`} variant="outline">
          Learn more
          <ArrowRight className="ml-1 size-4" />
        </ButtonLink>
      </CardContent>
    </Card>
  );
}

function CohortCard({ cohort }: { cohort: PublicCohortCard }) {
  const when = formatWhen(cohort.next_session_starts_at);
  const isLive = cohort.next_session_phase === "live";
  const programHref = getProgramPageHref(cohort.slug);
  const postcard = getProgramPostcard(cohort.slug);

  return (
    <Card className="overflow-hidden shadow-card">
      {postcard && (
        <div className="relative aspect-[16/10] bg-brand-surface">
          <Image
            src={postcard}
            alt={`${cohort.name} postcard`}
            fill
            className="object-cover"
            sizes="(max-width: 1024px) 100vw, 50vw"
          />
        </div>
      )}
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-brand-orange/15 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-brand-orange">
            Open for registration
          </span>
          {isLive && (
            <span className="inline-flex items-center gap-1.5 rounded-md bg-red-500/15 px-2 py-0.5 text-xs font-semibold uppercase text-red-600 dark:text-red-300">
              <span className="size-1.5 animate-pulse rounded-full bg-red-500" />
              Session live now
            </span>
          )}
        </div>
        <CardTitle className="font-heading text-2xl">{cohort.name}</CardTitle>
        {cohort.description && (
          <p className="text-base font-medium text-foreground/80">{cohort.description}</p>
        )}
        {cohort.course_title && (
          <p className="text-sm text-muted-foreground">{cohort.course_title}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
          {formatDate(cohort.registration_deadline) && (
            <p>
              <span className="font-medium text-foreground">Registration deadline:</span>{" "}
              {formatDate(cohort.registration_deadline)}
            </p>
          )}
          {formatDate(cohort.starts_at) && (
            <p>
              <span className="font-medium text-foreground">Start date:</span>{" "}
              {formatDate(cohort.starts_at)}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <Users className="size-3.5" />
            {cohort.sessions_count} session{cohort.sessions_count === 1 ? "" : "s"}
          </span>
          {when && (
            <span className="inline-flex items-center gap-1.5">
              <Calendar className="size-3.5" />
              {isLive ? "Live now" : `Next: ${when}`}
            </span>
          )}
          {cohort.next_session_title && (
            <span className="inline-flex items-center gap-1.5">
              <Radio className="size-3.5" />
              {cohort.next_session_title}
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-3 pt-2">
          {programHref ? (
            <ButtonLink
              href={programHref}
              className={cn("bg-brand-orange text-white hover:bg-brand-orange/90")}
            >
              View program
              <ArrowRight className="ml-1 size-4" />
            </ButtonLink>
          ) : cohort.price > 0 ? (
            <ButtonLink
              href={`/checkout/cohort/${cohort.slug}`}
              className={cn("bg-brand-orange text-white hover:bg-brand-orange/90")}
            >
              Register · {formatPrice(cohort.price, cohort.currency)}
              <ArrowRight className="ml-1 size-4" />
            </ButtonLink>
          ) : (
            <ButtonLink
              href="/register?next=/classroom"
              className={cn("bg-brand-orange text-white hover:bg-brand-orange/90")}
            >
              Get started
              <ArrowRight className="ml-1 size-4" />
            </ButtonLink>
          )}
          <ButtonLink href="/classroom" variant="outline">
            Open Classroom
          </ButtonLink>
          {cohort.course_slug && (
            <Link
              href={`/courses/${cohort.course_slug}`}
              className="inline-flex items-center text-sm font-medium text-brand-orange hover:underline"
            >
              View curriculum outline
            </Link>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
