"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BDE_COHORT_SLUG,
  blockchainDataEngineeringProgram,
} from "@/lib/blockchain-data-engineering-program";
import {
  listPublicCohorts,
  listSelfPacedCourses,
  type PublicCohortCard,
  type SelfPacedCourseCard,
} from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";
import {
  comingSoonCohortSlugs,
  getProgramPageHref,
  getProgramPostcard,
} from "@/lib/program-pages";
import { FEATURED_FREE_COURSE, mergeFreeCatalog } from "@/lib/self-paced";

type LearningOffer = {
  id: string;
  title: string;
  href: string;
  image: string;
  badge: string;
  subtitle?: string;
};

const MAX_OFFERS = 3;

function cohortOffer(cohort: PublicCohortCard): LearningOffer | null {
  const href = getProgramPageHref(cohort.slug);
  const image = getProgramPostcard(cohort.slug);
  if (!href || !image) return null;
  const paid = cohort.price > 0;
  return {
    id: `cohort-${cohort.id}`,
    title: cohort.course_title || cohort.name,
    href,
    image,
    badge: paid ? "Paid · Open" : "Free · Open",
    subtitle: paid ? formatPrice(cohort.price, cohort.currency) : "Instructor-led",
  };
}

function courseOffer(course: SelfPacedCourseCard): LearningOffer {
  return {
    id: `course-${course.slug}`,
    title: course.title,
    href: `/courses/${course.slug}`,
    image: course.thumbnail || "/4.png",
    badge: course.is_free || course.price === 0 ? "Free" : "Paid",
    subtitle: course.duration || undefined,
  };
}

function bdeFallbackOffer(): LearningOffer {
  const program = blockchainDataEngineeringProgram;
  return {
    id: "program-bde",
    title: program.h1,
    href: `/programs/${program.pageSlug}`,
    image: program.postcardImage,
    badge: "Paid · Open",
    subtitle: `${program.duration} · Instructor-led`,
  };
}

function buildOffers(
  relatedSlug: string | null | undefined,
  courses: SelfPacedCourseCard[],
  cohorts: PublicCohortCard[],
): LearningOffer[] {
  const offers: LearningOffer[] = [];
  const seen = new Set<string>();

  const push = (offer: LearningOffer | null) => {
    if (!offer || seen.has(offer.href) || offers.length >= MAX_OFFERS) return;
    seen.add(offer.href);
    offers.push(offer);
  };

  if (relatedSlug) {
    const related =
      courses.find((course) => course.slug === relatedSlug) ||
      (relatedSlug === FEATURED_FREE_COURSE.slug ? FEATURED_FREE_COURSE : null);
    if (related) {
      push(courseOffer(related));
    } else {
      push({
        id: `related-${relatedSlug}`,
        title: "Continue with the related course",
        href: `/courses/${relatedSlug}`,
        image: "/4.png",
        badge: "Course",
      });
    }
  }

  for (const course of mergeFreeCatalog(courses)) {
    push(courseOffer(course));
  }

  const blocked = comingSoonCohortSlugs();
  const openCohorts = cohorts
    .filter((cohort) => !blocked.has(cohort.slug) && (cohort.status === "open" || cohort.status === "active"))
    .sort((a, b) => {
      if (a.slug === BDE_COHORT_SLUG) return -1;
      if (b.slug === BDE_COHORT_SLUG) return 1;
      return 0;
    });

  for (const cohort of openCohorts) {
    push(cohortOffer(cohort));
  }

  if (!offers.some((offer) => offer.href.includes(blockchainDataEngineeringProgram.pageSlug))) {
    if (blockchainDataEngineeringProgram.registrationLive) {
      push(bdeFallbackOffer());
    }
  }

  return offers;
}

function OfferCard({ offer }: { offer: LearningOffer }) {
  return (
    <Link
      href={offer.href}
      className="group block overflow-hidden rounded-xl border bg-background transition-colors hover:border-brand-orange/40"
    >
      <div className="relative aspect-[16/10] bg-brand-surface">
        <Image
          src={offer.image}
          alt={offer.title}
          fill
          className="object-cover transition-transform duration-300 group-hover:scale-[1.02]"
          sizes="(max-width: 1024px) 100vw, 280px"
        />
      </div>
      <div className="space-y-2 p-3">
        <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
          {offer.badge}
        </Badge>
        <p className="line-clamp-2 text-sm font-medium leading-snug text-foreground group-hover:text-brand-navy">
          {offer.title}
        </p>
        {offer.subtitle ? (
          <p className="text-xs text-muted-foreground">{offer.subtitle}</p>
        ) : null}
        <p className="text-xs font-medium text-brand-orange">View details</p>
      </div>
    </Link>
  );
}

export function EventKeepLearning({ relatedCourseSlug }: { relatedCourseSlug?: string | null }) {
  const [offers, setOffers] = useState<LearningOffer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      listSelfPacedCourses().catch(() => [] as SelfPacedCourseCard[]),
      listPublicCohorts().catch(() => [] as PublicCohortCard[]),
    ])
      .then(([courses, cohorts]) => {
        if (!cancelled) setOffers(buildOffers(relatedCourseSlug, courses, cohorts));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [relatedCourseSlug]);

  if (!loading && offers.length === 0) return null;

  return (
    <Card className="shadow-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Keep learning</CardTitle>
        <p className="text-sm text-muted-foreground">
          Free courses and open programmes you can join next.
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? (
          <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading offers…
          </div>
        ) : (
          offers.map((offer) => <OfferCard key={offer.id} offer={offer} />)
        )}
      </CardContent>
    </Card>
  );
}
