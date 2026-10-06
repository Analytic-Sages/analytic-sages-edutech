"use client";

import { useState } from "react";
import { Loader2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError, getSessionRecording, type LiveSessionPublic } from "@/lib/api";
import { cn } from "@/lib/utils";

type Props = {
  session: LiveSessionPublic;
  className?: string;
  label?: string;
};

/**
 * Opens a session's recording. The recording lives in permanent storage and the
 * playback URL is generated on demand by an enrollment-gated API call, so this
 * fetches the signed URL when the student clicks (rather than embedding a raw,
 * expiring provider link in the page).
 */
export function SessionRecordingButton({ session, className, label = "Watch recording" }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function open() {
    setLoading(true);
    setError(null);
    try {
      const playback = await getSessionRecording(session.cohort_id, session.id);
      if (playback.watch_url) {
        window.open(playback.watch_url, "_blank", "noopener,noreferrer");
      } else {
        setError("This recording isn't ready yet. Please try again shortly.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not open the recording.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <Button
        type="button"
        onClick={open}
        disabled={loading}
        className={cn("bg-brand-orange text-white hover:bg-brand-orange/90", className)}
      >
        {loading ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
        {label}
      </Button>
      {error ? <span className="text-xs text-destructive">{error}</span> : null}
    </span>
  );
}