"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { provideRtkDesignSystem, RtkMeeting } from "@cloudflare/realtimekit-react-ui";
import { useRealtimeKitClient } from "@cloudflare/realtimekit-react";

type Props = {
  authToken: string;
  theme?: "light" | "dark";
  onLeft?: () => void;
};

const BRAND = {
  300: "#FDBA74",
  400: "#FB923C",
  500: "#F58220",
  600: "#EA580C",
  700: "#C2410C",
} as const;

/**
 * Live RealtimeKit meeting surface.
 * Init once per token; let RtkMeeting own join (avoids concurrent meeting.join).
 */
export function RealtimeKitRoom({ authToken, theme = "light", onLeft }: Props) {
  const [meeting, initMeeting] = useRealtimeKitClient();
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const initTokenRef = useRef<string | null>(null);
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!authToken) return;
    if (initTokenRef.current === authToken && meeting) {
      setReady(true);
      return;
    }

    let active = true;
    initTokenRef.current = authToken;

    async function boot() {
      try {
        setError(null);
        setReady(false);
        await initMeeting({
          authToken,
          defaults: { audio: false, video: false },
        });
        if (active) setReady(true);
      } catch (err) {
        if (active) {
          initTokenRef.current = null;
          setError(err instanceof Error ? err.message : "Failed to connect to the live classroom");
          setReady(false);
        }
      }
    }

    boot();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- init once per token
  }, [authToken]);

  useEffect(() => {
    const el = hostRef.current;
    if (!el || !ready) return;
    provideRtkDesignSystem(el, {
      theme: theme === "dark" ? "dark" : "light",
      borderRadius: "rounded",
      colors: {
        brand: { ...BRAND },
        text: theme === "dark" ? "#F8FAFC" : "#0F172A",
        "text-on-brand": "#FFFFFF",
        "video-bg": theme === "dark" ? "#0B1220" : "#E2E8F0",
        danger: "#EF4444",
        success: "#16A34A",
        warning: "#F59E0B",
      },
    });
  }, [theme, ready, meeting]);

  useEffect(() => {
    if (!meeting?.self) return;
    const self = meeting.self as {
      on?: (e: string, cb: () => void) => void;
      off?: (e: string, cb: () => void) => void;
    };
    const onRoomLeft = () => onLeft?.();
    self.on?.("roomLeft", onRoomLeft);
    return () => {
      self.off?.("roomLeft", onRoomLeft);
    };
  }, [meeting, onLeft]);

  if (error) {
    return (
      <div className="flex h-full min-h-[420px] items-center justify-center p-8 text-center text-sm text-red-600">
        {error}
      </div>
    );
  }

  if (!ready || !meeting) {
    return (
      <div className="flex h-full min-h-[420px] flex-col items-center justify-center gap-3 text-muted-foreground">
        <Loader2 className="size-6 animate-spin" />
        <p className="text-sm">Connecting to live class…</p>
      </div>
    );
  }

  return (
    <div
      ref={hostRef}
      className={cnRoom(theme)}
    >
      {/* Setup screen performs a single join — do not call meeting.join() yourself. */}
      <RtkMeeting meeting={meeting} showSetupScreen applyDesignSystem />
    </div>
  );
}

function cnRoom(theme: "light" | "dark") {
  return theme === "dark"
    ? "h-full min-h-[420px] w-full overflow-hidden rounded-lg bg-[#0b1220]"
    : "h-full min-h-[420px] w-full overflow-hidden rounded-lg bg-slate-100";
}
