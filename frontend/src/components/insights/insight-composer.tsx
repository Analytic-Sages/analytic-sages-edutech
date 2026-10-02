"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArticleBody } from "@/components/insights/article-body";
import { ArticleEditor } from "@/components/insights/article-editor";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import {
  INSIGHT_CATEGORIES,
  INSIGHT_CONTENT_TYPES,
  archiveStudioArticle,
  emptyArticleBody,
  publishStudioArticle,
  returnStudioArticle,
  submitStudioArticle,
  unpublishStudioArticle,
  updateStudioArticle,
  uploadInsightImage,
  listInsightAuthors,
  type ArticleBlock,
  type InsightStudio,
  type InsightAuthorOption,
} from "@/lib/insights";

type Props = {
  article: InsightStudio;
  workspace: "studio" | "admin";
};

type DraftSnapshot = {
  title: string;
  slug: string;
  excerpt: string;
  category: string;
  contentType: string;
  cover: string;
  seoTitle: string;
  seoDescription: string;
  contributors: InsightStudio["contributors"];
  blocks: ArticleBlock[];
  savedAt: number;
};

function draftKey(articleId: string) {
  return `insights-draft-${articleId}`;
}

function readDraft(articleId: string): DraftSnapshot | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(draftKey(articleId));
  if (!raw) return null;
  try {
    return JSON.parse(raw) as DraftSnapshot;
  } catch {
    window.localStorage.removeItem(draftKey(articleId));
    return null;
  }
}

export function InsightComposer({ article, workspace }: Props) {
  const router = useRouter();
  const [draft] = useState(() => readDraft(article.id));
  const [title, setTitle] = useState(draft?.title ?? article.title);
  const [slug, setSlug] = useState(draft?.slug ?? article.slug);
  const [excerpt, setExcerpt] = useState(draft?.excerpt ?? article.excerpt);
  const [category, setCategory] = useState(draft?.category ?? article.category);
  const [contentType, setContentType] = useState(draft?.contentType ?? article.content_type ?? "Blog");
  const [authorOptions, setAuthorOptions] = useState<InsightAuthorOption[]>([]);
  const [contributors, setContributors] = useState(draft?.contributors ?? article.contributors ?? []);
  const [cover, setCover] = useState(draft?.cover ?? article.cover_image_url ?? "");
  const [coverUploading, setCoverUploading] = useState(false);
  const [coverError, setCoverError] = useState<string | null>(null);
  const [seoTitle, setSeoTitle] = useState(draft?.seoTitle ?? article.seo_title ?? "");
  const [seoDescription, setSeoDescription] = useState(draft?.seoDescription ?? article.seo_description ?? "");
  const [blocks, setBlocks] = useState<ArticleBlock[]>(
    draft?.blocks ?? (article.body.blocks.length ? article.body.blocks : emptyArticleBody().blocks)
  );
  const [preview, setPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(
    draft ? "Restored your unsaved changes from this browser." : null
  );
  const [status, setStatus] = useState(article.status);
  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const skipNextSnapshot = useRef(true);

  const backHref = workspace === "admin" ? "/admin/insights" : "/studio";

  useEffect(() => {
    listInsightAuthors().then(setAuthorOptions).catch(() => setAuthorOptions([]));
  }, []);

  async function onCoverFile(file: File | undefined) {
    if (!file) return;
    setCoverError(null);
    setCoverUploading(true);
    try {
      const uploaded = await uploadInsightImage(file);
      setCover(uploaded.url);
    } catch (err) {
      setCoverError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setCoverUploading(false);
    }
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const saved = await updateStudioArticle(article.id, {
        title,
        slug,
        excerpt,
        category,
        content_type: contentType,
        cover_image_url: cover || null,
        seo_title: seoTitle || null,
        seo_description: seoDescription || null,
        og_image_url: cover || null,
        tags: article.tags,
        contributors: contributors.map((item) => ({
          author_profile_id: item.author_profile_id,
          contribution_role: item.contribution_role,
        })),
        body: { version: 1, blocks },
      });
      setStatus(saved.status);
      setSlug(saved.slug);
      setNotice("Draft saved.");
      if (typeof window !== "undefined") window.localStorage.removeItem(draftKey(article.id));
      return saved;
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save");
      return null;
    } finally {
      setSaving(false);
    }
  }

  // Keep a stable ref to the latest save() so the debounce effect doesn't need it in deps.
  const saveRef = useRef(save);
  useEffect(() => {
    saveRef.current = save;
  });

  // Instantly back up every change to localStorage, then debounce a real autosave to the server.
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (skipNextSnapshot.current) {
      skipNextSnapshot.current = false;
      return;
    }
    const snapshot: DraftSnapshot = {
      title,
      slug,
      excerpt,
      category,
      contentType,
      cover,
      seoTitle,
      seoDescription,
      contributors,
      blocks,
      savedAt: Date.now(),
    };
    window.localStorage.setItem(draftKey(article.id), JSON.stringify(snapshot));

    if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    autosaveTimer.current = setTimeout(() => {
      void saveRef.current();
    }, 3000);

    return () => {
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    };
  }, [title, slug, excerpt, category, contentType, cover, seoTitle, seoDescription, contributors, blocks, article.id]);

  async function run(action: () => Promise<InsightStudio>, ok: string) {
    const saved = await save();
    if (!saved) return;
    setSaving(true);
    try {
      const next = await action();
      setStatus(next.status);
      setNotice(ok);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Action failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        breadcrumbs={[{ label: workspace === "admin" ? "Insights" : "My articles", href: backHref }, { label: title || "Untitled" }]}
        title={workspace === "admin" ? "Review article" : "Edit article"}
        description={
          article.can_publish
            ? "Editors publish. Authors cannot."
            : "Save a draft, preview, then submit for editorial review. You cannot publish."
        }
      />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {notice ? <p className="text-sm text-muted-foreground">{notice} Status: {status.replace("_", " ")}</p> : null}

      <div className="grid gap-4">
        <div>
          <Label>Authors and contributors</Label>
          <div className="mt-2 space-y-3 rounded-lg border p-3">
            {authorOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">No author profiles are available yet.</p>
            ) : authorOptions.map((option) => {
              const selected = contributors.find((item) => item.author_profile_id === option.id);
              return (
                <div key={option.id} className="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <label className="flex min-w-0 flex-1 items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={Boolean(selected)}
                      onChange={(event) => {
                        if (event.target.checked) {
                          setContributors((current) => [...current, {
                            author_profile_id: option.id,
                            name: option.name,
                            title: option.title,
                            bio: "",
                            photo_url: null,
                            contribution_role: "Contributor",
                          }]);
                        } else {
                          setContributors((current) => current.filter((item) => item.author_profile_id !== option.id));
                        }
                      }}
                    />
                    <span className="truncate">{option.name} <span className="text-muted-foreground">· {option.title}</span></span>
                  </label>
                  {selected ? (
                    <Input
                      className="sm:w-48"
                      aria-label={`Contribution role for ${option.name}`}
                      value={selected.contribution_role}
                      onChange={(event) => setContributors((current) => current.map((item) => item.author_profile_id === option.id ? { ...item, contribution_role: event.target.value } : item))}
                      placeholder="Contribution role"
                    />
                  ) : null}
                </div>
              );
            })}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">The first selected person is shown as the primary author. Drag ordering is not needed: select contributors in the desired byline order.</p>
        </div>
        <div>
          <Label htmlFor="title">Title</Label>
          <Input id="title" value={title} onChange={(event) => setTitle(event.target.value)} />
        </div>
        <div>
          <Label htmlFor="slug">URL slug</Label>
          <Input
            id="slug"
            value={slug}
            onChange={(event) => setSlug(event.target.value)}
            placeholder="my-article-title"
          />
          <p className="mt-1 text-xs text-muted-foreground">
            Published at /insights/{slug || "…"}. Changing this after publishing breaks old links.
          </p>
        </div>
        <div>
          <Label htmlFor="excerpt">Subtitle / excerpt</Label>
          <Textarea id="excerpt" value={excerpt} onChange={(event) => setExcerpt(event.target.value)} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="category">Category</Label>
            <select
              id="category"
              className="mt-1 h-10 w-full rounded-lg border bg-background px-3 text-sm"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              {INSIGHT_CATEGORIES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="content-type">Content type</Label>
            <select
              id="content-type"
              className="mt-1 h-10 w-full rounded-lg border bg-background px-3 text-sm"
              value={contentType}
              onChange={(event) => setContentType(event.target.value)}
            >
              {INSIGHT_CONTENT_TYPES.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="cover">Cover image</Label>
            <div className="mt-1 space-y-2">
              {cover ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={cover} alt="Cover preview" className="h-32 w-full rounded-lg object-cover" />
              ) : null}
              <Input
                id="cover-upload"
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                disabled={coverUploading}
                onChange={(event) => void onCoverFile(event.target.files?.[0])}
              />
              <Input id="cover" placeholder="Or paste an image URL" value={cover} onChange={(event) => setCover(event.target.value)} />
              {coverUploading ? <p className="text-xs text-muted-foreground">Uploading…</p> : null}
              {coverError ? <p className="text-xs text-destructive">{coverError}</p> : null}
            </div>
          </div>
        </div>
        <div>
          <Label htmlFor="seo-title">SEO title</Label>
          <Input id="seo-title" value={seoTitle} onChange={(event) => setSeoTitle(event.target.value)} />
        </div>
        <div>
          <Label htmlFor="seo-desc">SEO description</Label>
          <Textarea id="seo-desc" value={seoDescription} onChange={(event) => setSeoDescription(event.target.value)} />
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" variant={preview ? "outline" : "default"} onClick={() => setPreview(false)}>
          Editor
        </Button>
        <Button type="button" variant={preview ? "default" : "outline"} onClick={() => setPreview(true)}>
          Preview
        </Button>
      </div>

      {preview ? (
        <article className="rounded-2xl border p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">{category}</p>
          <h1 className="mt-2 font-heading text-3xl font-bold">{title}</h1>
          <p className="mt-3 text-muted-foreground">{excerpt}</p>
          <div className="mt-8">
            <ArticleBody blocks={blocks} />
          </div>
        </article>
      ) : (
        <ArticleEditor blocks={blocks} onChange={setBlocks} />
      )}

      <div className="flex flex-wrap gap-2 border-t pt-4">
        <Button type="button" onClick={() => void save()} disabled={saving}>
          Save draft
        </Button>
        {article.can_submit ? (
          <Button
            type="button"
            variant="outline"
            disabled={saving}
            onClick={() => void run(() => submitStudioArticle(article.id), "Submitted for review.")}
          >
            Submit for review
          </Button>
        ) : null}
        {article.can_publish ? (
          <>
            <Button
              type="button"
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
              disabled={saving}
              onClick={() =>
                void run(
                  () => publishStudioArticle(article.id),
                  "Published. Subscribers are emailed the first time this article goes live.",
                )
              }
            >
              Publish
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={saving}
              onClick={() => void run(() => unpublishStudioArticle(article.id), "Unpublished.")}
            >
              Unpublish
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={saving}
              onClick={() => void run(() => returnStudioArticle(article.id), "Returned to draft.")}
            >
              Send back
            </Button>
            <Button
              type="button"
              variant="ghost"
              disabled={saving}
              onClick={() => void run(() => archiveStudioArticle(article.id), "Archived.")}
            >
              Archive
            </Button>
          </>
        ) : null}
        <Button type="button" variant="ghost" onClick={() => router.push(backHref)}>
          Back
        </Button>
      </div>
      {article.can_publish ? (
        <p className="text-xs text-muted-foreground">
          The first Publish emails everyone on the Insights list. Edits and republishing do not send
          again. Custom emails are sent from Resend Broadcasts, not this desk.
        </p>
      ) : null}
    </div>
  );
}
