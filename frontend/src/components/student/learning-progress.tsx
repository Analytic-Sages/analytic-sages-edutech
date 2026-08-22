"use client";

import { CheckCircle2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { ButtonLink } from "@/components/ui/button-link";
import { getContinueHref } from "@/lib/course-paths";
import { formatRelativeTime } from "@/lib/utils";
import type { EnrolledCourseBundle } from "@/lib/enrollments";

type LearningProgressProps = {
  items: EnrolledCourseBundle[];
};

export function LearningProgress({ items }: LearningProgressProps) {
  if (items.length === 0) return null;

  const lessonsCompleted = items.reduce(
    (sum, item) => sum + (item.course.lessonsCompleted ?? 0),
    0,
  );
  const lessonsTotal = items.reduce(
    (sum, item) => sum + (item.course.lessonsTotal ?? item.course.lessonsCount ?? 0),
    0,
  );
  const percent = lessonsTotal > 0 ? Math.round((lessonsCompleted / lessonsTotal) * 100) : 0;

  const withActivity = items.filter((item) => item.course.lastActivityAt);
  const recent = (
    withActivity.length
      ? [...withActivity].sort((a, b) => {
          const aTime = new Date(a.course.lastActivityAt as string).getTime();
          const bTime = new Date(b.course.lastActivityAt as string).getTime();
          return bTime - aTime;
        })
      : items
  )[0];

  const lastLesson = [...items]
    .filter((item) => item.course.lastCompletedLessonTitle && item.course.lastCompletedAt)
    .sort((a, b) => {
      const aTime = new Date(a.course.lastCompletedAt as string).getTime();
      const bTime = new Date(b.course.lastCompletedAt as string).getTime();
      return bTime - aTime;
    })[0];

  const when = formatRelativeTime(lastLesson?.course.lastCompletedAt);

  return (
    <div className="rounded-2xl border bg-card p-5 shadow-card">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="font-heading text-base font-bold">Learning progress</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {lessonsCompleted} of {lessonsTotal} lesson{lessonsTotal === 1 ? "" : "s"} completed
            {lessonsTotal > 0 ? ` · ${percent}% complete` : ""}
          </p>
        </div>
        {recent ? (
          <ButtonLink
            href={getContinueHref(recent.course)}
            className="shrink-0 bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            {lessonsCompleted === 0 ? "Start first lesson" : "Continue learning"}
          </ButtonLink>
        ) : null}
      </div>

      <Progress value={percent} className="mt-4 h-2" />

      {lastLesson?.course.lastCompletedLessonTitle ? (
        <p className="mt-4 flex items-start gap-2 text-sm">
          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span>
            Completed &ldquo;{lastLesson.course.lastCompletedLessonTitle}&rdquo;
            {when ? <span className="text-muted-foreground"> · {when}</span> : null}
          </span>
        </p>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">
          {recent
            ? `You're in ${recent.course.title}. Complete a lesson to see it here.`
            : "Complete a lesson to see recent activity."}
        </p>
      )}

      {items.length > 1 ? (
        <ul className="mt-4 space-y-2 border-t pt-4">
          {items.map(({ course }) => {
            const done = course.lessonsCompleted ?? 0;
            const total = course.lessonsTotal ?? course.lessonsCount ?? 0;
            return (
              <li key={course.id} className="flex items-center justify-between gap-3 text-sm">
                <span className="truncate font-medium">{course.title}</span>
                <span className="shrink-0 text-muted-foreground">
                  {done} of {total} · {course.progress ?? 0}%
                </span>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
