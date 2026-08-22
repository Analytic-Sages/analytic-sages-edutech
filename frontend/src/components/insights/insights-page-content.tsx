"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Clock, Search } from "lucide-react";
import { BlogLearnCta } from "@/components/blog/blog-learn-cta";
import { InsightsSubscribeCta } from "@/components/insights/insights-subscribe-cta";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";
import { listInsights, type InsightCard } from "@/lib/insights";

function formatDate(value: string | null) {
  if (!value) return "";
  return new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", year: "numeric" }).format(
    new Date(value)
  );
}

export function InsightsPageContent() {
  const [posts, setPosts] = useState<InsightCard[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");

  useEffect(() => {
    listInsights()
      .then(setPosts)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Could not load Insights"));
  }, []);

  const categories = ["all", ...new Set(posts.map((post) => post.category))];
  const filtered = posts.filter((post) => {
    const matchesSearch =
      post.title.toLowerCase().includes(search.toLowerCase()) ||
      post.excerpt.toLowerCase().includes(search.toLowerCase());
    return matchesSearch && (category === "all" || post.category === category);
  });
  const featured = posts.filter((post) => post.featured);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="Insights"
        description="Research · Tutorials · Career · Industry · Education"
      />
      {error ? <p className="mb-6 text-sm text-destructive">{error}</p> : null}

      {featured.length > 0 && search === "" && category === "all" ? (
        <div className="mb-12 grid gap-6 lg:grid-cols-2">
          {featured.map((post) => (
            <InsightCardView key={post.slug} post={post} />
          ))}
        </div>
      ) : null}

      <div className="mb-8 flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search articles..."
            className="pl-9"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <select
          className="h-10 rounded-lg border bg-background px-3 text-sm sm:w-48"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        >
          {categories.map((item) => (
            <option key={item} value={item}>
              {item === "all" ? "All categories" : item}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((post) => (
          <InsightCardView key={post.slug} post={post} />
        ))}
      </div>
      {filtered.length === 0 && !error ? (
        <p className="py-12 text-center text-muted-foreground">No articles match your search.</p>
      ) : null}

      <div className="mt-16 space-y-8">
        <InsightsSubscribeCta />
        <BlogLearnCta />
      </div>
    </div>
  );
}

function InsightCardView({ post }: { post: InsightCard }) {
  return (
    <Card className="flex flex-col overflow-hidden rounded-2xl shadow-card">
      <div className="relative aspect-[16/9] bg-brand-surface">
        {post.cover_image_url ? (
          post.cover_image_url.startsWith("/") && !post.cover_image_url.startsWith("/api") ? (
            <Image src={post.cover_image_url} alt={post.title} fill className="object-cover" sizes="50vw" />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={post.cover_image_url} alt={post.title} className="h-full w-full object-cover" />
          )
        ) : (
          <div className="absolute inset-0 bg-brand-navy/80" />
        )}
        <div className="absolute bottom-4 left-4">
          <Badge className="bg-background/90 text-foreground">{post.category}</Badge>
        </div>
      </div>
      <CardHeader>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <time dateTime={post.published_at || undefined}>{formatDate(post.published_at)}</time>
          <span className="inline-flex items-center gap-1">
            <Clock className="size-3.5" />
            {post.read_time_minutes} min read
          </span>
        </div>
        <CardTitle className="text-xl leading-snug">
          <Link href={`/insights/${post.slug}`}>{post.title}</Link>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="line-clamp-3 text-muted-foreground">{post.excerpt}</p>
        <p className="mt-4 text-sm font-medium">{post.author.name}</p>
        <p className="text-xs text-muted-foreground">{post.author.title}</p>
      </CardContent>
    </Card>
  );
}
