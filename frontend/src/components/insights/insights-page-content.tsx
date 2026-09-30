"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Clock, Search } from "lucide-react";
import { BlogLearnCta } from "@/components/blog/blog-learn-cta";
import { InsightsSubscribeCta } from "@/components/insights/insights-subscribe-cta";
import { PageHeader } from "@/components/layout/page-header";
import { Input } from "@/components/ui/input";
import {
  INSIGHT_CONTENT_TYPES,
  INSIGHT_TOPICS,
  listInsights,
  type InsightCard,
} from "@/lib/insights";

function formatDate(value: string | null) {
  if (!value) return "";
  return new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", year: "numeric" }).format(new Date(value));
}

function contentType(post: InsightCard) {
  return post.content_type || "Blog";
}

export function InsightsPageContent() {
  const [posts, setPosts] = useState<InsightCard[]>([]);
  const [error, setError] = useState(false);
  const [search, setSearch] = useState(() => typeof window === "undefined" ? "" : new URLSearchParams(window.location.search).get("q") || "");
  const [type, setType] = useState(() => typeof window === "undefined" ? "all" : new URLSearchParams(window.location.search).get("type") || "all");
  const [topic, setTopic] = useState(() => typeof window === "undefined" ? "all" : new URLSearchParams(window.location.search).get("topic") || "all");

  useEffect(() => {
    listInsights().then(setPosts).catch(() => {
      setError(true);
    });
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (search.trim()) params.set("q", search.trim());
    if (type !== "all") params.set("type", type);
    if (topic !== "all") params.set("topic", topic);
    const query = params.toString();
    window.history.replaceState(null, "", query ? `${window.location.pathname}?${query}` : window.location.pathname);
  }, [search, type, topic]);

  const filtered = posts.filter((post) => {
    const query = search.trim().toLowerCase();
    const searchable = [post.title, post.excerpt, post.category, ...(post.tags || [])].join(" ").toLowerCase();
    return (!query || searchable.includes(query)) &&
      (type === "all" || contentType(post) === type) &&
      (topic === "all" || post.category === topic);
  });
  const topics = [...new Set([...INSIGHT_TOPICS, ...posts.map((post) => post.category).filter(Boolean)])];
  const featured = filtered.find((post) => post.featured) || (!search && type === "all" && topic === "all" ? posts.find((post) => post.featured) : null);
  const latest = filtered.filter((post) => post.slug !== featured?.slug);
  const hasFilters = Boolean(search.trim()) || type !== "all" || topic !== "all";

  function resetFilters() {
    setSearch("");
    setType("all");
    setTopic("all");
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-10">
      <PageHeader title="Insights" description="Research, tutorials, case studies and ideas from Analytic Sages." />
      <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
        Practical thinking on blockchain data, DeFi, AI, quantitative finance, software engineering and Web3.
      </p>

      <div className="mt-10 border-y py-5">
        <div className="flex flex-wrap items-center gap-2" aria-label="Filter by content type">
          <span className="mr-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">Content type</span>
          <FilterButton active={type === "all"} onClick={() => setType("all")}>All</FilterButton>
          {INSIGHT_CONTENT_TYPES.map((item) => <FilterButton key={item} active={type === item} onClick={() => setType(item)}>{item}</FilterButton>)}
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2" aria-label="Filter by topic">
          <span className="mr-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">Topics</span>
          <FilterButton active={topic === "all"} onClick={() => setTopic("all")}>All topics</FilterButton>
          {topics.map((item) => <FilterButton key={item} active={topic === item} onClick={() => setTopic(item)}>{item}</FilterButton>)}
        </div>
      </div>

      <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search insights, topics or tags" className="h-11 pl-9" value={search} onChange={(event) => setSearch(event.target.value)} />
        </div>
        {hasFilters ? <button type="button" onClick={resetFilters} className="text-left text-sm font-medium underline underline-offset-4">Reset filters</button> : null}
      </div>

      {error ? (
        <div className="mt-12 border-y py-10 text-center">
          <p className="font-heading text-xl font-semibold">Insights are temporarily unavailable</p>
          <p className="mt-2 text-sm text-muted-foreground">Please try again shortly.</p>
        </div>
      ) : null}

      {!error && featured ? (
        <section className="mt-14" aria-labelledby="featured-heading">
          <SectionLabel id="featured-heading">Featured</SectionLabel>
          <Link href={`/insights/${featured.slug}`} className="group mt-5 grid overflow-hidden border-y lg:grid-cols-[1.05fr_0.95fr]">
            <div className="relative aspect-[16/10] bg-brand-surface lg:aspect-auto lg:min-h-[360px]"><InsightImage post={featured} priority /></div>
            <div className="flex flex-col justify-center px-1 py-8 sm:px-8 lg:py-12">
              <ContentTypeLabel type={contentType(featured)} />
              <h2 className="mt-4 max-w-xl font-heading text-3xl font-bold leading-tight tracking-tight sm:text-4xl">{featured.title}</h2>
              <p className="mt-4 max-w-xl text-base leading-7 text-muted-foreground">{featured.excerpt}</p>
              <ArticleMeta post={featured} className="mt-7" />
              <span className="mt-7 text-sm font-semibold underline decoration-brand-orange decoration-2 underline-offset-4">Read {contentType(featured).toLowerCase()}</span>
            </div>
          </Link>
        </section>
      ) : null}

      {!error ? (
        <section className="mt-14" aria-labelledby="latest-heading">
          <div className="flex items-end justify-between gap-4"><SectionLabel id="latest-heading">Latest insights</SectionLabel><span className="text-sm text-muted-foreground">{latest.length} {latest.length === 1 ? "article" : "articles"}</span></div>
          {latest.length > 0 ? <div className="mt-5 grid gap-x-8 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">{latest.map((post) => <InsightCardView key={post.slug} post={post} />)}</div> : (
            <div className="mt-5 border-y py-12 text-center"><p className="font-heading text-xl font-semibold">No insights found</p><p className="mt-2 text-sm text-muted-foreground">Try another content type, topic or search term.</p><button type="button" onClick={resetFilters} className="mt-5 text-sm font-semibold underline underline-offset-4">Reset filters</button></div>
          )}
        </section>
      ) : null}

      <div className="mt-20 space-y-8"><InsightsSubscribeCta /><BlogLearnCta /></div>
    </div>
  );
}

function FilterButton({ active, children, onClick }: { active: boolean; children: React.ReactNode; onClick: () => void }) {
  return <button type="button" onClick={onClick} className={`border-b-2 px-2 py-1.5 text-sm transition-colors ${active ? "border-brand-orange font-semibold text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}>{children}</button>;
}

function SectionLabel({ id, children }: { id: string; children: React.ReactNode }) {
  return <h2 id={id} className="font-heading text-xs font-bold uppercase tracking-[0.18em] text-brand-orange">{children}</h2>;
}

function ContentTypeLabel({ type }: { type: string }) {
  return <span className="text-xs font-bold uppercase tracking-[0.16em] text-brand-orange">{type}</span>;
}

function ArticleMeta({ post, className = "" }: { post: InsightCard; className?: string }) {
  const names = post.contributors?.length ? post.contributors.map((author) => author.name).join(", ") : post.author.name;
  return <div className={`flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground ${className}`}><span>{names}</span><span aria-hidden="true">·</span><time dateTime={post.published_at || undefined}>{formatDate(post.published_at)}</time><span aria-hidden="true">·</span><span className="inline-flex items-center gap-1"><Clock className="size-3.5" />{post.read_time_minutes} min read</span></div>;
}

function InsightCardView({ post }: { post: InsightCard }) {
  return <article className="group"><Link href={`/insights/${post.slug}`}><div className="relative aspect-[16/10] overflow-hidden bg-brand-surface"><InsightImage post={post} /></div><div className="pt-5"><ContentTypeLabel type={contentType(post)} /><h3 className="mt-2 font-heading text-xl font-bold leading-snug group-hover:underline group-hover:decoration-brand-orange group-hover:underline-offset-4">{post.title}</h3><p className="mt-3 line-clamp-3 text-sm leading-6 text-muted-foreground">{post.excerpt}</p><ArticleMeta post={post} className="mt-5 text-xs" /></div></Link></article>;
}

function InsightImage({ post, priority = false }: { post: InsightCard; priority?: boolean }) {
  if (!post.cover_image_url) return <div className="absolute inset-0 bg-brand-navy/90" />;
  if (post.cover_image_url.startsWith("/") && !post.cover_image_url.startsWith("/api")) return <Image src={post.cover_image_url} alt={post.title} fill priority={priority} className="object-cover transition-transform duration-500 group-hover:scale-[1.02]" sizes="(min-width: 1024px) 50vw, 100vw" />;
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={post.cover_image_url} alt={post.title} className="h-full w-full object-cover" />;
}
