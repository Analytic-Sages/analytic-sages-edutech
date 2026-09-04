"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { ArrowRight, Calendar, Loader2 } from "lucide-react";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BDE_COHORT_SLUG, blockchainDataEngineeringProgram } from "@/lib/blockchain-data-engineering-program";
import { formatPrice } from "@/lib/mock-data";
import {
  getProgramPageHref,
  getProgramPostcard,
  listComingSoonPrograms,
  type ProgramPageContent,
} from "@/lib/program-pages";
import { listPublicCohorts, type PublicCohortCard } from "@/lib/api";

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

function ComingSoonCard({ program }: { program: ProgramPageContent }) {
  return (
    <Card className="overflow-hidden shadow-card">
      <div className="relative aspect-[16/10] bg-brand-surface">
        <Image
          src={program.postcardImage}
          alt={`${program.headline} postcard`}
          fill
          className="object-cover"
          sizes="(max-width: 1024px) 100vw, 33vw"
        />
      </div>
      <CardHeader>
        <div className="mb-2 flex flex-wrap gap-2">
          <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-semibold uppercase text-muted-foreground">
            Coming soon
          </span>
        </div>
        <CardTitle className="font-heading text-xl">{program.headline}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-muted-foreground">
        <p className="font-medium text-foreground/80">{program.support}</p>
        <p>
          {program.duration} · {program.timeCommitment}
        </p>
        <ButtonLink href={`/programs/${program.pageSlug}`} variant="outline" className="mt-2">
          Learn more
          <ArrowRight className="ml-2 size-4" />
        </ButtonLink>
      </CardContent>
    </Card>
  );
}

/** Shown when the live BDE cohort is not yet returned by the public API. */
function LiveEngineeringFallbackCard() {
  const program = blockchainDataEngineeringProgram;
  return (
    <Card className="overflow-hidden shadow-card">
      <div className="relative aspect-[16/10] bg-brand-surface">
        <Image
          src={program.postcardImage}
          alt={`${program.h1} postcard`}
          fill
          className="object-cover"
          sizes="(max-width: 1024px) 100vw, 33vw"
        />
      </div>
      <CardHeader>
        <div className="mb-2 flex flex-wrap gap-2">
          <span className="rounded-md bg-brand-orange/15 px-2 py-0.5 text-xs font-semibold uppercase text-brand-orange">
            Open for registration
          </span>
        </div>
        <CardTitle className="font-heading text-xl">{program.h1}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-muted-foreground">
        <p className="font-medium text-foreground/80">{program.support}</p>
        <p>
          {program.duration} · {program.timeCommitment}
        </p>
        <ButtonLink
          href={`/programs/${program.pageSlug}`}
          className="mt-2 bg-brand-orange text-white hover:bg-brand-orange/90"
        >
          View program
          <ArrowRight className="ml-2 size-4" />
        </ButtonLink>
      </CardContent>
    </Card>
  );
}

export function HomeInstructorLedSection() {
  const [cohorts, setCohorts] = useState<PublicCohortCard[]>([]);
  const [loading, setLoading] = useState(true);
  const comingSoon = listComingSoonPrograms();

  useEffect(() => {
    let cancelled = false;
    listPublicCohorts()
      .then((data) => {
        if (!cancelled) {
          // Prefer open cohorts; keep BDE first when present so it leads the grid.
          const sorted = [...data].sort((a, b) => {
            if (a.slug === BDE_COHORT_SLUG) return -1;
            if (b.slug === BDE_COHORT_SLUG) return 1;
            return 0;
          });
          setCohorts(sorted.slice(0, 2));
        }
      })
      .catch(() => {
        if (!cancelled) setCohorts([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const hasBdeFromApi = cohorts.some((cohort) => cohort.slug === BDE_COHORT_SLUG);
  const hasContent = cohorts.length > 0 || comingSoon.length > 0 || !hasBdeFromApi;

  return (
    <section className="relative border-y bg-brand-warm py-20 sm:py-28">
      <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-orange">
              Instructor-Led Training
            </p>
            <h2 className="mt-3 font-heading text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
              Learn live with experts
            </h2>
            <p className="mt-3 max-w-xl text-lg text-muted-foreground">
              Independent live programmes you can join when open. Learn live. Build together. Join
              the classroom when your session starts.
            </p>
          </div>
          <ButtonLink href="/instructor-led" variant="outline" className="shrink-0">
            View all training
            <ArrowRight className="ml-2 size-4" />
          </ButtonLink>
        </div>

        {loading ? (
          <div className="mt-12 flex items-center gap-2 text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
            Loading cohorts…
          </div>
        ) : !hasContent ? (
          <Card className="mt-12">
            <CardContent className="py-10 text-center text-muted-foreground">
              New cohorts will appear here as they open.{" "}
              <ButtonLink href="/contact" variant="link" className="h-auto px-0">
                Contact us
              </ButtonLink>
            </CardContent>
          </Card>
        ) : (
          <div className="mt-12 grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
            {!hasBdeFromApi ? <LiveEngineeringFallbackCard /> : null}
            {cohorts.map((cohort) => {
              const programHref = getProgramPageHref(cohort.slug);
              const postcard = getProgramPostcard(cohort.slug);
              return (
                <Card key={cohort.id} className="overflow-hidden shadow-card">
                  {postcard && (
                    <div className="relative aspect-[16/10] bg-brand-surface">
                      <Image
                        src={postcard}
                        alt={`${cohort.name} postcard`}
                        fill
                        className="object-cover"
                        sizes="(max-width: 1024px) 100vw, 33vw"
                      />
                    </div>
                  )}
                  <CardHeader>
                    <div className="mb-2 flex flex-wrap gap-2">
                      {cohort.next_session_phase === "live" ? (
                        <span className="inline-flex items-center gap-1.5 rounded-md bg-red-500/15 px-2 py-0.5 text-xs font-semibold uppercase text-red-600">
                          <span className="size-1.5 animate-pulse rounded-full bg-red-500" />
                          Live now
                        </span>
                      ) : (
                        <span className="rounded-md bg-brand-orange/15 px-2 py-0.5 text-xs font-semibold uppercase text-brand-orange">
                          Open for registration
                        </span>
                      )}
                    </div>
                    <CardTitle className="font-heading text-xl">{cohort.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm text-muted-foreground">
                    {cohort.description && (
                      <p className="font-medium text-foreground/80">{cohort.description}</p>
                    )}
                    {formatDate(cohort.registration_deadline) && (
                      <p>
                        Registration deadline: {formatDate(cohort.registration_deadline)}
                      </p>
                    )}
                    {formatDate(cohort.starts_at) && (
                      <p className="inline-flex items-center gap-1.5">
                        <Calendar className="size-3.5" />
                        Starts {formatDate(cohort.starts_at)}
                      </p>
                    )}
                    {cohort.price > 0 && (
                      <p className="font-medium text-foreground">
                        {formatPrice(cohort.price, cohort.currency)}
                      </p>
                    )}
                    <ButtonLink
                      href={programHref ?? "/instructor-led"}
                      className="mt-2 bg-brand-orange text-white hover:bg-brand-orange/90"
                    >
                      View program
                      <ArrowRight className="ml-2 size-4" />
                    </ButtonLink>
                  </CardContent>
                </Card>
              );
            })}
            {comingSoon.map((program) => (
              <ComingSoonCard key={program.pageSlug} program={program} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
