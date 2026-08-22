import { cn } from "@/lib/utils";

type VideoPlayerProps = {
  videoId?: string | null;
  embedUrl?: string | null;
  title: string;
  provider?: string;
  className?: string;
  requireOpen?: boolean;
  opened?: boolean;
  onOpened?: () => void;
};

export function youtubeEmbedSrc(videoId: string, autoplay = false) {
  const params = new URLSearchParams();
  if (autoplay) params.set("autoplay", "1");
  // Captions stay in YouTube controls. Do not force them on, and do not burn them into the file.
  params.set("cc_load_policy", "0");
  return `https://www.youtube.com/embed/${videoId}?${params.toString()}`;
}

export function youtubeThumbnailSrc(videoId: string) {
  return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
}

function resolveSrc(
  videoId?: string | null,
  embedUrl?: string | null,
  provider = "youtube",
  autoplay = false
) {
  if (embedUrl) return embedUrl;
  if (videoId && provider === "youtube") return youtubeEmbedSrc(videoId, autoplay);
  return null;
}

export function VideoPlayer({
  videoId,
  embedUrl,
  title,
  provider = "youtube",
  className,
  requireOpen = false,
  opened = false,
  onOpened,
}: VideoPlayerProps) {
  const src = resolveSrc(videoId, embedUrl, provider, requireOpen && opened);
  const showPoster = Boolean(requireOpen && src && !opened);

  return (
    <div
      className={cn(
        "relative aspect-video w-full overflow-hidden rounded-xl border bg-brand-navy shadow-card",
        className
      )}
    >
      {showPoster ? (
        <button
          type="button"
          onClick={onOpened}
          className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-brand-navy text-white"
        >
          {videoId && provider === "youtube" ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={youtubeThumbnailSrc(videoId)}
              alt={`${title} video thumbnail`}
              className="absolute inset-0 size-full object-cover opacity-60"
            />
          ) : null}
          <span className="relative z-10 rounded-full bg-brand-orange px-5 py-2.5 text-sm font-semibold">
            Watch lesson
          </span>
          <span className="relative z-10 px-6 text-center text-sm text-white/85">{title}</span>
        </button>
      ) : src ? (
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
