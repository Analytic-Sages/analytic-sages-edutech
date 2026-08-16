"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { ButtonLink } from "@/components/ui/button-link";
import { getAccessToken } from "@/lib/api";
import { getContinueHref } from "@/lib/course-paths";
import { fetchEnrolledCourses } from "@/lib/enrollments";
import { formatPrice, getCourseBySlug, isCourseLive } from "@/lib/mock-data";
import { siteConfig } from "@/config/site";
import type { Course } from "@/types/course";

type Props = {
  slug: string;
  price: number;
  currency: string;
  comingSoon?: boolean;
};

export function CourseEnrollCta({ slug, price, currency, comingSoon }: Props) {
  const [loading, setLoading] = useState(true);
  const [enrolledCourse, setEnrolledCourse] = useState<Course | null>(null);
  const isComingSoon = comingSoon ?? !isCourseLive(slug);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!getAccessToken()) {
        if (!cancelled) {
          setEnrolledCourse(null);
          setLoading(false);
        }
        return;
      }

      try {
        const enrolled = await fetchEnrolledCourses();
        const match = enrolled.find((item) => item.course.slug === slug)?.course ?? null;
        if (!cancelled) setEnrolledCourse(match);
      } catch {
        if (!cancelled) setEnrolledCourse(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (loading) {
    return (
      <div className="mt-8 flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Checking enrollment…
      </div>
    );
  }

  if (enrolledCourse) {
    const mock = getCourseBySlug(slug);
    const courseForPlayer: Course = {
      ...enrolledCourse,
      modules: enrolledCourse.modules.length > 0 ? enrolledCourse.modules : mock?.modules ?? [],
    };

    return (
      <div className="mt-8 flex flex-col items-start gap-4 sm:flex-row sm:items-center">
        <span className="rounded-lg bg-success/10 px-3 py-1.5 text-sm font-medium text-success">
          You&apos;re enrolled
        </span>
        <ButtonLink
          href={getContinueHref(courseForPlayer)}
          size="lg"
          className="bg-brand-orange text-white hover:bg-brand-orange/90"
        >
          Continue learning
        </ButtonLink>
      </div>
    );
  }

  if (isComingSoon) {
    return (
      <div className="mt-8 space-y-4">
        <span className="inline-flex rounded-full bg-brand-orange/10 px-4 py-1.5 text-sm font-semibold text-brand-orange">
          Launching soon
        </span>
        <p className="max-w-md text-sm text-muted-foreground">
          Self-paced enrollment is launching soon. For live expert-led training, see our
          Instructor-Led cohorts, or email{" "}
          <a href={`mailto:${siteConfig.emails.hello}`} className="text-brand-orange hover:underline">
            {siteConfig.emails.hello}
          </a>{" "}
          to get notified.
        </p>
        <ButtonLink href="/instructor-led" size="lg" variant="outline">
          View Instructor-Led Training
        </ButtonLink>
      </div>
    );
  }

  return (
    <div className="mt-8 flex flex-col items-start gap-4 sm:flex-row sm:items-center">
      <span className="font-heading text-3xl font-bold text-brand-navy dark:text-brand-orange">
        {formatPrice(price, currency)}
      </span>
      <ButtonLink
        href={`/checkout/${slug}`}
        size="lg"
        className="bg-brand-orange text-white hover:bg-brand-orange/90"
      >
        Enroll Now
      </ButtonLink>
    </div>
  );
}
