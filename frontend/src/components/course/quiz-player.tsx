"use client";

import { useEffect, useState } from "react";
import { CircleAlert, Loader2, RotateCcw, Trophy } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  ApiError,
  getQuiz,
  listMyQuizAttempts,
  submitQuiz,
  type QuizAttemptSummary,
  type QuizPublic,
  type QuizResult,
} from "@/lib/api";
import { cn } from "@/lib/utils";

type Props = {
  slug: string;
  quizId: string;
  courseHref: string;
};

export function QuizPlayer({ slug, quizId, courseHref }: Props) {
  const [quiz, setQuiz] = useState<QuizPublic | null>(null);
  const [history, setHistory] = useState<QuizAttemptSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const [current, setCurrent] = useState(0);
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<QuizResult | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      setForbidden(false);
      setNotFound(false);
      try {
        const [loaded, attempts] = await Promise.all([
          getQuiz(quizId),
          listMyQuizAttempts(quizId).catch(() => [] as QuizAttemptSummary[]),
        ]);
        if (cancelled) return;
        setQuiz(loaded);
        setHistory(attempts);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 403) setForbidden(true);
        else if (err instanceof ApiError && err.status === 404) setNotFound(true);
        else setError(err instanceof ApiError ? err.detail : "Could not load this quiz");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [quizId]);

  function restart() {
    setResult(null);
    setSelections({});
    setCurrent(0);
  }

  async function handleSubmit() {
    if (!quiz) return;
    setSubmitting(true);
    setError(null);
    try {
      const answers = quiz.questions.map((question) => ({
        question_id: question.id,
        option_id: selections[question.id] ?? null,
      }));
      const graded = await submitQuiz(quiz.id, answers);
      setResult(graded);
      const attempts = await listMyQuizAttempts(quiz.id).catch(() => history);
      setHistory(attempts);
      setQuiz(await getQuiz(quiz.id).catch(() => quiz));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not submit your answers");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading quiz…
      </div>
    );
  }

  if (forbidden) {
    return (
      <EmptyState
        icon={<Trophy className="size-5" />}
        title="Enroll to take this quiz"
        description="Quizzes are available after you enroll in the course."
        action={{ label: "View course", href: `/courses/${slug}` }}
      />
    );
  }

  if (notFound || error || !quiz) {
    return (
      <EmptyState
        icon={<CircleAlert className="size-5" />}
        title="Quiz unavailable"
        description={error ?? "We couldn't find this quiz. It may have been removed."}
        action={{ label: "Back to course", href: courseHref }}
      />
    );
  }

  if (quiz.questions.length === 0) {
    return (
      <EmptyState
        icon={<CircleAlert className="size-5" />}
        title="Quiz coming soon"
        description="This quiz doesn't have any questions yet. Check back shortly."
        action={{ label: "Back to course", href: courseHref }}
      />
    );
  }

  if (result) {
    return (
      <div className="space-y-6">
        <Card
          className={cn(
            "shadow-card",
            result.passed ? "border-emerald-500/30" : "border-destructive/30",
          )}
        >
          <CardContent className="py-10 text-center">
            <div
              className={cn(
                "mx-auto mb-4 flex size-16 items-center justify-center rounded-full text-2xl font-bold",
                result.passed
                  ? "bg-emerald-500/10 text-emerald-600"
                  : "bg-destructive/10 text-destructive",
              )}
            >
              {result.score}%
            </div>
            <h2 className="font-heading text-xl font-bold">
              {result.passed ? "Congratulations!" : "Keep practicing"}
            </h2>
            <p className="mt-2 text-muted-foreground">
              {result.passed
                ? "You passed the quiz. Your progress has been saved."
                : `You need ${result.pass_score}% to pass. Review the material and try again.`}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {result.correct_count} of {result.total_questions} correct
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <Button variant="outline" onClick={restart}>
                <RotateCcw className="mr-2 size-4" />
                Retry quiz
              </Button>
              <ButtonLink
                href={courseHref}
                className="bg-brand-navy text-white hover:bg-brand-navy/90"
              >
                Back to course
              </ButtonLink>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          {result.results.map((item, index) => {
            const sourceQuestion = quiz.questions.find((q) => q.id === item.question_id);
            const selectedLabel =
              sourceQuestion?.options.find((o) => o.id === item.selected_option_id)?.label ??
              "No answer";
            const correctLabel =
              sourceQuestion?.options.find((o) => o.id === item.correct_option_id)?.label ?? "—";
            return (
              <Card key={item.question_id} className="shadow-card">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <span
                      className={cn(
                        "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white",
                        item.is_correct ? "bg-emerald-500" : "bg-destructive",
                      )}
                    >
                      {index + 1}
                    </span>
                    <div className="flex-1 space-y-2">
                      <p className="font-medium">{item.prompt}</p>
                      <p className="text-sm">
                        <span className="text-muted-foreground">Your answer: </span>
                        {selectedLabel}
                      </p>
                      {!item.is_correct && (
                        <p className="text-sm">
                          <span className="text-muted-foreground">Correct answer: </span>
                          {correctLabel}
                        </p>
                      )}
                      {item.explanation && (
                        <p className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
                          {item.explanation}
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    );
  }

  const question = quiz.questions[current];
  const answeredCount = quiz.questions.filter((q) => selections[q.id]).length;

  return (
    <div className="space-y-6">
      {quiz.description && (
        <p className="text-sm text-muted-foreground">{quiz.description}</p>
      )}
      <div className="flex flex-wrap gap-2">
        <Badge variant="secondary">Pass score {quiz.pass_score}%</Badge>
        {quiz.best_score !== null && (
          <Badge variant="secondary">Best {quiz.best_score}%</Badge>
        )}
        {quiz.attempts_count > 0 && (
          <Badge variant="secondary">
            {quiz.attempts_count} attempt{quiz.attempts_count === 1 ? "" : "s"}
          </Badge>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">
            Question {current + 1} of {quiz.questions.length}
          </span>
          <span className="font-medium">
            {answeredCount}/{quiz.questions.length} answered
          </span>
        </div>
        <Progress
          value={((current + 1) / quiz.questions.length) * 100}
          className="h-1.5"
        />
      </div>

      <Card className="shadow-card">
        <CardContent className="pt-6">
          <h2 className="font-heading text-lg font-semibold">{question.prompt}</h2>
          <div className="mt-6 space-y-3">
            {question.options.map((option, index) => (
              <button
                key={option.id}
                type="button"
                onClick={() => setSelections({ ...selections, [question.id]: option.id })}
                className={cn(
                  "flex w-full items-center rounded-lg border px-4 py-3 text-left text-sm transition-colors",
                  selections[question.id] === option.id
                    ? "border-brand-navy bg-brand-navy/5 dark:border-primary dark:bg-primary/10"
                    : "hover:bg-muted",
                )}
              >
                <span className="mr-3 flex size-6 shrink-0 items-center justify-center rounded-full border text-xs font-medium">
                  {String.fromCharCode(65 + index)}
                </span>
                {option.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="flex justify-between">
        <Button variant="outline" disabled={current === 0} onClick={() => setCurrent((q) => q - 1)}>
          Previous
        </Button>
        {current < quiz.questions.length - 1 ? (
          <Button
            className="bg-brand-navy text-white hover:bg-brand-navy/90"
            disabled={!selections[question.id]}
            onClick={() => setCurrent((q) => q + 1)}
          >
            Next
          </Button>
        ) : (
          <Button
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
            disabled={submitting || answeredCount < quiz.questions.length}
            onClick={handleSubmit}
          >
            {submitting && <Loader2 className="mr-2 size-4 animate-spin" />}
            Submit Quiz
          </Button>
        )}
      </div>

      {history.length > 0 && (
        <div className="rounded-xl border p-4">
          <h3 className="mb-3 font-heading text-sm font-semibold">Previous attempts</h3>
          <ul className="space-y-1 text-sm">
            {history.map((attempt) => (
              <li key={attempt.id} className="flex items-center justify-between">
                <span className="text-muted-foreground">
                  {attempt.completed_at ? new Date(attempt.completed_at).toLocaleString() : "—"}
                </span>
                <span
                  className={cn(
                    "font-medium",
                    attempt.passed ? "text-emerald-600" : "text-muted-foreground",
                  )}
                >
                  {attempt.score}% {attempt.passed ? "· Passed" : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}