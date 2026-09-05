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
  updateAdminEvent,
  uploadAdminEventImage,
  type EventAdmin,
  type EventType,
} from "@/lib/api";
import { EVENT_TYPE_LABELS, isBundledEventCover, resolveEventCoverSrc } from "@/lib/events";

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
  youtube_live_url: string;
  recording_url: string;
  learn_topics: string;
  audience: string;
  prerequisites: string;
  related_course_slug: string;
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
  youtube_live_url: "",
  recording_url: "",
  learn_topics: "",
  audience: "",
  prerequisites: "",
  related_course_slug: "",
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
    youtube_live_url: event.youtube_live_url ?? "",
    recording_url: event.recording_url ?? "",
    learn_topics: event.learn_topics.join("\n"),
    audience: event.audience.join("\n"),
    prerequisites: event.prerequisites,
    related_course_slug: event.related_course_slug ?? "",
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
  return {
    slug: form.slug.trim(),
    title: form.title.trim(),
    event_type: form.event_type,
    short_description: form.short_description.trim(),
    description: form.description.trim(),
    cover_image: form.cover_image.trim() || null,
    starts_at: form.starts_at ? withSeconds(form.starts_at) : null,
    ends_at: form.ends_at ? withSeconds(form.ends_at) : null,
    timezone: form.timezone.trim() || "Africa/Lagos",
    host_name: form.host_name.trim() || null,
    youtube_live_url: form.youtube_live_url.trim() || null,
    recording_url: form.recording_url.trim() || null,
    learn_topics: lines(form.learn_topics),
    audience: lines(form.audience),
    prerequisites: form.prerequisites.trim(),
    related_course_slug: form.related_course_slug.trim() || null,
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

  useEffect(() => {
    if (!eventId) return;
    let ignore = false;
    getAdminEvent(eventId)
      .then((event) => {
        if (ignore) return;
        setForm(fromEvent(event));
        setCancelled(event.cancelled);
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

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = toPayload(form);
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
            <Input id="title" value={form.title} onChange={(e) => set("title", e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="slug">Slug</Label>
            <Input id="slug" value={form.slug} onChange={(e) => set("slug", e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="event_type">Type</Label>
            <select
              id="event_type"
              className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
              value={form.event_type}
              onChange={(e) => set("event_type", e.target.value as EventType)}
            >
              {Object.entries(EVENT_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
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
          <div className="space-y-2">
            <Label htmlFor="related_course_slug">Related course slug</Label>
            <Input
              id="related_course_slug"
              value={form.related_course_slug}
              onChange={(e) => set("related_course_slug", e.target.value)}
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="youtube_live_url">YouTube Live URL</Label>
            <Input
              id="youtube_live_url"
              value={form.youtube_live_url}
              onChange={(e) => set("youtube_live_url", e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="recording_url">Recording URL</Label>
            <Input
              id="recording_url"
              value={form.recording_url}
              onChange={(e) => set("recording_url", e.target.value)}
            />
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
