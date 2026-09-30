"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Upload } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiError,
  cancelAdminEvent,
  createAdminEvent,
  getAdminEvent,
  listPublicCohorts,
  listSelfPacedCourses,
  updateAdminEvent,
  uploadAdminEventImage,
  type EventAdmin,
  type EventPlatform,
  type EventType,
  type KeepLearningOffer,
} from "@/lib/api";
import {
  EVENT_PLATFORM_LABELS,
  EVENT_TYPE_LABELS,
  isBundledEventCover,
  isValidEventSlug,
  resolveEventCoverSrc,
  slugifyEventValue,
} from "@/lib/events";
import {
  BDE_COHORT_SLUG,
  blockchainDataEngineeringProgram,
} from "@/lib/blockchain-data-engineering-program";
import { comingSoonCohortSlugs, getProgramPageHref } from "@/lib/program-pages";
import { FEATURED_FREE_COURSE, mergeFreeCatalog } from "@/lib/self-paced";

type KeepLearningOption = {
  key: string;
  kind: "course" | "program";
  slug: string;
  label: string;
};

type FormState = {
  slug: string;
  title: string;
  event_type: EventType;
  short_description: string;
  description: string;
  cover_image: string;
  starts_at: string;
  ends_at: string;
  timezone: string;
  host_name: string;
  platform: EventPlatform;
  platform_label: string;
  youtube_live_url: string;
  recording_url: string;
  learn_topics: string;
  audience: string;
  prerequisites: string;
  keep_learning: KeepLearningOffer[];
  seo_title: string;
  seo_description: string;
  published: boolean;
};

const EMPTY: FormState = {
  slug: "",
  title: "",
  event_type: "workshop",
  short_description: "",
  description: "",
  cover_image: "",
  starts_at: "",
  ends_at: "",
  timezone: "Africa/Lagos",
  host_name: "Analytic Sages",
  platform: "youtube",
  platform_label: "",
  youtube_live_url: "",
  recording_url: "",
  learn_topics: "",
  audience: "",
  prerequisites: "",
  keep_learning: [],
  seo_title: "",
  seo_description: "",
  published: false,
};

function toLocalInput(iso: string | null, timeZone: string) {
  if (!iso) return "";
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(new Date(iso));
  const get = (type: string) => parts.find((part) => part.type === type)?.value ?? "";
  return `${get("year")}-${get("month")}-${get("day")}T${get("hour")}:${get("minute")}`;
}

function fromEvent(event: EventAdmin): FormState {
  const keep =
    event.keep_learning?.length > 0
      ? event.keep_learning
      : event.related_course_slug
        ? [{ kind: "course" as const, slug: event.related_course_slug }]
        : [];
  return {
    slug: event.slug,
    title: event.title,
    event_type: event.event_type as EventType,
    short_description: event.short_description,
    description: event.description,
    cover_image: event.cover_image ?? "",
    starts_at: toLocalInput(event.starts_at, event.timezone),
    ends_at: toLocalInput(event.ends_at, event.timezone),
    timezone: event.timezone,
    host_name: event.host_name ?? "",
    platform: (event.platform as EventPlatform) || "youtube",
    platform_label: event.platform_label ?? "",
    youtube_live_url: event.youtube_live_url ?? "",
    recording_url: event.recording_url ?? "",
    learn_topics: event.learn_topics.join("\n"),
    audience: event.audience.join("\n"),
    prerequisites: event.prerequisites,
    keep_learning: keep,
    seo_title: event.seo_title ?? "",
    seo_description: event.seo_description ?? "",
    published: event.published,
  };
}

function lines(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function withSeconds(value: string) {
  if (!value) return "";
  return value.length === 16 ? `${value}:00` : value;
}

function toPayload(form: FormState) {
  const keep_learning = form.keep_learning.slice(0, 3);
  const related =
    keep_learning.find((offer) => offer.kind === "course")?.slug || null;
  return {
    slug: slugifyEventValue(form.slug),
    title: form.title.trim(),
    event_type: form.event_type,
    short_description: form.short_description.trim(),
    description: form.description.trim(),
    cover_image: form.cover_image.trim() || null,
    starts_at: form.starts_at ? withSeconds(form.starts_at) : null,
    ends_at: form.ends_at ? withSeconds(form.ends_at) : null,
    timezone: form.timezone.trim() || "Africa/Lagos",
    host_name: form.host_name.trim() || null,
    platform: form.platform,
    platform_label: form.platform === "other" ? form.platform_label.trim() || null : null,
    youtube_live_url: form.youtube_live_url.trim() || null,
    recording_url: form.recording_url.trim() || null,
    learn_topics: lines(form.learn_topics),
    audience: lines(form.audience),
    prerequisites: form.prerequisites.trim(),
    related_course_slug: related,
    keep_learning,
    seo_title: form.seo_title.trim() || null,
    seo_description: form.seo_description.trim() || null,
    published: form.published,
    price: 0,
    currency: "USD",
  };
}

export function AdminEventForm({ eventId }: { eventId?: string }) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [loading, setLoading] = useState(Boolean(eventId));
  const [saving, setSaving] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cancelled, setCancelled] = useState(false);
  const [slugTouched, setSlugTouched] = useState(Boolean(eventId));
  const [keepOptions, setKeepOptions] = useState<KeepLearningOption[]>([]);

  useEffect(() => {
    let ignore = false;
    Promise.all([
      listSelfPacedCourses().catch(() => []),
      listPublicCohorts().catch(() => []),
    ]).then(([courses, cohorts]) => {
      if (ignore) return;
      const options: KeepLearningOption[] = [];
      for (const course of mergeFreeCatalog(courses)) {
        options.push({
          key: `course:${course.slug}`,
          kind: "course",
          slug: course.slug,
          label: `Free · ${course.title}`,
        });
      }
      if (!options.some((option) => option.slug === FEATURED_FREE_COURSE.slug)) {
        options.unshift({
          key: `course:${FEATURED_FREE_COURSE.slug}`,
          kind: "course",
          slug: FEATURED_FREE_COURSE.slug,
          label: `Free · ${FEATURED_FREE_COURSE.title}`,
        });
      }
      const blocked = comingSoonCohortSlugs();
      for (const cohort of cohorts) {
        if (blocked.has(cohort.slug)) continue;
        if (cohort.status !== "open" && cohort.status !== "active") continue;
        if (!getProgramPageHref(cohort.slug)) continue;
        options.push({
          key: `program:${cohort.slug}`,
          kind: "program",
          slug: cohort.slug,
          label: `Paid · ${cohort.course_title || cohort.name}`,
        });
      }
      if (
        blockchainDataEngineeringProgram.registrationLive &&
        !options.some((option) => option.slug === BDE_COHORT_SLUG || option.slug === blockchainDataEngineeringProgram.pageSlug)
      ) {
        options.push({
          key: `program:${blockchainDataEngineeringProgram.pageSlug}`,
          kind: "program",
          slug: blockchainDataEngineeringProgram.pageSlug,
          label: `Paid · ${blockchainDataEngineeringProgram.h1}`,
        });
      }
      setKeepOptions(options);
    });
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (!eventId) return;
    let ignore = false;
    getAdminEvent(eventId)
      .then((event) => {
        if (ignore) return;
        setForm(fromEvent(event));
        setCancelled(event.cancelled);
        setSlugTouched(true);
      })
      .catch((err) => {
        if (!ignore) setError(err instanceof ApiError ? err.detail : "Could not load event.");
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [eventId]);

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function onTitleChange(value: string) {
    setForm((current) => ({
      ...current,
      title: value,
      slug: !eventId && !slugTouched ? slugifyEventValue(value) : current.slug,
    }));
  }

  function onSlugChange(value: string) {
    setSlugTouched(true);
    set("slug", slugifyEventValue(value));
  }

  function toggleKeepLearning(option: KeepLearningOption) {
    setForm((current) => {
      const exists = current.keep_learning.some(
        (offer) => offer.kind === option.kind && offer.slug === option.slug,
      );
      if (exists) {
        return {
          ...current,
          keep_learning: current.keep_learning.filter(
            (offer) => !(offer.kind === option.kind && offer.slug === option.slug),
          ),
        };
      }
      if (current.keep_learning.length >= 3) return current;
      return {
        ...current,
        keep_learning: [...current.keep_learning, { kind: option.kind, slug: option.slug }],
      };
    });
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    const slug = slugifyEventValue(form.slug);
    if (!isValidEventSlug(slug)) {
      setError(
        "URL slug must be at least 3 characters using lowercase letters, numbers, and hyphens (e.g. data-infrastructure).",
      );
      setSaving(false);
      return;
    }
    try {
      const payload = toPayload({ ...form, slug });
      if (eventId) {
        await updateAdminEvent(eventId, payload);
      } else {
        const created = await createAdminEvent(payload);
        router.replace(`/admin/events/${created.id}`);
        return;
      }
      router.push("/admin/events");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save event.");
    } finally {
      setSaving(false);
    }
  }

  async function onCancelEvent() {
    if (!eventId) return;
    setCancelling(true);
    setError(null);
    try {
      const updated = await cancelAdminEvent(eventId);
      setCancelled(updated.cancelled);
      setForm(fromEvent(updated));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not cancel event.");
    } finally {
      setCancelling(false);
    }
  }

  async function onUploadCover(fileList: FileList | null) {
    const file = fileList?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const uploaded = await uploadAdminEventImage(file);
      set("cover_image", uploaded.url);
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.detail : "Could not upload image.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const coverPreview = resolveEventCoverSrc(form.cover_image);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading event…
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        breadcrumbs={[
          { label: "Admin", href: "/admin" },
          { label: "Events", href: "/admin/events" },
          { label: eventId ? "Edit event" : "New event" },
        ]}
        title={eventId ? "Edit event" : "New event"}
        description="Leave start and end empty to publish as Coming soon. Add dates later when the session is scheduled. Times use the timezone you set."
      />
      <form onSubmit={onSubmit} className="max-w-3xl space-y-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="title">Title</Label>
            <Input id="title" value={form.title} onChange={(e) => onTitleChange(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="slug">URL slug</Label>
            <Input
              id="slug"
              value={form.slug}
              onChange={(e) => onSlugChange(e.target.value)}
              placeholder="data-infrastructure"
              required
            />
            <p className="text-xs text-muted-foreground">
              Used in the event link. Lowercase letters, numbers, and hyphens only — filled from the title
              automatically.
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="event_type">Type</Label>
            <select
              id="event_type"
              className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
              value={form.event_type}
              onChange={(e) => {
                const nextType = e.target.value as EventType;
                setForm((current) => ({
                  ...current,
                  event_type: nextType,
                  platform:
                    nextType === "x_space" && current.platform === "youtube"
                      ? "x_space"
                      : current.platform,
                }));
              }}
            >
              {Object.entries(EVENT_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="platform">Live platform</Label>
            <select
              id="platform"
              className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
              value={form.platform}
              onChange={(e) => set("platform", e.target.value as EventPlatform)}
            >
              {Object.entries(EVENT_PLATFORM_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          {form.platform === "other" ? (
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="platform_label">Platform name</Label>
              <Input
                id="platform_label"
                value={form.platform_label}
                onChange={(e) => set("platform_label", e.target.value)}
                placeholder="e.g. Google Meet, Discord"
              />
            </div>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="starts_at">Starts</Label>
            <Input
              id="starts_at"
              type="datetime-local"
              value={form.starts_at}
              onChange={(e) => set("starts_at", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="ends_at">Ends</Label>
            <Input
              id="ends_at"
              type="datetime-local"
              value={form.ends_at}
              onChange={(e) => set("ends_at", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone</Label>
            <Input id="timezone" value={form.timezone} onChange={(e) => set("timezone", e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="host_name">Host name</Label>
            <Input id="host_name" value={form.host_name} onChange={(e) => set("host_name", e.target.value)} />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="short_description">Short description</Label>
          <Textarea
            id="short_description"
            value={form.short_description}
            onChange={(e) => set("short_description", e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="description">Full description</Label>
          <Textarea
            id="description"
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
            rows={8}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="cover_image">Cover image</Label>
            <div className="grid gap-4 sm:grid-cols-[minmax(0,16rem)_1fr] sm:items-start">
              <div className="relative aspect-video overflow-hidden rounded-xl border bg-brand-surface">
                {coverPreview ? (
                  // eslint-disable-next-line @next/next/no-img-element -- admin preview for bundled, media, and remote URLs
                  <img
                    src={coverPreview}
                    alt="Event cover preview"
                    className="size-full object-cover"
                  />
                ) : (
                  <div className="flex size-full items-center justify-center px-4 text-center text-xs text-muted-foreground">
                    No cover yet
                  </div>
                )}
              </div>
              <div className="space-y-3">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  className="sr-only"
                  onChange={(e) => void onUploadCover(e.target.files)}
                />
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={uploading}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    {uploading ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Upload className="size-4" />
                    )}
                    {uploading ? "Uploading…" : "Upload image"}
                  </Button>
                  {form.cover_image ? (
                    <Button
                      type="button"
                      variant="ghost"
                      disabled={uploading}
                      onClick={() => {
                        set("cover_image", "");
                        setUploadError(null);
                      }}
                    >
                      Remove
                    </Button>
                  ) : null}
                </div>
                <p className="text-xs text-muted-foreground">
                  JPG, PNG, WebP, or GIF up to 5MB. Or paste a site path like{" "}
                  <span className="font-mono">/4.png</span> / a full https URL below.
                </p>
                <Input
                  id="cover_image"
                  value={form.cover_image}
                  onChange={(e) => set("cover_image", e.target.value)}
                  placeholder="/4.png or https://…"
                />
                {uploadError ? <p className="text-sm text-destructive">{uploadError}</p> : null}
                {coverPreview && isBundledEventCover(coverPreview) ? (
                  <p className="text-xs text-muted-foreground">Using a built-in site image.</p>
                ) : null}
              </div>
            </div>
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Keep learning (up to 3)</Label>
            <p className="text-xs text-muted-foreground">
              Pick the courses or programmes shown in the event sidebar so they match this session.
              Leave empty to use the default free course and open programmes.
            </p>
            <div className="max-h-48 space-y-2 overflow-y-auto rounded-lg border p-3">
              {keepOptions.length === 0 ? (
                <p className="text-xs text-muted-foreground">Loading options…</p>
              ) : (
                keepOptions.map((option) => {
                  const checked = form.keep_learning.some(
                    (offer) => offer.kind === option.kind && offer.slug === option.slug,
                  );
                  return (
                    <label key={option.key} className="flex cursor-pointer items-start gap-2 text-sm">
                      <input
                        type="checkbox"
                        className="mt-0.5"
                        checked={checked}
                        disabled={!checked && form.keep_learning.length >= 3}
                        onChange={() => toggleKeepLearning(option)}
                      />
                      <span>{option.label}</span>
                    </label>
                  );
                })
              )}
            </div>
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="youtube_live_url">Live URL</Label>
            <Input
              id="youtube_live_url"
              value={form.youtube_live_url}
              onChange={(e) => set("youtube_live_url", e.target.value)}
              placeholder="https://… (YouTube, X Space, Zoom, etc.)"
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="recording_url">Recording URL</Label>
            <Input
              id="recording_url"
              value={form.recording_url}
              onChange={(e) => set("recording_url", e.target.value)}
              placeholder="https://…"
            />
            <p className="text-xs text-muted-foreground">
              When set on a free event, visitors can open the recording from the event page.
            </p>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="learn_topics">What you will cover (one per line)</Label>
            <Textarea
              id="learn_topics"
              value={form.learn_topics}
              onChange={(e) => set("learn_topics", e.target.value)}
              rows={5}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="audience">Who it is for (one per line)</Label>
            <Textarea
              id="audience"
              value={form.audience}
              onChange={(e) => set("audience", e.target.value)}
              rows={5}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="prerequisites">Prerequisites</Label>
          <Textarea
            id="prerequisites"
            value={form.prerequisites}
            onChange={(e) => set("prerequisites", e.target.value)}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="seo_title">SEO title</Label>
            <Input id="seo_title" value={form.seo_title} onChange={(e) => set("seo_title", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="seo_description">SEO description</Label>
            <Input
              id="seo_description"
              value={form.seo_description}
              onChange={(e) => set("seo_description", e.target.value)}
            />
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.published}
            onChange={(e) => set("published", e.target.checked)}
          />
          Published on /events
        </label>
        {cancelled && (
          <p className="text-sm font-medium text-destructive">This event is cancelled.</p>
        )}
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={saving} className="bg-brand-orange text-white hover:bg-brand-orange/90">
            {saving ? <Loader2 className="size-4 animate-spin" /> : eventId ? "Save changes" : "Create event"}
          </Button>
          {eventId && !cancelled && (
            <Button type="button" variant="outline" disabled={cancelling} onClick={onCancelEvent}>
              {cancelling ? <Loader2 className="size-4 animate-spin" /> : "Cancel event"}
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
