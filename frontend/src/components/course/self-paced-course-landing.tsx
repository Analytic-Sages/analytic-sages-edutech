"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, Circle, Lock, PlayCircle } from "lucide-react";
import { InstructorRoster } from "@/components/marketing/instructor-roster";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { catalogIsFree, catalogPriceLabel } from "@/lib/catalog-price";
import {
  ApiError,
  clearAccessToken,
  enrollSelfPacedCourse,
  getAccessToken,
  getSelfPacedCourse,
  type SelfPacedCoursePublic,
  type SelfPacedLessonOutline,
} from "@/lib/api";
import { firstLessonSlug, formatDurationSeconds, selfPacedLearnHref } from "@/lib/self-paced";
import { trackStartTrial } from "@/lib/marketing-pixels";

type Props = {
  initialCourse: SelfPacedCoursePublic;
};

function enrollLoginPath(slug: string) {
  return `/login?next=${encodeURIComponent(`/courses/${slug}?enroll=1`)}`;
}

function ctaLabel(course: SelfPacedCoursePublic) {
  if (course.completed) return "Review Course";
  if (course.enrolled) return "Continue Learning";
  return "Enroll for Free";
}

function LessonRow({
  lesson,
  index,
  enrolled,
  courseSlug,
}: {
  lesson: SelfPacedLessonOutline;
  index: number;
  enrolled: boolean;
  courseSlug: string;
}) {
  const duration = formatDurationSeconds(lesson.duration_seconds);
  const content = (
    <>
      {lesson.completed ? (
        <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-600" />
      ) : enrolled ? (
        <Circle className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
      ) : (
        <Lock className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
      )}
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Lesson {index}
        </p>
        <p className="font-medium text-foreground">{lesson.title}</p>
        {lesson.subtitle && (
          <p className="text-sm text-muted-foreground">{lesson.subtitle}</p>
        )}
      </div>
      {duration && (
        <span className="shrink-0 font-mono text-sm text-muted-foreground">{duration}</span>
      )}
    </>
  );

  if (!enrolled) {
    return (
      <div className="flex items-start gap-3 rounded-xl border bg-background px-4 py-3">
        {content}
      </div>
    );
  }

  return (
    <a
      href={`/courses/${courseSlug}/learn/${lesson.slug}`}
      className="flex items-start gap-3 rounded-xl border bg-background px-4 py-3 transition-colors hover:border-brand-navy/30 hover:bg-brand-navy/5"
    >
      {content}
    </a>
  );
}

export function SelfPacedCourseLanding({ initialCourse }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [course, setCourse] = useState(initialCourse);
  const [enrolling, setEnrolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const enrollLock = useRef(false);

  useEffect(() => {
    let cancelled = false;
    getSelfPacedCourse(initialCourse.slug)
      .then((next) => {
        if (!cancelled) setCourse(next);
      })
      .catch(() => {
        /* keep SSR payload */
      });
    return () => {
      cancelled = true;
    };
  }, [initialCourse.slug]);

  useEffect(() => {
    if (searchParams.get("enroll") !== "1") return;
    if (!getAccessToken()) return;
    if (course.enrolled) {
      router.replace(selfPacedLearnHref(course));
      return;
    }
    if (enrollLock.current) return;
    enrollLock.current = true;

    let cancelled = false;
    async function finishEnroll() {
      setEnrolling(true);
      setError(null);
      try {
        const result = await enrollSelfPacedCourse(course.slug);
        trackStartTrial(course.title);
        const refreshed = await getSelfPacedCourse(course.slug);
        if (cancelled) return;
        setCourse(refreshed);
        router.replace(selfPacedLearnHref({ ...refreshed, resume_lesson_slug: result.resume_lesson_slug }));
      } catch (err) {
        enrollLock.current = false;
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          clearAccessToken();
          router.replace(enrollLoginPath(course.slug));
          return;
        }
        setError(err instanceof ApiError ? err.detail : "Could not enroll in this course");
        setEnrolling(false);
      }
    }
    void finishEnroll();
    return () => {
      cancelled = true;
    };
  }, [course, router, searchParams]);

  async function onEnroll() {
    setError(null);
    if (!getAccessToken()) {
      router.push(enrollLoginPath(course.slug));
      return;
    }
    if (course.enrolled) {
      router.push(selfPacedLearnHref(course));
      return;
    }
    setEnrolling(true);
    try {
      const result = await enrollSelfPacedCourse(course.slug);
      trackStartTrial(course.title);
      const refreshed = await getSelfPacedCourse(course.slug);
      setCourse(refreshed);
      router.push(selfPacedLearnHref({ ...refreshed, resume_lesson_slug: result.resume_lesson_slug }));
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clearAccessToken();
        router.push(enrollLoginPath(course.slug));
        return;
      }
      setError(err instanceof ApiError ? err.detail : "Could not enroll in this course");
      setEnrolling(false);
    }
  }

  const heroThumb =
    course.thumbnail || "/dune-analytics-practical-sql-dashboard-techniques.png";
  const lessonCount =
    course.lessons_count ||
    course.modules.reduce((sum, module) => sum + module.lessons.length, 0);

  return (
    <div className="pb-20">
      <section className="border-b bg-background">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:px-8 lg:py-16">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-orange">
              {catalogIsFree({
                price: course.price,
                currency: course.currency,
                is_free: course.is_free,
              })
                ? "Free self-paced course"
                : "Paid self-paced course"}
            </p>
            <h1 className="mt-4 font-heading text-4xl font-bold tracking-tight text-brand-navy sm:text-5xl dark:text-foreground">
              {course.title}
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted-foreground">
              {course.long_description || course.description}
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              <Badge
                className={
                  catalogIsFree({
                    price: course.price,
                    currency: course.currency,
                    is_free: course.is_free,
                  })
                    ? "bg-brand-orange text-white"
                    : "bg-brand-navy text-white"
                }
              >
                {catalogPriceLabel({
                  price: course.price,
                  currency: course.currency,
                  is_free: course.is_free,
                })}
              </Badge>
              <Badge variant="outline">{lessonCount} lessons</Badge>
              <Badge variant="outline">~{course.estimated_minutes || 70} minutes</Badge>
              <Badge variant="outline">{course.difficulty}</Badge>
            </div>
            {course.enrolled && (
              <div className="mt-6 max-w-md space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Course progress</span>
                  <span className="font-medium">
                    {course.progress_percent}% · {course.lessons_completed} of {lessonCount} lessons
                  </span>
                </div>
                <Progress value={course.progress_percent} className="h-2" />
              </div>
            )}
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button
                size="lg"
                onClick={onEnroll}
                disabled={enrolling}
                className="bg-brand-orange text-white hover:bg-brand-orange/90"
              >
                {enrolling ? "Enrolling…" : ctaLabel(course)}
              </Button>
              {course.enrolled && firstLessonSlug(course) && (
                <ButtonLink href={selfPacedLearnHref(course)} variant="outline" size="lg">
                  <PlayCircle className="size-4" />
                  Open course
                </ButtonLink>
              )}
            </div>
            {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
          </div>
          <div className="relative aspect-video overflow-hidden rounded-2xl border bg-brand-surface shadow-card">
            <Image
              src={heroThumb}
              alt={course.title}
              fill
              className="object-cover"
              priority
              sizes="(max-width: 1024px) 100vw, 40vw"
            />
          </div>
        </div>
      </section>

      <InstructorRoster instructors={course.instructors} />

      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2 className="font-heading text-2xl font-bold tracking-tight">Course outline</h2>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          You can browse every lesson before enrolling. The video player unlocks after you enroll
          for free.
        </p>
        <div className="mt-8 space-y-8">
          {course.modules.map((module, moduleIndex) => {
            let lessonNumber = course.modules
              .slice(0, moduleIndex)
              .reduce((sum, item) => sum + item.lessons.length, 0);
            return (
              <section key={module.id}>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-orange">
                  Module {moduleIndex + 1}
                </p>
                <h3 className="mt-1 font-heading text-xl font-semibold">{module.title}</h3>
                {module.description && (
                  <p className="mt-1 text-sm text-muted-foreground">{module.description}</p>
                )}
                <div className="mt-4 space-y-2">
                  {module.lessons.map((lesson) => {
                    lessonNumber += 1;
                    return (
                      <LessonRow
                        key={lesson.id}
                        lesson={lesson}
                        index={lessonNumber}
                        enrolled={course.enrolled}
                        courseSlug={course.slug}
                      />
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>

        <Card className="mt-16 border-brand-navy/15 bg-brand-navy/[0.03] shadow-none">
          <CardContent className="flex flex-col gap-5 py-8 sm:flex-row sm:items-center sm:justify-between">
            <div className="max-w-xl">
              <h2 className="font-heading text-xl font-semibold">Ready to go further?</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Build beyond individual tutorials with structured, instructor-led training, practical
                projects, assignments and expert guidance.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:items-end">
              <ButtonLink href="/instructor-led" className="bg-brand-navy text-white hover:bg-brand-navy/90">
                Explore Instructor-Led Training
              </ButtonLink>
              <ButtonLink
                href="/programs/blockchain-data-engineering"
                variant="ghost"
                className="text-brand-orange"
              >
                View Blockchain Data Engineering
              </ButtonLink>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
