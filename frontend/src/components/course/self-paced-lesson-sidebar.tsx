"use client";

import Link from "next/link";
import { CheckCircle2, Circle, PlayCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SelfPacedCoursePublic } from "@/lib/api";

type Props = {
  course: SelfPacedCoursePublic;
  currentLessonSlug: string;
};

export function SelfPacedLessonSidebar({ course, currentLessonSlug }: Props) {
  return (
    <div className="space-y-6">
      {course.modules.map((module, moduleIndex) => (
        <div key={module.id}>
          <p className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-brand-orange">
            Module {moduleIndex + 1}
          </p>
          <h3 className="mb-2 px-3 font-heading text-sm font-semibold">{module.title}</h3>
          <ul className="space-y-0.5">
            {module.lessons.map((lesson) => {
              const href = `/courses/${course.slug}/learn/${lesson.slug}`;
              const isActive = currentLessonSlug === lesson.slug;
              return (
                <li key={lesson.id}>
                  <Link
                    href={href}
                    className={cn(
                      "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
                      isActive
                        ? "bg-brand-navy text-white"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    {lesson.completed ? (
                      <CheckCircle2 className="size-4 shrink-0 text-emerald-500" />
                    ) : isActive ? (
                      <PlayCircle className="size-4 shrink-0" />
                    ) : (
                      <Circle className="size-4 shrink-0" />
                    )}
                    <span className="line-clamp-2 flex-1">{lesson.title}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
