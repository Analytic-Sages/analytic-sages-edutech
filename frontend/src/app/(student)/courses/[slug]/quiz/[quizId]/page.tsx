"use client";

import { use, useState } from "react";
import { notFound } from "next/navigation";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { getContinueHref } from "@/lib/course-paths";
import { moduleQuiz, getCourseBySlug } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

type Props = { params: Promise<{ slug: string; quizId: string }> };

export default function QuizPage({ params }: Props) {
  const { slug } = use(params);
  const course = getCourseBySlug(slug);
  const quiz = moduleQuiz;
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [submitted, setSubmitted] = useState(false);

  if (!course) notFound();

  const courseHref = getContinueHref(course);
  const question = quiz.questions[currentQ];
  const score = submitted
    ? Math.round(
        (quiz.questions.filter((q) => answers[q.id] === q.correctIndex).length /
          quiz.questions.length) *
          100
      )
    : 0;
  const passed = score >= quiz.passScore;

  const handleSubmit = () => {
    if (Object.keys(answers).length < quiz.questions.length) return;
    setSubmitted(true);
  };

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: course.title, href: courseHref },
          { label: quiz.title },
        ]}
        title={quiz.title}
      />

      {!submitted ? (
        <>
          <div className="mb-6 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">
                Question {currentQ + 1} of {quiz.questions.length}
              </span>
              <span className="font-medium">Pass score: {quiz.passScore}%</span>
            </div>
            <Progress
              value={((currentQ + 1) / quiz.questions.length) * 100}
              className="h-1.5"
            />
          </div>

          <Card className="shadow-card">
            <CardContent className="pt-6">
              <h2 className="font-heading text-lg font-semibold">{question.question}</h2>
              <div className="mt-6 space-y-3">
                {question.options.map((option, index) => (
                  <button
                    key={option}
                    onClick={() => setAnswers({ ...answers, [question.id]: index })}
                    className={cn(
                      "flex w-full items-center rounded-lg border px-4 py-3 text-left text-sm transition-colors",
                      answers[question.id] === index
                        ? "border-brand-navy bg-brand-navy/5 dark:border-primary dark:bg-primary/10"
                        : "hover:bg-muted"
                    )}
                  >
                    <span className="mr-3 flex size-6 shrink-0 items-center justify-center rounded-full border text-xs font-medium">
                      {String.fromCharCode(65 + index)}
                    </span>
                    {option}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="mt-6 flex justify-between">
            <Button
              variant="outline"
              disabled={currentQ === 0}
              onClick={() => setCurrentQ((q) => q - 1)}
            >
              Previous
            </Button>
            {currentQ < quiz.questions.length - 1 ? (
              <Button
                className="bg-brand-navy text-white hover:bg-brand-navy/90"
                disabled={answers[question.id] === undefined}
                onClick={() => setCurrentQ((q) => q + 1)}
              >
                Next
              </Button>
            ) : (
              <Button
                className="bg-brand-orange text-white hover:bg-brand-orange/90"
                disabled={Object.keys(answers).length < quiz.questions.length}
                onClick={handleSubmit}
              >
                Submit Quiz
              </Button>
            )}
          </div>
        </>
      ) : (
        <Card className={cn("shadow-card", passed ? "border-success/30" : "border-destructive/30")}>
          <CardContent className="py-12 text-center">
            <div
              className={cn(
                "mx-auto mb-4 flex size-16 items-center justify-center rounded-full text-2xl font-bold",
                passed ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"
              )}
            >
              {score}%
            </div>
            <h2 className="font-heading text-xl font-bold">
              {passed ? "Congratulations!" : "Keep practicing"}
            </h2>
            <p className="mt-2 text-muted-foreground">
              {passed
                ? "You passed the quiz. Your progress has been saved."
                : `You need ${quiz.passScore}% to pass. Review the lessons and try again.`}
            </p>
            <div className="mt-6 flex justify-center gap-3">
              {!passed && (
                <Button variant="outline" onClick={() => { setSubmitted(false); setCurrentQ(0); setAnswers({}); }}>
                  Retry
                </Button>
              )}
              <ButtonLink
                href={courseHref}
                className="bg-brand-navy text-white hover:bg-brand-navy/90"
              >
                Back to Course
              </ButtonLink>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
