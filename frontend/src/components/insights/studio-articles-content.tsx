"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, Plus } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { ApiError, getMe } from "@/lib/api";
import {
  createStudioArticle,
  emptyArticleBody,
  listStudioArticles,
  type InsightStudioRow,
} from "@/lib/insights";

export function StudioArticlesContent() {
  const router = useRouter();
  const [rows, setRows] = useState<InsightStudioRow[]>([]);
  const [role, setRole] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getMe()
      .then((user) => {
        if (cancelled) return;
        if (user.role === "editor" || user.role === "admin") {
          router.replace("/admin/insights");
          return null;
        }
        if (user.role !== "author") {
          router.replace(user.role === "instructor" ? "/staff" : "/dashboard");
          return null;
        }
        setRole(user.role);
        return listStudioArticles();
      })
      .then((articles) => {
        if (cancelled || !articles) return;
        setRows(articles);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load articles");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function create() {
    const created = await createStudioArticle({
      title: "Untitled article",
      excerpt: "",
      category: "Education",
      body: emptyArticleBody(),
    });
    router.push(`/studio/${created.id}`);
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading your articles…
      </div>
    );
  }

  const drafts = rows.filter((row) => row.status === "draft").length;
  const pending = rows.filter((row) => row.status === "pending_review").length;
  const published = rows.filter((row) => row.status === "published").length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="My articles"
        description="Write drafts and submit them for review. Editors publish — authors cannot."
      />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <div className="flex flex-wrap gap-4 text-sm">
        <span>Drafts {drafts}</span>
        <span>Pending review {pending}</span>
        <span>Published {published}</span>
      </div>
      <Button type="button" onClick={() => void create()}>
        <Plus className="size-4" />
        New article
      </Button>
      <div className="overflow-x-auto rounded-xl border">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Updated</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b">
                <td className="px-4 py-3">
                  <Link href={`/studio/${row.id}`} className="font-medium hover:underline">
                    {row.title}
                  </Link>
                </td>
                <td className="px-4 py-3 capitalize">{row.status.replace("_", " ")}</td>
                <td className="px-4 py-3">{row.category}</td>
                <td className="px-4 py-3 text-muted-foreground">
                  {new Date(row.updated_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {role && rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">No articles yet. Create a draft to start.</p>
      ) : null}
    </div>
  );
}
