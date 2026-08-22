"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { InsightComposer } from "@/components/insights/insight-composer";
import { ApiError } from "@/lib/api";
import { getStudioArticle, type InsightStudio } from "@/lib/insights";

export function InsightEditLoader({
  id,
  workspace,
}: {
  id: string;
  workspace: "studio" | "admin";
}) {
  const [article, setArticle] = useState<InsightStudio | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStudioArticle(id)
      .then(setArticle)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Could not load article"));
  }, [id]);

  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!article) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading article…
      </div>
    );
  }
  return <InsightComposer key={article.id} article={article} workspace={workspace} />;
}
