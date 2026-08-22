"use client";

import { useState } from "react";
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
  archiveStudioArticle,
  emptyArticleBody,
  publishStudioArticle,
  returnStudioArticle,
  submitStudioArticle,
  unpublishStudioArticle,
  updateStudioArticle,
  type ArticleBlock,
  type InsightStudio,
} from "@/lib/insights";

type Props = {
  article: InsightStudio;
  workspace: "studio" | "admin";
};

export function InsightComposer({ article, workspace }: Props) {
  const router = useRouter();
  const [title, setTitle] = useState(article.title);
  const [excerpt, setExcerpt] = useState(article.excerpt);
  const [category, setCategory] = useState(article.category);
  const [cover, setCover] = useState(article.cover_image_url || "");
  const [seoTitle, setSeoTitle] = useState(article.seo_title || "");
  const [seoDescription, setSeoDescription] = useState(article.seo_description || "");
  const [blocks, setBlocks] = useState<ArticleBlock[]>(article.body.blocks.length ? article.body.blocks : emptyArticleBody().blocks);
  const [preview, setPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [status, setStatus] = useState(article.status);

  const backHref = workspace === "admin" ? "/admin/insights" : "/studio";

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const saved = await updateStudioArticle(article.id, {
        title,
        excerpt,
        category,
        cover_image_url: cover || null,
        seo_title: seoTitle || null,
        seo_description: seoDescription || null,
        og_image_url: cover || null,
        tags: article.tags,
        body: { version: 1, blocks },
      });
      setStatus(saved.status);
      setNotice("Draft saved.");
      return saved;
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save");
      return null;
    } finally {
      setSaving(false);
    }
  }

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
          <Label htmlFor="title">Title</Label>
          <Input id="title" value={title} onChange={(event) => setTitle(event.target.value)} />
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
            <Label htmlFor="cover">Cover image URL</Label>
            <Input id="cover" value={cover} onChange={(event) => setCover(event.target.value)} />
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
