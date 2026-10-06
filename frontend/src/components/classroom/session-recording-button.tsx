"use client";

import { useState } from "react";
import { Loader2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ApiError, getSessionRecording, type LiveSessionPublic } from "@/lib/api";
import { cn } from "@/lib/utils";

type Props = {
  session: LiveSessionPublic;
  className?: string;
  label?: string;
};

function isEmbeddedPlayer(url: string) {
  try {
    const parsed = new URL(url);
    return (
      parsed.hostname.endsWith("cloudflarestream.com") ||
      parsed.pathname.endsWith("/iframe")
    );
  } catch {
    return false;
  }
}

/**
 * Plays a session recording inside Analytic Sages. The enrollment-gated API
 * returns a short-lived file address, which is used only as the player source.
 */
export function SessionRecordingButton({ session, className, label = "Watch recording" }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);

  async function openPlayer() {
    setLoading(true);
    setError(null);
    try {
      const playback = await getSessionRecording(session.cohort_id, session.id);
      if (!playback.watch_url) {
        setError("This recording isn't ready yet. Please try again shortly.");
        return;
      }
      setMediaUrl(playback.watch_url);
      setOpen(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not open the recording.");
    } finally {
      setLoading(false);
    }
  }

  function onOpenChange(next: boolean) {
    setOpen(next);
    if (!next) setMediaUrl(null);
  }

  const subtitle = [session.course_title, session.week_label].filter(Boolean).join(" · ");

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <Button
        type="button"
        onClick={openPlayer}
        disabled={loading}
        className={cn("bg-brand-orange text-white hover:bg-brand-orange/90", className)}
      >
        {loading ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
        {label}
      </Button>
      {error ? <span className="text-xs text-destructive">{error}</span> : null}
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="gap-0 overflow-hidden bg-brand-navy p-0 text-white sm:max-w-4xl [&_[data-slot=dialog-close]]:text-white [&_[data-slot=dialog-close]]:hover:bg-white/10">
          <DialogHeader className="gap-1 px-5 py-4 pr-12 text-left">
            <p className="text-[11px] font-medium tracking-[0.14em] text-white/70 uppercase">
              Analytic Sages
            </p>
            <DialogTitle className="text-lg text-white">{session.title}</DialogTitle>
            {subtitle ? (
              <DialogDescription className="text-white/70">{subtitle}</DialogDescription>
            ) : (
              <DialogDescription className="sr-only">Session recording</DialogDescription>
            )}
          </DialogHeader>
          <div className="bg-black">
            {mediaUrl && isEmbeddedPlayer(mediaUrl) ? (
              <iframe
                src={mediaUrl}
                title={session.title}
                className="aspect-video w-full"
                allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture"
                allowFullScreen
              />
            ) : mediaUrl ? (
              <video
                key={mediaUrl}
                src={mediaUrl}
                controls
                autoPlay
                playsInline
                className="aspect-video w-full"
                controlsList="nodownload"
              >
                Your browser cannot play this recording.
              </video>
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
    </span>
  );
}
