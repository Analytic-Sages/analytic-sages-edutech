import Image from "next/image";
import { notFound } from "next/navigation";
import { Clock } from "lucide-react";
import { BlogLearnCta } from "@/components/blog/blog-learn-cta";
import { ArticleBody } from "@/components/insights/article-body";
import { ArticleShare } from "@/components/insights/article-share";
import { InsightsSubscribeCta } from "@/components/insights/insights-subscribe-cta";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { ApiError } from "@/lib/api";
import { getInsight, type InsightArticle } from "@/lib/insights";
import { blogPostingJsonLd, pageMetadata } from "@/lib/seo";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ slug: string }> };

function formatDate(value: string | null) {
  if (!value) return "";
  return new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", year: "numeric" }).format(
    new Date(value)
  );
}

async function loadPost(slug: string): Promise<InsightArticle | null> {
  try {
    return await getInsight(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export async function generateMetadata({ params }: Props) {
  const { slug } = await params;
  const post = await loadPost(slug);
  if (!post) return { title: "Article Not Found" };
  return pageMetadata({
    title: post.seo_title || post.title,
    description: post.seo_description || post.excerpt,
    path: `/insights/${post.slug}`,
    image: post.og_image_url || post.cover_image_url,
    type: "article",
  });
}

export default async function InsightArticlePage({ params }: Props) {
  const { slug } = await params;
  const post = await loadPost(slug);
  if (!post) notFound();

  return (
    <article className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(
            blogPostingJsonLd({
              title: post.title,
              excerpt: post.excerpt,
              slug: post.slug,
              publishedAt: post.published_at || new Date().toISOString(),
              coverImage: post.cover_image_url || undefined,
              author: { name: post.author.name },
            })
          ),
        }}
      />
      <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">{post.category}</p>
      <h1 className="mt-3 font-heading text-4xl font-bold tracking-tight">{post.title}</h1>
      {post.excerpt ? <p className="mt-4 text-lg text-muted-foreground">{post.excerpt}</p> : null}

      {post.cover_image_url ? (
        <div className="relative my-8 aspect-[16/9] overflow-hidden">
          {post.cover_image_url.startsWith("/") && !post.cover_image_url.startsWith("/api") ? (
            <Image src={post.cover_image_url} alt={post.title} fill className="object-cover" priority sizes="768px" />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={post.cover_image_url} alt={post.title} className="h-full w-full object-cover" />
          )}
        </div>
      ) : null}

      <div className="mb-8 flex flex-wrap items-center gap-4 border-b pb-8">
        <Badge variant="outline">{post.category}</Badge>
        <time dateTime={post.published_at || undefined} className="text-sm text-muted-foreground">
          {formatDate(post.published_at)}
        </time>
        <span className="flex items-center gap-1 text-sm text-muted-foreground">
          <Clock className="size-3.5" />
          {post.read_time_minutes} min read
        </span>
        <div className="sm:ml-auto">
          <p className="text-sm font-medium">{post.author.name}</p>
          <p className="text-xs text-muted-foreground">{post.author.title}</p>
        </div>
      </div>

      <ArticleBody blocks={post.body.blocks} />

      {post.author.bio ? (
        <section className="mt-12 border-t pt-8">
          <p className="text-sm font-medium">{post.author.name}</p>
          <p className="text-sm text-muted-foreground">{post.author.title}</p>
          <p className="mt-2 text-sm text-muted-foreground">{post.author.bio}</p>
        </section>
      ) : null}

      {post.related.length > 0 ? (
        <section className="mt-12 border-t pt-8">
          <h2 className="font-heading text-xl font-bold">Related Insights</h2>
          <ul className="mt-4 space-y-3">
            {post.related.map((item) => (
              <li key={item.slug}>
                <ButtonLink href={`/insights/${item.slug}`} variant="outline">
                  {item.title}
                </ButtonLink>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="mt-12 space-y-8 border-t pt-8">
        <ArticleShare title={post.title} path={`/insights/${post.slug}`} />
        <InsightsSubscribeCta />
        <BlogLearnCta />
        <ButtonLink href="/insights" variant="outline">
          Back to Insights
        </ButtonLink>
      </div>
    </article>
  );
}
