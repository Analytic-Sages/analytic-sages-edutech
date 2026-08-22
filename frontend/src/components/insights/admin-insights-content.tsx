"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, Plus } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import {
  createStudioArticle,
  emptyArticleBody,
  listStudioArticles,
  type InsightStudioRow,
} from "@/lib/insights";

export function AdminInsightsContent() {
  const router = useRouter();
  const [rows, setRows] = useState<InsightStudioRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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
      body: emptyArticleBody(),
    });
    router.push(`/admin/insights/${created.id}`);
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
              <th className="px-4 py-3">Category</th>
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
                <td className="px-4 py-3">{row.category}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
