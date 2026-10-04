"use client";

import { use, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { MockQuizPlayer } from "@/components/course/mock-quiz-player";
import { QuizPlayer } from "@/components/course/quiz-player";
import { PageHeader } from "@/components/layout/page-header";
import { ApiError, getQuiz } from "@/lib/api";
import { getContinueHref } from "@/lib/course-paths";
import { getCourseBySlug, moduleQuiz } from "@/lib/mock-data";

type Props = { params: Promise<{ slug: string; quizId: string }> };

export default function QuizPage({ params }: Props) {
  const { slug, quizId } = use(params);
  const course = getCourseBySlug(slug);
  const courseHref = course ? getContinueHref(course) : `/courses/${slug}`;

  const [mode, setMode] = useState<"loading" | "api" | "mock">("loading");
  const [title, setTitle] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getQuiz(quizId)
      .then((quiz) => {
        if (cancelled) return;
        setTitle(quiz.title);
        setMode("api");
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setTitle(moduleQuiz.title);
          setMode("mock");
        } else {
          setMode("api");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [quizId]);

  const header = (
    <PageHeader
      breadcrumbs={[
        { label: "Dashboard", href: "/dashboard" },
        { label: course?.title ?? slug, href: courseHref },
        { label: title ?? "Quiz" },
      ]}
      title={title ?? "Quiz"}
    />
  );

  if (mode === "loading") {
    return (
      <div className="mx-auto max-w-2xl">
        {header}
        <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Loading quiz…
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      {header}
      {mode === "mock" ? (
        <MockQuizPlayer />
      ) : (
        <QuizPlayer slug={slug} quizId={quizId} courseHref={courseHref} />
      )}
    </div>
  );
}