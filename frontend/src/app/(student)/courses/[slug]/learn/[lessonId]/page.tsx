"use client";

import Link from "next/link";
import { use, useState } from "react";
import { ChevronLeft, ChevronRight, Download, FileText, Menu } from "lucide-react";
import { notFound } from "next/navigation";
import { LessonSidebar } from "@/components/course/lesson-sidebar";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { getCourseBySlug } from "@/lib/mock-data";

type Props = {
  params: Promise<{ slug: string; lessonId: string }>;
};

export default function CoursePlayerPage({ params }: Props) {
  const { slug, lessonId } = use(params);
  const course = getCourseBySlug(slug);
  const [completed, setCompleted] = useState(false);

  if (!course) notFound();

  const allLessons = course.modules.flatMap((m) => m.lessons);
  const currentIndex = allLessons.findIndex((l) => l.id === lessonId);
  const currentLesson = allLessons[currentIndex] ?? allLessons[0];
  const prevLesson = allLessons[currentIndex - 1];
  const nextLesson = allLessons[currentIndex + 1];

  return (
    <div className="-m-4 flex min-h-[calc(100vh-4rem)] flex-col lg:-m-8 lg:flex-row">
      {/* Mobile module drawer */}
      <div className="border-b p-4 lg:hidden">
        <Sheet>
          <SheetTrigger
            className="inline-flex h-7 items-center gap-2 rounded-[min(var(--radius-md),12px)] border border-border bg-background px-2.5 text-[0.8rem] font-medium hover:bg-muted lg:hidden"
          >
            <Menu className="size-4" />
            Course Content
          </SheetTrigger>
          <SheetContent side="left" className="w-80 overflow-y-auto p-4">
            <LessonSidebar
              courseSlug={slug}
              modules={course.modules}
              currentLessonId={currentLesson.id}
            />
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop sidebar */}
      <aside className="hidden w-80 shrink-0 overflow-y-auto border-r bg-brand-surface p-4 lg:block">
        <div className="mb-4">
          <Link
            href={`/courses/${slug}`}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Back to course
          </Link>
          <h2 className="mt-2 font-heading font-semibold line-clamp-2">{course.title}</h2>
          <Progress value={course.progress ?? 0} className="mt-3 h-1.5" />
          <p className="mt-1 text-xs text-muted-foreground">{course.progress}% complete</p>
        </div>
        <LessonSidebar
          courseSlug={slug}
          modules={course.modules}
          currentLessonId={currentLesson.id}
        />
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        <div className="aspect-video w-full bg-brand-navy/5">
          <div className="flex h-full items-center justify-center bg-gradient-to-br from-brand-navy/10 to-brand-orange/10">
            <div className="text-center">
              <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-brand-navy text-white">
                ▶
              </div>
              <p className="text-sm text-muted-foreground">
                Bunny Stream player (connects in Phase 3)
              </p>
            </div>
          </div>
        </div>

        <div className="flex-1 p-4 sm:p-6 lg:p-8">
          <h1 className="font-heading text-xl font-bold sm:text-2xl">{currentLesson.title}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{currentLesson.duration}</p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              variant={completed ? "secondary" : "default"}
              className={completed ? "" : "bg-brand-navy text-white hover:bg-brand-navy/90"}
              onClick={() => setCompleted(true)}
            >
              {completed ? "✓ Completed" : "Mark Complete"}
            </Button>
            {prevLesson && (
              <ButtonLink href={`/courses/${slug}/learn/${prevLesson.id}`} variant="outline">
                <ChevronLeft className="size-4" />
                Previous
              </ButtonLink>
            )}
            {nextLesson && (
              <ButtonLink
                href={`/courses/${slug}/learn/${nextLesson.id}`}
                className="bg-brand-orange text-white hover:bg-brand-orange/90"
              >
                Next
                <ChevronRight className="size-4" />
              </ButtonLink>
            )}
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileText className="size-4" />
                  Lesson Notes
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                <p>
                  In this lesson, you&apos;ll learn how to read and interpret blockchain
                  transactions using Etherscan. We cover gas fees, internal transactions,
                  and token transfers.
                </p>
              </CardContent>
            </Card>
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Download className="size-4" />
                  Resources
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {["Lesson Slides.pdf", "Sample Dataset.csv", "Code Examples.zip"].map(
                  (file) => (
                    <button
                      key={file}
                      className="flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-sm hover:bg-muted transition-colors"
                    >
                      <Download className="size-4 text-brand-navy" />
                      {file}
                    </button>
                  )
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
