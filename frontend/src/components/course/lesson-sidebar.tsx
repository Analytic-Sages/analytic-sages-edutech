"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CheckCircle2, Circle, PlayCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Module } from "@/types/course";

type LessonSidebarProps = {
  courseSlug: string;
  modules: Module[];
  currentLessonId: string;
};

export function LessonSidebar({ courseSlug, modules, currentLessonId }: LessonSidebarProps) {
  const pathname = usePathname();

  return (
    <div className="space-y-6">
      {modules.map((module) => (
        <div key={module.id}>
          <h3 className="mb-2 px-3 font-heading text-sm font-semibold">{module.title}</h3>
          <ul className="space-y-0.5">
            {module.lessons.map((lesson) => {
              const href = `/courses/${courseSlug}/learn/${lesson.id}`;
              const isActive = currentLessonId === lesson.id;
              return (
                <li key={lesson.id}>
                  <Link
                    href={href}
                    className={cn(
                      "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
                      isActive
                        ? "bg-brand-navy text-white dark:bg-primary"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    {lesson.completed ? (
                      <CheckCircle2 className="size-4 shrink-0 text-success" />
                    ) : isActive ? (
                      <PlayCircle className="size-4 shrink-0" />
                    ) : (
                      <Circle className="size-4 shrink-0" />
                    )}
                    <span className="line-clamp-2 flex-1">{lesson.title}</span>
                    <span className="shrink-0 text-xs opacity-70">{lesson.duration}</span>
                  </Link>
                </li>
              );
            })}
            {module.quiz && (
              <li>
                <Link
                  href={`/courses/${courseSlug}/quiz/${module.quiz.id}`}
                  className={cn(
                    "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
                    pathname.includes("/quiz/")
                      ? "bg-brand-orange text-white"
                      : "text-muted-foreground hover:bg-muted"
                  )}
                >
                  <span className="flex size-4 items-center justify-center rounded bg-brand-orange/20 text-[10px] font-bold">
                    Q
                  </span>
                  {module.quiz.title}
                </Link>
              </li>
            )}
          </ul>
        </div>
      ))}
    </div>
  );
}
