"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Check,
  ChevronDown,
  Loader2,
  Plus,
  Save,
  Trash2,
  Upload,
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiError,
  addAdminLessonResource,
  createAdminCourse,
  createAdminLesson,
  createAdminModule,
  createLessonVideoUpload,
  deleteAdminLesson,
  deleteAdminModule,
  getAdminCourseDetail,
  updateAdminLesson,
  updateAdminCourse,
  updateAdminModule,
  uploadAdminLessonResource,
  type AdminCourseDetail,
  type AdminLessonRow,
  type AdminModuleRow,
} from "@/lib/api";
import { QuizBuilder } from "@/components/admin/quiz-builder";
import { cn } from "@/lib/utils";

const RESOURCE_KINDS = ["pdf", "slides", "dataset", "code", "repo", "reading", "doc", "other"];

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 160);
}

type DetailsState = {
  title: string;
  slug: string;
  description: string;
  long_description: string;
  thumbnail: string;
  category: string;
  difficulty: string;
  duration: string;
  price: number;
  currency: string;
  is_free: boolean;
  certificate_enabled: boolean;
  published: boolean;
};

export function AdminCourseEditor({ slug }: { slug?: string }) {
  const router = useRouter();
  const isNew = !slug;

  const [detail, setDetail] = useState<AdminCourseDetail | null>(null);
  const [loading, setLoading] = useState(!isNew);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  const [details, setDetails] = useState<DetailsState>({
    title: "",
    slug: "",
    description: "",
    long_description: "",
    thumbnail: "",
    category: "General",
    difficulty: "Beginner",
    duration: "",
    price: 0,
    currency: "USD",
    is_free: true,
    certificate_enabled: false,
    published: false,
  });

  const load = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAdminCourseDetail(slug);
      setDetail(data);
      setDetails({
        title: data.title,
        slug: data.slug,
        description: data.description,
        long_description: data.long_description,
        thumbnail: data.thumbnail ?? "",
        category: data.category,
        difficulty: data.difficulty,
        duration: data.duration,
        price: data.price,
        currency: data.currency,
        is_free: data.is_free,
        certificate_enabled: data.certificate_enabled,
        published: data.published,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load course");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    return () => clearTimeout(timer);
  }, [load]);

  async function saveDetails() {
    setSaving(true);
    setError(null);
    try {
      if (isNew) {
        const created = await createAdminCourse({
          ...details,
          slug: details.slug || slugify(details.title),
        });
        router.replace(`/admin/courses/${created.slug}`);
        return;
      }
      const updated = await updateAdminCourse(slug!, details);
      setDetail(updated);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save the course");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading course…
      </div>
    );
  }

  if (!isNew && error && !detail) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn't load course"
        description={error}
        action={{ label: "Back to courses", href: "/admin/courses" }}
      />
    );
  }

  async function addModule() {
    if (!slug) return;
    setBusy(true);
    setError(null);
    try {
      await createAdminModule(slug, { title: `Module ${(detail?.modules.length ?? 0) + 1}` });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not add module");
    } finally {
      setBusy(false);
    }
  }

  async function removeModule(module: AdminModuleRow) {
    if (!window.confirm(`Delete "${module.title}" and its lessons?`)) return;
    setBusy(true);
    setError(null);
    try {
      await deleteAdminModule(module.id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not delete module");
    } finally {
      setBusy(false);
    }
  }

  async function renameModule(module: AdminModuleRow, title: string) {
    try {
      await updateAdminModule(module.id, { title });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not rename module");
    }
  }

  async function addLesson(module: AdminModuleRow) {
    setBusy(true);
    setError(null);
    try {
      await createAdminLesson(module.id, { title: `Lesson ${module.lessons.length + 1}` });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not add lesson");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="mb-4">
        <Link
          href="/admin/courses"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          All courses
        </Link>
      </div>
      <PageHeader
        title={isNew ? "Create course" : detail?.title || "Edit course"}
        description="Publish a course, modules, lessons and downloads — no developer needed."
        action={
          <div className="flex items-center gap-2">
            {savedAt && (
              <span className="inline-flex items-center gap-1 text-xs text-success">
                <Check className="size-3.5" /> Saved
              </span>
            )}
            <Button
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
              onClick={saveDetails}
              disabled={saving}
            >
              {saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
              {isNew ? "Create course" : "Save details"}
            </Button>
          </div>
        }
      />

      {error && (
        <p className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-6">
          <CourseDetailsForm
            details={details}
            isNew={isNew}
            onChange={setDetails}
          />
        </div>

        <div className="space-y-6">
          <section className="rounded-xl border p-4 shadow-card">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-heading text-lg font-semibold">Curriculum</h2>
              <Button variant="outline" size="sm" onClick={addModule} disabled={isNew || busy}>
                <Plus className="size-4" />
                Module
              </Button>
            </div>
            {isNew ? (
              <p className="text-sm text-muted-foreground">
                Create the course first, then add modules and lessons.
              </p>
            ) : (detail?.modules.length ?? 0) === 0 ? (
              <p className="text-sm text-muted-foreground">No modules yet.</p>
            ) : (
              <div className="space-y-3">
                {detail!.modules.map((module) => (
                  <ModuleEditor
                    key={module.id}
                    module={module}
                    busy={busy}
                    onRename={(title) => renameModule(module, title)}
                    onDelete={() => removeModule(module)}
                    onAddLesson={() => addLesson(module)}
                    onChanged={load}
                    onError={setError}
                  />
                ))}
              </div>
            )}
          </section>

          {isNew || !detail ? (
            <QuizBuilder courseSlug="" modules={[]} disabled />
          ) : (
            <QuizBuilder courseSlug={detail.slug} modules={detail.modules} />
          )}
        </div>
      </div>
    </div>
  );
}

function CourseDetailsForm({
  details,
  isNew,
  onChange,
}: {
  details: DetailsState;
  isNew: boolean;
  onChange: (next: DetailsState) => void;
}) {
  const set = <K extends keyof DetailsState>(key: K, value: DetailsState[K]) =>
    onChange({ ...details, [key]: value });

  return (
    <section className="rounded-xl border p-4 shadow-card">
      <h2 className="mb-4 font-heading text-lg font-semibold">Course details</h2>
      <div className="grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor="c-title">Title</Label>
          <Input
            id="c-title"
            value={details.title}
            onChange={(e) => {
              const title = e.target.value;
              onChange({
                ...details,
                title,
                slug: isNew && details.slug ? details.slug : slugify(title),
              });
            }}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="c-slug">Slug</Label>
          <Input
            id="c-slug"
            value={details.slug}
            disabled={!isNew}
            onChange={(e) => set("slug", slugify(e.target.value))}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="c-desc">Short description</Label>
          <Textarea
            id="c-desc"
            rows={2}
            value={details.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="c-long">Long description</Label>
          <Textarea
            id="c-long"
            rows={4}
            value={details.long_description}
            onChange={(e) => set("long_description", e.target.value)}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="c-thumb">Thumbnail URL</Label>
          <Input
            id="c-thumb"
            value={details.thumbnail}
            onChange={(e) => set("thumbnail", e.target.value)}
            placeholder="/blockchain-data-engineering.png"
          />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="grid gap-1.5">
            <Label htmlFor="c-cat">Category</Label>
            <Input id="c-cat" value={details.category} onChange={(e) => set("category", e.target.value)} />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="c-diff">Difficulty</Label>
            <Input
              id="c-diff"
              value={details.difficulty}
              onChange={(e) => set("difficulty", e.target.value)}
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="c-dur">Duration</Label>
            <Input
              id="c-dur"
              value={details.duration}
              onChange={(e) => set("duration", e.target.value)}
              placeholder="10 weeks"
            />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="grid gap-1.5">
            <Label htmlFor="c-price">Price</Label>
            <Input
              id="c-price"
              type="number"
              min={0}
              value={details.price}
              onChange={(e) => set("price", Number(e.target.value) || 0)}
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="c-cur">Currency</Label>
            <Input
              id="c-cur"
              maxLength={3}
              value={details.currency}
              onChange={(e) => set("currency", e.target.value.toUpperCase())}
            />
          </div>
          <div className="grid gap-1.5">
            <Label>Flags</Label>
            <div className="flex flex-wrap items-center gap-3 pt-1 text-sm">
              <label className="flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={details.is_free}
                  onChange={(e) => set("is_free", e.target.checked)}
                />
                Free
              </label>
              <label className="flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={details.published}
                  onChange={(e) => set("published", e.target.checked)}
                />
                Published
              </label>
              <label className="flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={details.certificate_enabled}
                  onChange={(e) => set("certificate_enabled", e.target.checked)}
                />
                Certificate
              </label>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
function ModuleEditor({
  module,
  busy,
  onRename,
  onDelete,
  onAddLesson,
  onChanged,
  onError,
}: {
  module: AdminModuleRow;
  busy: boolean;
  onRename: (title: string) => void;
  onDelete: () => void;
  onAddLesson: () => void;
  onChanged: () => Promise<void>;
  onError: (message: string | null) => void;
}) {
  const [open, setOpen] = useState(true);
  const [title, setTitle] = useState(module.title);
  const [expandedLesson, setExpandedLesson] = useState<string | null>(null);

  return (
    <div className="rounded-lg border">
      <div className="flex items-center gap-2 p-2.5">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="text-muted-foreground"
          aria-label={open ? "Collapse module" : "Expand module"}
        >
          <ChevronDown className={cn("size-4 transition-transform", !open && "-rotate-90")} />
        </button>
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={() => title.trim() && title !== module.title && onRename(title.trim())}
          className="h-8 flex-1"
        />
        <Button variant="ghost" size="sm" onClick={onAddLesson} disabled={busy} title="Add lesson">
          <Plus className="size-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onDelete} disabled={busy} title="Delete module">
          <Trash2 className="size-4 text-destructive" />
        </Button>
      </div>

      {open && (
        <div className="space-y-1.5 border-t p-2.5">
          {module.lessons.length === 0 ? (
            <p className="text-xs text-muted-foreground">No lessons yet.</p>
          ) : (
            module.lessons.map((lesson) => (
              <div key={lesson.id} className="rounded-md border">
                <button
                  type="button"
                  onClick={() =>
                    setExpandedLesson((current) => (current === lesson.id ? null : lesson.id))
                  }
                  className="flex w-full items-center justify-between gap-2 px-2.5 py-2 text-left text-sm"
                >
                  <span className="truncate">
                    {lesson.title}
                    <span className="ml-2 text-xs text-muted-foreground">{lesson.slug}</span>
                  </span>
                  <span className="flex items-center gap-2">
                    {lesson.video_id ? (
                      <Badge variant="outline" className="text-[0.65rem]">
                        {lesson.video_provider === "cloudflare_stream" ? "Stream" : "YouTube"}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-[0.65rem] text-muted-foreground">
                        No video
                      </Badge>
                    )}
                    {!lesson.published && (
                      <Badge variant="outline" className="text-[0.65rem]">
                        Draft
                      </Badge>
                    )}
                  </span>
                </button>
                {expandedLesson === lesson.id && (
                  <LessonEditor
                    lesson={lesson}
                    onChanged={onChanged}
                    onError={onError}
                  />
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function LessonEditor({
  lesson,
  onChanged,
  onError,
}: {
  lesson: AdminLessonRow;
  onChanged: () => Promise<void>;
  onError: (message: string | null) => void;
}) {
  const [draft, setDraft] = useState({
    title: lesson.title,
    subtitle: lesson.subtitle ?? "",
    description: lesson.description,
    video_provider: lesson.video_provider || "youtube",
    video_id: lesson.video_id ?? "",
    duration_seconds: lesson.duration_seconds ?? 0,
    published: lesson.published,
    what_you_learn: lesson.what_you_learn.join("\n"),
    key_concepts: lesson.key_concepts.join("\n"),
  });
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [resLabel, setResLabel] = useState("");
  const [resKind, setResKind] = useState("pdf");
  const [resUrl, setResUrl] = useState("");
  const [uploading, setUploading] = useState(false);

  async function save() {
    setBusy(true);
    onError(null);
    try {
      await updateAdminLesson(lesson.id, {
        title: draft.title,
        subtitle: draft.subtitle || null,
        description: draft.description,
        video_provider: draft.video_provider,
        video_id: draft.video_id || null,
        duration_seconds: draft.duration_seconds || null,
        published: draft.published,
        what_you_learn: draft.what_you_learn.split("\n").map((s) => s.trim()).filter(Boolean),
        key_concepts: draft.key_concepts.split("\n").map((s) => s.trim()).filter(Boolean),
      });
      await onChanged();
      setStatus("Saved");
      setTimeout(() => setStatus(null), 2000);
    } catch (err) {
      onError(err instanceof ApiError ? err.detail : "Could not save lesson");
    } finally {
      setBusy(false);
    }
  }

  async function removeLesson() {
    if (!window.confirm(`Delete lesson "${lesson.title}"?`)) return;
    setBusy(true);
    onError(null);
    try {
      await deleteAdminLesson(lesson.id);
      await onChanged();
    } catch (err) {
      onError(err instanceof ApiError ? err.detail : "Could not delete lesson");
    } finally {
      setBusy(false);
    }
  }

  async function startVideoUpload() {
    setBusy(true);
    onError(null);
    setStatus(null);
    try {
      const upload = await createLessonVideoUpload(lesson.id);
      setDraft((d) => ({ ...d, video_provider: "cloudflare_stream", video_id: upload.uid }));
      setStatus(
        upload.mode === "mock"
          ? `Mock upload — configure CLOUDFLARE_* for real video. UID ${upload.uid}.`
          : "Upload URL ready — POST your video file to it, then save the lesson."
      );
      await onChanged();
    } catch (err) {
      onError(err instanceof ApiError ? err.detail : "Could not create upload URL");
    } finally {
      setBusy(false);
    }
  }

  async function addResourceByUrl() {
    if (!resLabel.trim() || !resUrl.trim()) return;
    setBusy(true);
    onError(null);
    try {
      await addAdminLessonResource(lesson.id, {
        label: resLabel.trim(),
        url: resUrl.trim(),
        kind: resKind,
      });
      setResLabel("");
      setResUrl("");
      await onChanged();
    } catch (err) {
      onError(err instanceof ApiError ? err.detail : "Could not add resource");
    } finally {
      setBusy(false);
    }
  }

  async function uploadResource(file: File) {
    const label = resLabel.trim() || file.name;
    setUploading(true);
    onError(null);
    try {
      await uploadAdminLessonResource(lesson.id, { label, kind: resKind }, file);
      setResLabel("");
      await onChanged();
    } catch (err) {
      onError(err instanceof ApiError ? err.detail : "Could not upload file");
    } finally {
      setUploading(false);
    }
  }

  const field = "h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm";

  return (
    <div className="space-y-3 border-t bg-muted/30 p-3">
      <div className="grid gap-2">
        <Label className="text-xs">Title</Label>
        <Input
          className="h-8"
          value={draft.title}
          onChange={(e) => setDraft({ ...draft, title: e.target.value })}
        />
      </div>
      <div className="grid gap-2">
        <Label className="text-xs">Subtitle</Label>
        <Input
          className="h-8"
          value={draft.subtitle}
          onChange={(e) => setDraft({ ...draft, subtitle: e.target.value })}
        />
      </div>
      <div className="grid gap-2">
        <Label className="text-xs">Description</Label>
        <Textarea
          rows={2}
          value={draft.description}
          onChange={(e) => setDraft({ ...draft, description: e.target.value })}
        />
      </div>

      <div className="grid grid-cols-[1fr_1fr_auto] items-end gap-2">
        <div className="grid gap-2">
          <Label className="text-xs">Video provider</Label>
          <select
            className={field}
            value={draft.video_provider}
            onChange={(e) => setDraft({ ...draft, video_provider: e.target.value })}
          >
            <option value="youtube">YouTube</option>
            <option value="cloudflare_stream">Cloudflare Stream</option>
          </select>
        </div>
        <div className="grid gap-2">
          <Label className="text-xs">
            {draft.video_provider === "cloudflare_stream" ? "Stream video UID" : "YouTube video ID"}
          </Label>
          <Input
            className="h-8"
            value={draft.video_id}
            onChange={(e) => setDraft({ ...draft, video_id: e.target.value })}
          />
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={startVideoUpload}
          disabled={busy}
          title="Create a Cloudflare Stream upload"
        >
          <Upload className="size-4" />
          Upload
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="grid gap-2">
          <Label className="text-xs">Duration (seconds)</Label>
          <Input
            className="h-8"
            type="number"
            min={0}
            value={draft.duration_seconds}
            onChange={(e) => setDraft({ ...draft, duration_seconds: Number(e.target.value) || 0 })}
          />
        </div>
        <label className="flex items-end gap-1.5 pb-1 text-sm">
          <input
            type="checkbox"
            checked={draft.published}
            onChange={(e) => setDraft({ ...draft, published: e.target.checked })}
          />
          Published
        </label>
      </div>

      <div className="grid gap-2">
        <Label className="text-xs">What you&apos;ll learn (one per line)</Label>
        <Textarea
          rows={2}
          value={draft.what_you_learn}
          onChange={(e) => setDraft({ ...draft, what_you_learn: e.target.value })}
        />
      </div>
      <div className="grid gap-2">
        <Label className="text-xs">Key concepts (one per line)</Label>
        <Textarea
          rows={2}
          value={draft.key_concepts}
          onChange={(e) => setDraft({ ...draft, key_concepts: e.target.value })}
        />
      </div>
<div className="rounded-md border bg-background p-2.5">
        <p className="mb-2 text-xs font-semibold">Downloads</p>
        {lesson.resources.length > 0 && (
          <ul className="mb-2 space-y-1 text-xs">
            {lesson.resources.map((resource) => (
              <li key={resource.url} className="flex items-center justify-between gap-2">
                <span className="truncate">
                  {resource.label}
                  <span className="ml-1 text-muted-foreground">({resource.kind})</span>
                </span>
                <a
                  href={resource.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-brand-navy underline dark:text-brand-orange"
                >
                  open
                </a>
              </li>
            ))}
          </ul>
        )}
        <div className="grid grid-cols-[1fr_auto_auto] gap-2">
          <Input
            className="h-8"
            placeholder="Label (e.g. Starter notebook)"
            value={resLabel}
            onChange={(e) => setResLabel(e.target.value)}
          />
          <select className={field} value={resKind} onChange={(e) => setResKind(e.target.value)}>
            {RESOURCE_KINDS.map((kind) => (
              <option key={kind} value={kind}>
                {kind}
              </option>
            ))}
          </select>
          <label className="inline-flex cursor-pointer items-center gap-1 rounded-lg border border-input px-2.5 text-sm">
            {uploading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
            File
            <input
              type="file"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void uploadResource(file);
              }}
            />
          </label>
        </div>
        <div className="mt-2 grid grid-cols-[1fr_auto] gap-2">
          <Input
            className="h-8"
            placeholder="…or paste a URL"
            value={resUrl}
            onChange={(e) => setResUrl(e.target.value)}
          />
          <Button variant="outline" size="sm" onClick={addResourceByUrl} disabled={busy}>
            Add
          </Button>
        </div>
      </div>

      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-2">
          <Button
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
            size="sm"
            onClick={save}
            disabled={busy}
          >
            {busy ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
            Save lesson
          </Button>
          <Button variant="ghost" size="sm" onClick={removeLesson} disabled={busy}>
            <Trash2 className="size-4 text-destructive" />
            Delete
          </Button>
        </div>
        {status && <span className="text-xs text-muted-foreground">{status}</span>}
      </div>
    </div>
  );
}