import Image from "next/image";
import { notFound } from "next/navigation";
import { ArrowLeft, Clock } from "lucide-react";
import { BlogLearnCta } from "@/components/blog/blog-learn-cta";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { formatBlogDate, getBlogPostBySlug } from "@/lib/mock-blog-data";
import { blogPostingJsonLd, pageMetadata } from "@/lib/seo";

type BlogPostPageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: BlogPostPageProps) {
  const { slug } = await params;
  const post = getBlogPostBySlug(slug);
  if (!post) return { title: "Article Not Found" };
  return pageMetadata({
    title: post.title,
    description: post.excerpt,
    path: `/blog/${post.slug}`,
    image: post.coverImage,
    type: "article",
  });
}

export default async function BlogPostPage({ params }: BlogPostPageProps) {
  const { slug } = await params;
  const post = getBlogPostBySlug(slug);

  if (!post) notFound();

  return (
    <article className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(blogPostingJsonLd(post)) }}
      />
      <PageHeader
        breadcrumbs={[
          { label: "Blog", href: "/blog" },
          { label: post.title },
        ]}
        title={post.title}
        description={post.excerpt}
      />

      {post.coverImage && (
        <div className="relative mb-8 aspect-[16/9] overflow-hidden rounded-[20px] shadow-elevated">
          <Image
            src={post.coverImage}
            alt={post.title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 768px"
            priority
          />
        </div>
      )}

      <div className="mb-8 flex flex-wrap items-center gap-4 border-b pb-8">
        <Badge variant="outline">{post.category}</Badge>
        <time dateTime={post.publishedAt} className="text-sm text-muted-foreground">
          {formatBlogDate(post.publishedAt)}
        </time>
        <span className="flex items-center gap-1 text-sm text-muted-foreground">
          <Clock className="size-3.5" />
          {post.readTime}
        </span>
        <div className="flex items-center gap-2 sm:ml-auto">
          <div className="flex size-9 items-center justify-center rounded-full bg-brand-navy text-xs font-medium text-white">
            {post.author.avatar}
          </div>
          <div>
            <p className="text-sm font-medium">{post.author.name}</p>
            <p className="text-xs text-muted-foreground">{post.author.role}</p>
          </div>
        </div>
      </div>

      <div className="prose prose-neutral max-w-none space-y-6">
        {post.content.map((paragraph) => (
          <p key={paragraph.slice(0, 40)} className="text-lg leading-relaxed text-muted-foreground">
            {paragraph}
          </p>
        ))}
      </div>

      <div className="mt-12 space-y-8 border-t pt-8">
        <BlogLearnCta />
        <ButtonLink href="/blog" variant="outline" className="gap-2">
          <ArrowLeft className="size-4" />
          Back to blog
        </ButtonLink>
      </div>
    </article>
  );
}
