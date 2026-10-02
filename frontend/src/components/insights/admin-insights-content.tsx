"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, Plus, Star } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import {
  createStudioArticle,
  emptyArticleBody,
  listStudioArticles,
  setStudioArticleFeatured,
  type InsightStudioRow,
} from "@/lib/insights";

export function AdminInsightsContent() {
  const router = useRouter();
  const [rows, setRows] = useState<InsightStudioRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [featureBusyId, setFeatureBusyId] = useState<string | null>(null);

  useEffect(() => {
    listStudioArticles()
      .then(setRows)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Could not load Insights"))
      .finally(() => setLoading(false));
  }, []);

  async function create() {
    const created = await createStudioArticle({
      title: "Untitled article",
      excerpt: "",
      category: "Education",
      content_type: "Blog",
      body: emptyArticleBody(),
    });
    router.push(`/admin/insights/${created.id}`);
  }

  async function toggleFeatured(row: InsightStudioRow) {
    setError(null);
    setFeatureBusyId(row.id);
    try {
      const updated = await setStudioArticleFeatured(row.id, !row.featured);
      setRows((current) => current.map((item) => ({
        ...item,
        featured: updated.featured ? item.id === row.id : item.id === row.id ? false : item.featured,
      })));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update featured article");
    } finally {
      setFeatureBusyId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading Insights…
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Insights"
        description="Review author submissions and publish. Instructors do not have this workspace."
      />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <Button type="button" onClick={() => void create()}>
        <Plus className="size-4" />
        New article
      </Button>
      <div className="overflow-x-auto rounded-xl border">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Author</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Topic</th>
              <th className="px-4 py-3">Featured</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b">
                <td className="px-4 py-3">
                  <Link href={`/admin/insights/${row.id}`} className="font-medium hover:underline">
                    {row.title}
                  </Link>
                </td>
                <td className="px-4 py-3">{row.author_name}</td>
                <td className="px-4 py-3 capitalize">{row.status.replace("_", " ")}</td>
                <td className="px-4 py-3">{row.content_type}</td>
                <td className="px-4 py-3">{row.category}</td>
                <td className="px-4 py-3">
                  <Button
                    type="button"
                    variant={row.featured ? "secondary" : "outline"}
                    size="sm"
                    disabled={row.status !== "published" || featureBusyId !== null}
                    onClick={() => void toggleFeatured(row)}
                    aria-label={row.featured ? `Unfeature ${row.title}` : `Feature ${row.title}`}
                  >
                    {featureBusyId === row.id ? <Loader2 className="size-4 animate-spin" /> : <Star className="size-4" />}
                    {row.featured ? "Featured" : "Feature"}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
