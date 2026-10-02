import { apiFetch, getAccessToken } from "@/lib/api";

export type InsightAuthor = {
  name: string;
  title: string;
  bio: string;
  photo_url: string | null;
};

export type InsightContributor = InsightAuthor & {
  author_profile_id: string;
  contribution_role: string;
};

export type InsightAuthorOption = {
  id: string;
  name: string;
  title: string;
};

export type InsightCard = {
  slug: string;
  title: string;
  excerpt: string;
  category: string;
  content_type: string;
  tags: string[];
  cover_image_url: string | null;
  featured: boolean;
  read_time_minutes: number;
  published_at: string | null;
  author: InsightAuthor;
  contributors: InsightContributor[];
};

export type InsightArticle = InsightCard & {
  body: { version: number; blocks: ArticleBlock[] };
  tags: string[];
  seo_title: string | null;
  seo_description: string | null;
  og_image_url: string | null;
  related: InsightCard[];
};

export type ArticleStatus = "draft" | "pending_review" | "published" | "archived";

export type ArticleBlock =
  | { type: "paragraph"; text: string }
  | { type: "heading"; level: 1 | 2 | 3 | 4; text: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "quote"; text: string }
  | { type: "divider" }
  | { type: "code"; language: string; code: string }
  | {
      type: "image";
      src: string;
      alt: string;
      caption?: string;
      credit?: string;
      width?: "small" | "medium" | "large" | "full";
      aspect?: "original" | "square" | "landscape" | "portrait" | "wide";
    }
  | { type: "youtube"; videoId: string }
  | { type: "table"; headers: string[]; rows: string[][] }
  | {
      type: "chart";
      chartType: "line" | "bar" | "pie" | "scatter";
      title?: string;
      labels: string[];
      values: number[];
      source?: string;
      caption?: string;
    }
  | { type: "takeaways"; items: string[] };

export type InsightStudio = {
  id: string;
  slug: string;
  title: string;
  excerpt: string;
  cover_image_url: string | null;
  category: string;
  content_type: string;
  tags: string[];
  body: { version: number; blocks: ArticleBlock[] };
  status: ArticleStatus;
  featured: boolean;
  seo_title: string | null;
  seo_description: string | null;
  og_image_url: string | null;
  read_time_minutes: number;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  author: InsightAuthor;
  contributors: InsightContributor[];
  can_publish: boolean;
  can_submit: boolean;
};

export type InsightStudioRow = {
  id: string;
  slug: string;
  title: string;
  status: ArticleStatus;
  featured: boolean;
  category: string;
  content_type: string;
  updated_at: string;
  published_at: string | null;
  author_name: string;
};

export const INSIGHT_CATEGORIES = [
  "Research",
  "Tutorials",
  "Career",
  "Industry",
  "Education",
  "Guides",
] as const;

export const INSIGHT_CONTENT_TYPES = ["Research", "Blog", "Tutorial", "Case Study"] as const;

export const INSIGHT_TOPICS = [
  "Blockchain Data",
  "DeFi",
  "AI",
  "Quantitative Finance",
  "Software Engineering",
  "Web3",
  "Career",
] as const;

export function emptyArticleBody(): InsightStudio["body"] {
  return { version: 1, blocks: [{ type: "paragraph", text: "" }] };
}

export function listInsights() {
  return apiFetch<InsightCard[]>("/api/v1/insights", { auth: false });
}

export function getInsight(slug: string) {
  return apiFetch<InsightArticle>(`/api/v1/insights/${encodeURIComponent(slug)}`, { auth: false });
}

export function listInsightAuthors() {
  return apiFetch<InsightAuthorOption[]>("/api/v1/studio/authors");
}

export function subscribeInsights(email: string) {
  return apiFetch<{ message: string }>("/api/v1/insights/subscribe", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email }),
  });
}

export function listStudioArticles() {
  return apiFetch<InsightStudioRow[]>("/api/v1/studio/articles");
}

export function getStudioArticle(id: string) {
  return apiFetch<InsightStudio>(`/api/v1/studio/articles/${id}`);
}

export function createStudioArticle(payload: Partial<InsightStudio> & { title: string }) {
  return apiFetch<InsightStudio>("/api/v1/studio/articles", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateStudioArticle(id: string, payload: unknown) {
  return apiFetch<InsightStudio>(`/api/v1/studio/articles/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function setStudioArticleFeatured(id: string, featured: boolean) {
  return apiFetch<InsightStudio>(`/api/v1/studio/articles/${id}/feature`, {
    method: featured ? "POST" : "DELETE",
  });
}

export function submitStudioArticle(id: string) {
  return apiFetch<InsightStudio>(`/api/v1/studio/articles/${id}/submit`, { method: "POST" });
}

export function publishStudioArticle(id: string) {
  return apiFetch<InsightStudio>(`/api/v1/studio/articles/${id}/publish`, { method: "POST" });
}

export function unpublishStudioArticle(id: string) {
  return apiFetch<InsightStudio>(`/api/v1/studio/articles/${id}/unpublish`, { method: "POST" });
}

export function returnStudioArticle(id: string) {
  return apiFetch<InsightStudio>(`/api/v1/studio/articles/${id}/return`, { method: "POST" });
}

export function archiveStudioArticle(id: string) {
  return apiFetch<InsightStudio>(`/api/v1/studio/articles/${id}/archive`, { method: "POST" });
}

export async function uploadInsightImage(file: File) {
  const headers = new Headers();
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/api/v1/insights/uploads", {
    method: "POST",
    headers,
    body,
    credentials: "include",
  });
  if (!response.ok) {
    const data = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(data?.detail || "Upload failed");
  }
  return response.json() as Promise<{ url: string }>;
}
