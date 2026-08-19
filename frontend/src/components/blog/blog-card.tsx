import Link from "next/link";
import Image from "next/image";
import { ArrowRight, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { formatBlogDate } from "@/lib/mock-blog-data";
import type { BlogPost } from "@/types/blog";
import { cn } from "@/lib/utils";

type BlogCardProps = {
  post: BlogPost;
  className?: string;
};

const categoryColors: Record<string, string> = {
  Careers: "bg-brand-navy/10 text-brand-navy",
  Tutorials: "bg-brand-orange/10 text-brand-orange",
  Community: "bg-success/10 text-success",
  Guides: "bg-brand-orange/10 text-brand-orange",
};

export function BlogCard({ post, className }: BlogCardProps) {
  return (
    <Card
      className={cn(
        "group flex flex-col overflow-hidden rounded-2xl shadow-card transition-all duration-300 hover:-translate-y-1 hover:shadow-elevated",
        className
      )}
    >
      <div className="relative aspect-[16/9] overflow-hidden bg-brand-surface">
        {post.coverImage ? (
          <Image
            src={post.coverImage}
            alt=""
            fill
            className="object-cover transition-transform duration-500 group-hover:scale-[1.03]"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-brand-navy/90 via-brand-navy/70 to-brand-orange/80" />
        )}
        <div className="absolute inset-0 flex items-end bg-gradient-to-t from-black/50 via-transparent to-transparent p-6">
          <Badge
            className={cn(
              "bg-background/90 text-foreground backdrop-blur-sm",
              categoryColors[post.category]
            )}
          >
            {post.category}
          </Badge>
        </div>
      </div>
      <CardHeader className="flex-1">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <time dateTime={post.publishedAt}>{formatBlogDate(post.publishedAt)}</time>
          <span className="flex items-center gap-1">
            <Clock className="size-3.5" />
            {post.readTime}
          </span>
        </div>
        <CardTitle className="line-clamp-2 text-xl leading-snug group-hover:text-brand-navy dark:group-hover:text-brand-orange">
          <Link href={`/blog/${post.slug}`}>{post.title}</Link>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="line-clamp-3 text-muted-foreground">{post.excerpt}</p>
        <div className="mt-4 flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-full bg-brand-navy text-xs font-medium text-white">
            {post.author.avatar}
          </div>
          <div>
            <p className="text-sm font-medium">{post.author.name}</p>
            <p className="text-xs text-muted-foreground">{post.author.role}</p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="border-t">
        <Link
          href={`/blog/${post.slug}`}
          className="inline-flex items-center gap-1 text-sm font-medium text-brand-orange transition-transform group-hover:translate-x-1"
        >
          Read article
          <ArrowRight className="size-4" />
        </Link>
      </CardFooter>
    </Card>
  );
}
