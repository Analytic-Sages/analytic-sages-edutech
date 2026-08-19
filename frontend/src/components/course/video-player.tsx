import { cn } from "@/lib/utils";

type VideoPlayerProps = {
  videoId?: string | null;
  embedUrl?: string | null;
  title: string;
  provider?: string;
  className?: string;
};

export function youtubeEmbedSrc(videoId: string) {
  return `https://www.youtube.com/embed/${videoId}`;
}

export function youtubeThumbnailSrc(videoId: string) {
  return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
}

function resolveSrc(videoId?: string | null, embedUrl?: string | null, provider = "youtube") {
  if (embedUrl) return embedUrl;
  if (videoId && provider === "youtube") return youtubeEmbedSrc(videoId);
  return null;
}

export function VideoPlayer({
  videoId,
  embedUrl,
  title,
  provider = "youtube",
  className,
}: VideoPlayerProps) {
  const src = resolveSrc(videoId, embedUrl, provider);

  return (
    <div
      className={cn(
        "relative aspect-video w-full overflow-hidden rounded-xl border bg-brand-navy shadow-card",
        className
      )}
    >
      {src ? (
        <iframe
          src={src}
          title={title}
          className="absolute inset-0 size-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
          referrerPolicy="strict-origin-when-cross-origin"
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-sm text-white/80">
          Video is not available for this lesson yet.
        </div>
      )}
    </div>
  );
}
