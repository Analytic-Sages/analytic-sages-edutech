"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, ChevronDown, Loader2, Plus, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  addAdminQuizQuestion,
  createAdminQuiz,
  deleteAdminQuiz,
  deleteAdminQuizQuestion,
  formatApiDetail,
  getAdminQuiz,
  getAdminQuizzes,
  updateAdminQuiz,
  updateAdminQuizQuestion,
  type AdminModuleRow,
  type AdminQuizDetail,
  type AdminQuizQuestion,
  type AdminQuizRow,
  type QuizOptionInput,
} from "@/lib/api";
import { cn } from "@/lib/utils";

type Props = {
  courseSlug: string;
  modules: AdminModuleRow[];
  disabled?: boolean;
};

type DraftOption = { label: string; is_correct: boolean };

function emptyDraftOptions(): DraftOption[] {
  return [
    { label: "", is_correct: true },
    { label: "", is_correct: false },
  ];
}

export function QuizBuilder({ courseSlug, modules, disabled }: Props) {
  const [quizzes, setQuizzes] = useState<AdminQuizRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newModuleId, setNewModuleId] = useState<string>("");
  const [newPassScore, setNewPassScore] = useState(70);

  useEffect(() => {
    if (disabled) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const rows = await getAdminQuizzes(courseSlug);
        if (!cancelled) setQuizzes(rows);
      } catch (err) {
        if (!cancelled) setError(formatApiDetail(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [courseSlug, disabled]);

  async function refresh() {
    try {
      setQuizzes(await getAdminQuizzes(courseSlug));
    } catch (err) {
      setError(formatApiDetail(err));
    }
  }

  async function handleCreate() {
    if (!newTitle.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const quiz = await createAdminQuiz(courseSlug, {
        title: newTitle.trim(),
        pass_score: newPassScore,
        module_id: newModuleId || null,
      });
      setNewTitle("");
      setNewModuleId("");
      setCreating(false);
      await refresh();
      setExpanded(quiz.id);
    } catch (err) {
      setError(formatApiDetail(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(quizId: string) {
    setBusy(true);
    setError(null);
    try {
      await deleteAdminQuiz(quizId);
      if (expanded === quizId) setExpanded(null);
      await refresh();
    } catch (err) {
      setError(formatApiDetail(err));
    } finally {
      setBusy(false);
    }
  }

  async function togglePublished(quiz: AdminQuizRow) {
    setBusy(true);
    try {
      await updateAdminQuiz(quiz.id, { published: !quiz.published });
      await refresh();
    } catch (err) {
      setError(formatApiDetail(err));
    } finally {
      setBusy(false);
    }
  }

  if (disabled) {
    return (
      <section className="rounded-xl border p-4 shadow-card">
        <h2 className="mb-2 font-heading text-lg font-semibold">Quizzes</h2>
        <p className="text-sm text-muted-foreground">
          Create the course first, then add module quizzes.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border p-4 shadow-card">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-heading text-lg font-semibold">Quizzes</h2>
        <Button variant="outline" size="sm" onClick={() => setCreating((v) => !v)} disabled={busy}>
          <Plus className="size-4" />
          Quiz
        </Button>
      </div>

      {error && (
        <p className="mb-3 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      {creating && (
        <div className="mb-4 space-y-3 rounded-lg border bg-muted/40 p-3">
          <Input
            placeholder="Quiz title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
          />
          <div className="flex flex-wrap items-center gap-3">
            <select
              className="h-9 rounded-md border bg-background px-2 text-sm"
              value={newModuleId}
              onChange={(e) => setNewModuleId(e.target.value)}
            >
              <option value="">Course-level quiz</option>
              {modules.map((module, index) => (
                <option key={module.id} value={module.id}>
                  Module {index + 1}: {module.title}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-2 text-sm">
              Pass score
              <Input
                type="number"
                min={0}
                max={100}
                value={newPassScore}
                onChange={(e) => setNewPassScore(Number(e.target.value))}
                className="h-9 w-20"
              />
            </label>
          </div>
          <div className="flex gap-2">
            <Button
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
              size="sm"
              onClick={handleCreate}
              disabled={busy || !newTitle.trim()}
            >
              {busy ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
              Create quiz
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setCreating(false)}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Loading quizzes…
        </div>
      ) : quizzes.length === 0 ? (
        <p className="text-sm text-muted-foreground">No quizzes yet.</p>
      ) : (
        <div className="space-y-3">
          {quizzes.map((quiz) => (
            <QuizCard
              key={quiz.id}
              quiz={quiz}
              busy={busy}
              expanded={expanded === quiz.id}
              onToggle={() => setExpanded((id) => (id === quiz.id ? null : quiz.id))}
              onDelete={() => handleDelete(quiz.id)}
              onTogglePublished={() => togglePublished(quiz)}
              onChanged={refresh}
              onError={setError}
              onBusy={setBusy}
            />
          ))}
        </div>
      )}
    </section>
  );
}

type QuizCardProps = {
  quiz: AdminQuizRow;
  busy: boolean;
  expanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
  onTogglePublished: () => void;
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
  onBusy: (value: boolean) => void;
};

function QuizCard({
  quiz,
  busy,
  expanded,
  onToggle,
  onDelete,
  onTogglePublished,
  onChanged,
  onError,
  onBusy,
}: QuizCardProps) {
  const [detail, setDetail] = useState<AdminQuizDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!expanded) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const loaded = await getAdminQuiz(quiz.id);
        if (!cancelled) setDetail(loaded);
      } catch (err) {
        if (!cancelled) onError(formatApiDetail(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [expanded, quiz.id, onError]);

  async function refresh() {
    const loaded = await getAdminQuiz(quiz.id).catch(() => null);
    if (loaded) setDetail(loaded);
    await onChanged();
  }

  return (
    <Card className="shadow-card">
      <CardContent className="pt-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <button
            type="button"
            onClick={onToggle}
            className="flex flex-1 items-start gap-2 text-left"
          >
            <ChevronDown
              className={cn("mt-1 size-4 shrink-0 transition-transform", expanded && "rotate-180")}
            />
            <div>
              <p className="font-medium">{quiz.title}</p>
              <div className="mt-1 flex flex-wrap gap-1.5">
                <Badge variant={quiz.published ? "default" : "secondary"}>
                  {quiz.published ? "Published" : "Draft"}
                </Badge>
                <Badge variant="secondary">Pass {quiz.pass_score}%</Badge>
                <Badge variant="secondary">{quiz.questions_total} questions</Badge>
                <Badge variant="secondary">{quiz.attempts_count} attempts</Badge>
                {quiz.attempts_count > 0 && (
                  <Badge variant="secondary">{quiz.pass_rate}% pass rate</Badge>
                )}
              </div>
            </div>
          </button>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onTogglePublished} disabled={busy}>
              {quiz.published ? "Unpublish" : "Publish"}
            </Button>
            <Button variant="ghost" size="sm" onClick={onDelete} disabled={busy}>
              <Trash2 className="size-4 text-destructive" />
            </Button>
          </div>
        </div>

        {expanded && (
          <div className="mt-4 space-y-3 border-t pt-4">
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" /> Loading questions…
              </div>
            ) : (
              <>
                {(detail?.questions.length ?? 0) === 0 ? (
                  <p className="text-sm text-muted-foreground">No questions yet.</p>
                ) : (
                  detail!.questions.map((question, index) => (
                    <QuestionEditor
                      key={question.id}
                      index={index + 1}
                      question={question}
                      onChanged={refresh}
                      onError={onError}
                      onBusy={onBusy}
                    />
                  ))
                )}
                <NewQuestionForm quizId={quiz.id} onChanged={refresh} onError={onError} onBusy={onBusy} />
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function OptionsEditor({
  options,
  onChange,
}: {
  options: DraftOption[];
  onChange: (options: DraftOption[]) => void;
}) {
  function update(index: number, patch: Partial<DraftOption>) {
    onChange(options.map((option, i) => (i === index ? { ...option, ...patch } : option)));
  }

  function markCorrect(index: number) {
    onChange(options.map((option, i) => ({ ...option, is_correct: i === index })));
  }

  return (
    <div className="space-y-2">
      {options.map((option, index) => (
        <div key={index} className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => markCorrect(index)}
            title="Mark as correct answer"
            className={cn(
              "flex size-6 shrink-0 items-center justify-center rounded-full border",
              option.is_correct
                ? "border-emerald-500 bg-emerald-500 text-white"
                : "text-transparent hover:border-emerald-500",
            )}
          >
            <CheckCircle2 className="size-4" />
          </button>
          <Input
            value={option.label}
            placeholder={`Option ${String.fromCharCode(65 + index)}`}
            onChange={(e) => update(index, { label: e.target.value })}
          />
          {options.length > 2 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onChange(options.filter((_, i) => i !== index))}
            >
              <Trash2 className="size-4 text-destructive" />
            </Button>
          )}
        </div>
      ))}
      {options.length < 8 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() =>
            onChange([
              ...options,
              { label: "", is_correct: options.every((option) => !option.is_correct) },
            ])
          }
        >
          <Plus className="size-4" />
          Add option
        </Button>
      )}
      <p className="text-xs text-muted-foreground">
        Tap the circle to mark the correct answer.
      </p>
    </div>
  );
}

function toOptionInputs(options: DraftOption[]): QuizOptionInput[] {
  return options
    .filter((option) => option.label.trim())
    .map((option) => ({ label: option.label.trim(), is_correct: option.is_correct }));
}

type QuestionEditorProps = {
  index: number;
  question: AdminQuizQuestion;
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
  onBusy: (value: boolean) => void;
};

function QuestionEditor({ index, question, onChanged, onError, onBusy }: QuestionEditorProps) {
  const [prompt, setPrompt] = useState(question.prompt);
  const [explanation, setExplanation] = useState(question.explanation ?? "");
  const [options, setOptions] = useState<DraftOption[]>(
    question.options.map((option) => ({ label: option.label, is_correct: option.is_correct })),
  );
  const [saving, setSaving] = useState(false);

  async function save() {
    const inputs = toOptionInputs(options);
    if (!prompt.trim() || inputs.length < 2 || !inputs.some((option) => option.is_correct)) {
      onError("Each question needs a prompt, 2+ options, and one correct answer.");
      return;
    }
    setSaving(true);
    onBusy(true);
    try {
      await updateAdminQuizQuestion(question.id, {
        prompt: prompt.trim(),
        explanation: explanation.trim() || null,
        options: inputs,
      });
      await onChanged();
    } catch (err) {
      onError(formatApiDetail(err));
    } finally {
      setSaving(false);
      onBusy(false);
    }
  }

  async function remove() {
    onBusy(true);
    try {
      await deleteAdminQuizQuestion(question.id);
      await onChanged();
    } catch (err) {
      onError(formatApiDetail(err));
    } finally {
      onBusy(false);
    }
  }

  return (
    <div className="space-y-2 rounded-lg border bg-background p-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Question {index}
        </span>
        <Button variant="ghost" size="sm" onClick={remove}>
          <Trash2 className="size-4 text-destructive" />
        </Button>
      </div>
      <Textarea
        rows={2}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Question prompt"
      />
      <OptionsEditor options={options} onChange={setOptions} />
      <Textarea
        rows={2}
        value={explanation}
        onChange={(e) => setExplanation(e.target.value)}
        placeholder="Explanation shown after answering (optional)"
      />
      <Button
        size="sm"
        className="bg-brand-navy text-white hover:bg-brand-navy/90"
        onClick={save}
        disabled={saving}
      >
        {saving && <Loader2 className="mr-2 size-4 animate-spin" />}
        Save question
      </Button>
    </div>
  );
}

type NewQuestionFormProps = {
  quizId: string;
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
  onBusy: (value: boolean) => void;
};

function NewQuestionForm({ quizId, onChanged, onError, onBusy }: NewQuestionFormProps) {
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [explanation, setExplanation] = useState("");
  const [options, setOptions] = useState<DraftOption[]>(emptyDraftOptions());
  const [saving, setSaving] = useState(false);

  async function submit() {
    const inputs = toOptionInputs(options);
    if (!prompt.trim() || inputs.length < 2 || !inputs.some((option) => option.is_correct)) {
      onError("Each question needs a prompt, 2+ options, and one correct answer.");
      return;
    }
    setSaving(true);
    onBusy(true);
    try {
      await addAdminQuizQuestion(quizId, {
        prompt: prompt.trim(),
        explanation: explanation.trim() || null,
        options: inputs,
      });
      setPrompt("");
      setExplanation("");
      setOptions(emptyDraftOptions());
      setOpen(false);
      await onChanged();
    } catch (err) {
      onError(formatApiDetail(err));
    } finally {
      setSaving(false);
      onBusy(false);
    }
  }

  if (!open) {
    return (
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        <Plus className="size-4" />
        Add question
      </Button>
    );
  }

  return (
    <div className="space-y-2 rounded-lg border border-dashed bg-muted/30 p-3">
      <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        New question
      </span>
      <Textarea
        rows={2}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Question prompt"
      />
      <OptionsEditor options={options} onChange={setOptions} />
      <Textarea
        rows={2}
        value={explanation}
        onChange={(e) => setExplanation(e.target.value)}
        placeholder="Explanation shown after answering (optional)"
      />
      <div className="flex gap-2">
        <Button
          size="sm"
          className="bg-brand-orange text-white hover:bg-brand-orange/90"
          onClick={submit}
          disabled={saving}
        >
          {saving && <Loader2 className="mr-2 size-4 animate-spin" />}
          Add question
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
          Cancel
        </Button>
      </div>
    </div>
  );
}