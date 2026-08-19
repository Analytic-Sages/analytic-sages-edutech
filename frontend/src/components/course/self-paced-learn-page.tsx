"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, ChevronLeft, ChevronRight, Loader2, Menu } from "lucide-react";
import { SelfPacedLessonSidebar } from "@/components/course/self-paced-lesson-sidebar";
import { VideoPlayer } from "@/components/course/video-player";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Progress } from "@/components/ui/progress";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
  ApiError,
  completeSelfPacedLesson,
  getSelfPacedLearn,
  getSelfPacedLesson,
  type SelfPacedCoursePublic,
  type SelfPacedLessonDetail,
} from "@/lib/api";
import { formatDurationSeconds } from "@/lib/self-paced";

type Props = {
  slug: string;
  lessonSlug: string;
};

export function SelfPacedLearnPage({ slug, lessonSlug }: Props) {
  const [course, setCourse] = useState<SelfPacedCoursePublic | null>(null);
  const [lesson, setLesson] = useState<SelfPacedLessonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      setForbidden(false);
      try {
        const [learn, detail] = await Promise.all([
          getSelfPacedLearn(slug),
          getSelfPacedLesson(slug, lessonSlug),
        ]);
        if (!cancelled) {
          setCourse(learn);
          setLesson(detail);
        }
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 403) {
          setForbidden(true);
        } else if (err instanceof ApiError && err.status === 404) {
          setError("Lesson not found");
        } else {
          setError(err instanceof ApiError ? err.detail : "Could not load this lesson");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [slug, lessonSlug]);

  async function markComplete() {
    if (!lesson || lesson.completed) return;
    setCompleting(true);
    try {
      const result = await completeSelfPacedLesson(slug, lessonSlug);
      const [learn, detail] = await Promise.all([
        getSelfPacedLearn(slug),
        getSelfPacedLesson(slug, lessonSlug),
      ]);
      setCourse(learn);
      setLesson({ ...detail, course_completed: result.course_completed });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save progress");
    } finally {
      setCompleting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading lesson…
      </div>
    );
  }

  if (forbidden) {
    return (
      <div className="p-6 sm:p-8">
        <EmptyState
          icon={<BookOpen className="size-5" />}
          title="Enroll to start learning"
          description="This lesson is available after you enroll in the free course."
          action={{ label: "View course", href: `/courses/${slug}` }}
        />
      </div>
    );
  }

  if (error || !course || !lesson) {
    return (
      <div className="p-6 sm:p-8">
        <EmptyState
          icon={<BookOpen className="size-5" />}
          title="Couldn't load lesson"
          description={error || "This lesson is unavailable."}
          action={{ label: "Back to course", href: `/courses/${slug}` }}
        />
      </div>
    );
  }

  const duration = formatDurationSeconds(lesson.duration_seconds);

  return (
    <div className="-m-4 flex min-h-[calc(100vh-4rem)] flex-col lg:-m-8 lg:flex-row">
      <div className="border-b p-4 lg:hidden">
        <div className="mb-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">
            {lesson.module_title}
          </p>
          <h2 className="font-heading text-base font-semibold">{course.title}</h2>
          <Progress value={lesson.progress_percent} className="mt-2 h-1.5" />
          <p className="mt-1 text-xs text-muted-foreground">{lesson.progress_percent}% complete</p>
        </div>
        <Sheet>
          <SheetTrigger className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-background px-3 text-sm font-medium hover:bg-muted">
            <Menu className="size-4" />
            Course outline
          </SheetTrigger>
          <SheetContent side="left" className="w-80 overflow-y-auto p-4">
            <SelfPacedLessonSidebar course={course} currentLessonSlug={lesson.slug} />
          </SheetContent>
        </Sheet>
      </div>

      <aside className="hidden w-80 shrink-0 overflow-y-auto border-r bg-brand-surface p-4 lg:block">
        <Link href={`/courses/${slug}`} className="text-sm text-muted-foreground hover:text-foreground">
          Back to course
        </Link>
        <h2 className="mt-2 font-heading font-semibold">{course.title}</h2>
        <Progress value={lesson.progress_percent} className="mt-3 h-1.5" />
        <p className="mt-1 text-xs text-muted-foreground">
          {lesson.progress_percent}% · {lesson.lessons_completed} of {lesson.lessons_total} lessons
        </p>
        <div className="mt-6">
          <SelfPacedLessonSidebar course={course} currentLessonSlug={lesson.slug} />
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        {lesson.course_completed && (
          <div className="border-b bg-emerald-50 px-4 py-4 sm:px-6">
            <h2 className="font-heading text-base font-semibold text-emerald-900">Course completed</h2>
            <p className="mt-1 text-sm text-emerald-800">
              You&apos;ve completed {course.title}.
            </p>
          </div>
        )}

        <div className="border-b px-4 py-4 sm:px-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">
            {course.title}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {lesson.module_title} · Lesson {lesson.lesson_number}
          </p>
        </div>

        <div className="p-4 sm:p-6">
          <VideoPlayer
            videoId={lesson.video_id}
            provider={lesson.video_provider}
            title={lesson.title}
          />
        </div>

        <div className="flex-1 px-4 pb-10 sm:px-6">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">
              Lesson {lesson.lesson_number} of {lesson.lessons_total}
            </Badge>
            {duration && <span className="text-sm text-muted-foreground">{duration}</span>}
          </div>
          <h1 className="mt-2 font-heading text-2xl font-bold">{lesson.title}</h1>
          {lesson.subtitle && <p className="mt-1 text-muted-foreground">{lesson.subtitle}</p>}
          {lesson.description && (
            <p className="mt-4 max-w-3xl text-sm leading-relaxed text-muted-foreground">
              {lesson.description}
            </p>
          )}

          {lesson.what_you_learn.length > 0 && (
            <section className="mt-8">
              <h2 className="font-heading text-lg font-semibold">What you&apos;ll learn</h2>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                {lesson.what_you_learn.map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-brand-orange" />
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {lesson.key_concepts.length > 0 && (
            <section className="mt-8">
              <h2 className="font-heading text-lg font-semibold">Key concepts</h2>
              <ul className="mt-3 flex flex-wrap gap-2">
                {lesson.key_concepts.map((item) => (
                  <Badge key={item} variant="outline">
                    {item}
                  </Badge>
                ))}
              </ul>
            </section>
          )}

          {lesson.resources.length > 0 && (
            <section className="mt-8">
              <h2 className="font-heading text-lg font-semibold">Resources</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {lesson.resources.map((item) => (
                  <li key={item.url}>
                    <a
                      href={item.url}
                      className="text-brand-orange hover:underline"
                      target="_blank"
                      rel="noreferrer"
                    >
                      {item.label}
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            {lesson.prev_slug ? (
              <ButtonLink href={`/courses/${slug}/learn/${lesson.prev_slug}`} variant="outline">
                <ChevronLeft className="size-4" />
                Previous lesson
              </ButtonLink>
            ) : (
              <span />
            )}
            <Button
              onClick={markComplete}
              disabled={completing || lesson.completed}
              className={
                lesson.completed
                  ? "bg-emerald-600 text-white hover:bg-emerald-600"
                  : "bg-brand-navy text-white hover:bg-brand-navy/90"
              }
            >
              {lesson.completed ? "Lesson complete" : completing ? "Saving…" : "Mark lesson complete"}
            </Button>
            {lesson.next_slug ? (
              <ButtonLink
                href={`/courses/${slug}/learn/${lesson.next_slug}`}
                className="bg-brand-orange text-white hover:bg-brand-orange/90"
              >
                Next lesson
                <ChevronRight className="size-4" />
              </ButtonLink>
            ) : (
              <ButtonLink href="/instructor-led" variant="outline">
                Explore more learning
              </ButtonLink>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
