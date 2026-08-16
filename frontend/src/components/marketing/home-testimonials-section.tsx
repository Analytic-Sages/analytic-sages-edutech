import { Play } from "lucide-react";
import { PatternBackground } from "@/components/marketing/pattern-background";
import {
  homeTestimonials,
  toYouTubeEmbedSrc,
  type TestimonialVideo,
} from "@/lib/testimonials";
import { cn } from "@/lib/utils";

function TestimonialPlayer({
  item,
  featured = false,
}: {
  item: TestimonialVideo;
  featured?: boolean;
}) {
  const embedSrc = toYouTubeEmbedSrc(item.youtubeUrl);

  return (
    <article className={cn("flex flex-col", featured && "lg:col-span-2")}>
      <div
        className={cn(
          "relative overflow-hidden rounded-2xl border bg-brand-surface shadow-card",
          featured ? "aspect-video" : "aspect-video"
        )}
      >
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
              featured ? "text-lg sm:text-xl" : "text-base"
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

export function HomeTestimonialsSection() {
  const [featured, ...rest] = homeTestimonials;

  return (
    <section className="relative overflow-hidden border-y bg-background py-24 sm:py-32">
      <PatternBackground />
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-lg font-bold uppercase tracking-[0.12em] text-brand-orange sm:text-xl">
            Testimonials
          </p>
          <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem]">
            Hear from our learners
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-muted-foreground">
            Real stories from people building blockchain analytics skills with Analytic Sages.
          </p>
        </div>

        <div className="mt-14 grid gap-10 lg:grid-cols-2 lg:gap-12">
          {featured && <TestimonialPlayer item={featured} featured />}
          {rest.map((item) => (
            <TestimonialPlayer key={item.id} item={item} />
          ))}
        </div>
      </div>
    </section>
  );
}
