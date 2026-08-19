import { Play } from "lucide-react";
import {
  toYouTubeEmbedSrc,
  type TestimonialVideo,
} from "@/lib/testimonials";
import { cn } from "@/lib/utils";

export function TestimonialPlayer({
  item,
  featured = false,
}: {
  item: TestimonialVideo;
  featured?: boolean;
}) {
  const embedSrc = toYouTubeEmbedSrc(item.youtubeUrl);

  return (
    <article className={cn("flex flex-col", featured && "lg:col-span-2")}>
      <div className="relative aspect-video overflow-hidden rounded-2xl border bg-brand-surface shadow-card">
        {embedSrc ? (
          <iframe
            src={embedSrc}
            title={`${item.name}: Analytic Sages testimonial`}
            className="absolute inset-0 size-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
            loading="lazy"
            referrerPolicy="strict-origin-when-cross-origin"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-gradient-to-br from-brand-navy/[0.06] to-transparent px-6 text-center">
            <span className="flex size-14 items-center justify-center rounded-full bg-brand-navy text-white shadow-elevated sm:size-16">
              <Play className="size-6 fill-current sm:size-7" />
            </span>
            <p className="font-heading text-base font-semibold text-foreground sm:text-lg">
              Video coming soon
            </p>
            <p className="max-w-xs text-sm text-muted-foreground">
              Learner stories will appear here once published.
            </p>
          </div>
        )}
      </div>

      <div className={cn("mt-5", featured && "sm:mt-6")}>
        {item.quote && (
          <p
            className={cn(
              "leading-relaxed text-muted-foreground",
              featured ? "text-lg sm:text-xl" : "text-base",
            )}
          >
            &ldquo;{item.quote}&rdquo;
          </p>
        )}
        <p className="mt-3 font-heading text-base font-bold text-foreground sm:text-lg">
          {item.name}
        </p>
        <p className="mt-0.5 text-sm font-medium text-brand-orange">{item.role}</p>
      </div>
    </article>
  );
}
