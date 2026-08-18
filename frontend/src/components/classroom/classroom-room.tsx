"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  ClipboardList,
  Hand,
  Loader2,
  LogOut,
  MessageSquare,
  Mic,
  MicOff,
  MonitorUp,
  Moon,
  Radio,
  Sun,
  Users,
  Video,
  VideoOff,
} from "lucide-react";
import { useTheme } from "@/components/providers/theme-provider";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import {
  ApiError,
  getClassroomSession,
  joinClassroomSession,
  type ClassroomJoinResponse,
  type LiveSessionPublic,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const RealtimeKitRoom = dynamic(
  () =>
    import("@/components/classroom/realtimekit-room").then((m) => m.RealtimeKitRoom),
  {
    ssr: false,
    loading: () => (
      <div className="flex min-h-[420px] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading live classroom…
      </div>
    ),
  }
);

type PanelTab = "chat" | "resources" | "assignment" | "participants";

function formatCountdown(ms: number) {
  if (ms <= 0) return "00:00:00";
  const total = Math.floor(ms / 1000);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return [h, m, s].map((n) => String(n).padStart(2, "0")).join(":");
}

function formatWhen(iso: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      weekday: "long",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function ClassroomRoom({ sessionId }: { sessionId: string }) {
  const { theme, toggleTheme } = useTheme();
  const [session, setSession] = useState<LiveSessionPublic | null>(null);
  const [join, setJoin] = useState<ClassroomJoinResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inRoom, setInRoom] = useState(false);
  const [panel, setPanel] = useState<PanelTab>("resources");
  const [now, setNow] = useState(() => Date.now());
  const [micOn, setMicOn] = useState(false);
  const [camOn, setCamOn] = useState(false);
  const [handRaised, setHandRaised] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chat, setChat] = useState<Array<{ id: string; author: string; body: string }>>([
    {
      id: "1",
      author: "Instructor",
      body: "Welcome. Drop questions in chat; we'll cover JOINs after the demo.",
    },
  ]);

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getClassroomSession(sessionId);
        if (!cancelled) setSession(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load session");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const countdownMs = useMemo(() => {
    if (!session) return 0;
    return new Date(session.starts_at).getTime() - now;
  }, [session, now]);

  async function handleJoin() {
    setJoining(true);
    setError(null);
    try {
      const result = await joinClassroomSession(sessionId);
      setJoin(result);
      if (result.phase === "live") {
        setInRoom(true);
        setPanel("chat");
      } else {
        setError(result.message || "Class is not joinable yet");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to join class");
    } finally {
      setJoining(false);
    }
  }

  function sendChat() {
    const body = chatInput.trim();
    if (!body) return;
    setChat((prev) => [
      ...prev,
      { id: String(Date.now()), author: join?.display_name || "You", body },
    ]);
    setChatInput("");
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center gap-2 bg-background text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Opening classroom…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-4 text-center">
        <p className="text-muted-foreground">{error || "Session not found"}</p>
        <ButtonLink href="/classroom">Back to schedule</ButtonLink>
      </div>
    );
  }

  const phase = join?.phase ?? session.phase;
  const useLiveKit = inRoom && join?.mode === "live" && Boolean(join.auth_token);
  const useMockRoom = inRoom && join?.mode === "mock";

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="flex items-center justify-between gap-4 border-b bg-card px-4 py-3 sm:px-6">
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold uppercase tracking-[0.14em] text-brand-orange">
            Analytic Sages
          </p>
          <h1 className="truncate font-heading text-lg font-semibold sm:text-xl">{session.title}</h1>
          <p className="truncate text-xs text-muted-foreground">
            {session.cohort_name}
            {session.week_label ? ` · ${session.week_label}` : ""}
            {` · Session ${session.session_number}`}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {phase === "live" && (
            <span className="inline-flex items-center gap-1.5 rounded-md bg-red-500/15 px-2.5 py-1 text-xs font-bold uppercase tracking-wide text-red-600 dark:text-red-300">
              <span className="size-1.5 animate-pulse rounded-full bg-red-500" />
              Live
            </span>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            title={theme === "dark" ? "Light mode" : "Dark mode"}
          >
            {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
          <ButtonLink href="/classroom" variant="ghost" size="sm">
            <LogOut className="size-4" />
            Leave
          </ButtonLink>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-screen-2xl flex-1 flex-col gap-4 p-4 sm:p-6 lg:flex-row">
        <main className="flex min-h-0 flex-1 flex-col gap-4">
          {!inRoom && phase === "upcoming" && (
            <UpcomingState
              session={session}
              countdown={formatCountdown(countdownMs)}
              onJoinEarly={session.can_join ? handleJoin : undefined}
              joining={joining}
              error={error}
            />
          )}

          {!inRoom && phase === "ended" && <EndedState session={session} />}
          {!inRoom && phase === "cancelled" && (
            <div className="flex flex-1 flex-col items-center justify-center rounded-xl border bg-card p-10 text-center shadow-card">
              <p className="font-heading text-2xl font-semibold">Class cancelled</p>
              <p className="mt-2 max-w-md text-muted-foreground">
                This session was cancelled. Check your schedule for the next class.
              </p>
              <ButtonLink href="/classroom" className="mt-6 bg-brand-orange text-white">
                Back to schedule
              </ButtonLink>
            </div>
          )}

          {!inRoom && phase === "live" && (
            <div className="flex flex-1 flex-col items-center justify-center rounded-xl border bg-gradient-to-b from-brand-navy/10 to-card p-10 text-center shadow-card dark:from-brand-navy/40 dark:to-background">
              <Radio className="mb-4 size-10 text-brand-orange" />
              <p className="font-heading text-3xl font-semibold">Class is live</p>
              <p className="mt-2 max-w-lg text-muted-foreground">
                {session.course_title || session.cohort_name}. Join to enter the Analytic Sages
                live classroom.
              </p>
              {error && <p className="mt-4 text-sm text-red-600 dark:text-red-300">{error}</p>}
              <Button
                onClick={handleJoin}
                disabled={joining}
                className="mt-8 bg-brand-orange text-white hover:bg-brand-orange/90"
              >
                {joining ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    Joining…
                  </>
                ) : (
                  "Join live class"
                )}
              </Button>
            </div>
          )}

          {useLiveKit && join?.auth_token && (
            <div className="min-h-[520px] flex-1 overflow-hidden rounded-xl border">
              <RealtimeKitRoom
                authToken={join.auth_token}
                theme={theme}
                onLeft={() => setInRoom(false)}
              />
            </div>
          )}

          {useMockRoom && (
            <MockStage
              micOn={micOn}
              camOn={camOn}
              handRaised={handRaised}
              onToggleMic={() => setMicOn((v) => !v)}
              onToggleCam={() => setCamOn((v) => !v)}
              onToggleHand={() => setHandRaised((v) => !v)}
              displayName={join?.display_name || "You"}
            />
          )}

          {inRoom && join?.mode === "mock" && (
            <p className="text-center text-xs text-muted-foreground">
              Preview mode: live video connects when classroom media is fully configured.
            </p>
          )}
        </main>

        <aside className="flex w-full shrink-0 flex-col overflow-hidden rounded-xl border bg-card lg:w-[400px] xl:w-[440px]">
          <div className="grid grid-cols-2 gap-1 border-b p-2 sm:grid-cols-4 sm:gap-1.5 sm:p-2.5">
            {(
              [
                ["resources", "Resources", BookOpen],
                ["chat", "Chat", MessageSquare],
                ["assignment", "Assignment", ClipboardList],
                ["participants", "Participants", Users],
              ] as const
            ).map(([id, label, Icon]) => (
              <button
                key={id}
                type="button"
                onClick={() => setPanel(id)}
                className={cn(
                  "flex min-h-14 flex-col items-center justify-center gap-1.5 rounded-lg px-2 py-2.5 text-center text-xs font-semibold transition-colors sm:min-h-16 sm:text-[13px]",
                  panel === id
                    ? "bg-brand-navy text-white shadow-sm dark:bg-brand-orange"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="size-4 shrink-0 sm:size-[18px]" />
                <span className="leading-tight">{label}</span>
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-5 text-sm sm:p-6">
            {panel === "resources" && (
              <div className="space-y-4">
                <div>
                  <h3 className="font-heading font-semibold">Today&apos;s objectives</h3>
                  {session.objectives.length === 0 ? (
                    <p className="mt-2 text-muted-foreground">Objectives will appear here.</p>
                  ) : (
                    <ul className="mt-2 list-disc space-y-1 pl-4 text-foreground/90">
                      {session.objectives.map((o) => (
                        <li key={o}>{o}</li>
                      ))}
                    </ul>
                  )}
                </div>
                <div>
                  <h3 className="font-heading font-semibold">Session resources</h3>
                  {session.resources.length === 0 ? (
                    <p className="mt-2 text-muted-foreground">No resources linked yet.</p>
                  ) : (
                    <ul className="mt-2 space-y-2">
                      {session.resources.map((r) => (
                        <li key={`${r.title}-${r.url}`}>
                          <a
                            href={r.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-brand-orange hover:underline"
                          >
                            {r.title}
                          </a>
                          <span className="ml-2 text-xs uppercase text-muted-foreground">
                            {r.kind}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            )}

            {panel === "chat" && (
              <div className="flex h-full min-h-[280px] flex-col">
                <div className="flex-1 space-y-3">
                  {chat.map((m) => (
                    <div key={m.id}>
                      <p className="text-xs font-semibold text-brand-orange">{m.author}</p>
                      <p className="text-foreground/90">{m.body}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex gap-2">
                  <input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendChat()}
                    placeholder="Type a message…"
                    className="flex-1 rounded-md border bg-background px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus:border-brand-orange"
                  />
                  <Button
                    type="button"
                    size="sm"
                    onClick={sendChat}
                    className="bg-brand-orange text-white hover:bg-brand-orange/90"
                  >
                    Send
                  </Button>
                </div>
                {join?.mode === "live" && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    Class chat also appears in the live session controls.
                  </p>
                )}
              </div>
            )}

            {panel === "assignment" && (
              <div>
                <h3 className="font-heading font-semibold">Your assignment</h3>
                {session.assignment_summary ? (
                  <p className="mt-2 whitespace-pre-wrap text-foreground/90">
                    {session.assignment_summary}
                  </p>
                ) : (
                  <p className="mt-2 text-muted-foreground">
                    No assignment published for this session yet.
                  </p>
                )}
              </div>
            )}

            {panel === "participants" && (
              <div className="space-y-2">
                <p className="text-muted-foreground">Instructor</p>
                <p className="rounded-md bg-muted px-3 py-2">Lead Instructor</p>
                <p className="mt-4 text-muted-foreground">You</p>
                <p className="rounded-md bg-muted px-3 py-2">
                  {join?.display_name || "Student"}
                  {session.member_role ? ` · ${session.member_role}` : ""}
                </p>
                <p className="mt-4 text-xs text-muted-foreground">
                  The full participant list updates as people join the live session.
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

function UpcomingState({
  session,
  countdown,
  onJoinEarly,
  joining,
  error,
}: {
  session: LiveSessionPublic;
  countdown: string;
  onJoinEarly?: () => void;
  joining: boolean;
  error: string | null;
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center rounded-xl border bg-gradient-to-b from-brand-navy/10 to-card p-10 text-center shadow-card dark:from-brand-navy/50 dark:to-background">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-brand-orange">
        Class starts in
      </p>
      <p className="mt-3 font-heading text-5xl font-bold tracking-tight tabular-nums sm:text-6xl">
        {countdown}
      </p>
      <p className="mt-6 text-lg text-foreground/90">Today&apos;s topic: {session.title}</p>
      <p className="mt-1 text-sm text-muted-foreground">{formatWhen(session.starts_at)}</p>
      {error && <p className="mt-4 text-sm text-red-600 dark:text-red-300">{error}</p>}
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {onJoinEarly && (
          <Button
            onClick={onJoinEarly}
            disabled={joining}
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            {joining ? "Joining…" : "Enter classroom"}
          </Button>
        )}
        <ButtonLink href="/classroom" variant="outline">
          View schedule
        </ButtonLink>
      </div>
    </div>
  );
}

function EndedState({ session }: { session: LiveSessionPublic }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center rounded-xl border bg-card p-10 text-center shadow-card">
      <p className="font-heading text-3xl font-semibold">Class completed</p>
      <p className="mt-2 max-w-md text-muted-foreground">
        Attendance is being recorded. Check back later if a session recording becomes available.
      </p>
      {session.recording_url ? (
        <a
          href={session.recording_url}
          className="mt-6 inline-flex rounded-md bg-brand-orange px-4 py-2 text-sm font-medium text-white"
          target="_blank"
          rel="noreferrer"
        >
          Watch recording
        </a>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">Recording processing…</p>
      )}
      {session.assignment_summary && (
        <p className="mt-6 max-w-lg text-sm text-foreground/80">{session.assignment_summary}</p>
      )}
      <ButtonLink href="/classroom" className="mt-8 bg-brand-navy text-white">
        Continue learning
      </ButtonLink>
    </div>
  );
}

function MockStage({
  micOn,
  camOn,
  handRaised,
  onToggleMic,
  onToggleCam,
  onToggleHand,
  displayName,
}: {
  micOn: boolean;
  camOn: boolean;
  handRaised: boolean;
  onToggleMic: () => void;
  onToggleCam: () => void;
  onToggleHand: () => void;
  displayName: string;
}) {
  return (
    <div className="flex flex-1 flex-col overflow-hidden rounded-xl border bg-card">
      <div className="relative flex min-h-[360px] flex-1 items-center justify-center bg-gradient-to-br from-brand-navy/80 to-brand-navy text-white">
        <div className="text-center">
          <Video className="mx-auto mb-3 size-12 text-white/40" />
          <p className="font-heading text-xl font-semibold">Instructor / Screen</p>
          <p className="mt-1 text-sm text-white/70">Classroom preview · {displayName}</p>
        </div>
        {handRaised && (
          <span className="absolute right-4 top-4 rounded-md bg-brand-orange px-2 py-1 text-xs font-bold text-white">
            Hand raised
          </span>
        )}
      </div>
      <div className="flex flex-wrap items-center justify-center gap-2 border-t bg-muted/40 px-4 py-3">
        <ControlBtn active={micOn} onClick={onToggleMic} label={micOn ? "Mute" : "Unmute"}>
          {micOn ? <Mic className="size-4" /> : <MicOff className="size-4" />}
        </ControlBtn>
        <ControlBtn active={camOn} onClick={onToggleCam} label={camOn ? "Stop video" : "Start video"}>
          {camOn ? <Video className="size-4" /> : <VideoOff className="size-4" />}
        </ControlBtn>
        <ControlBtn active={false} onClick={() => undefined} label="Share">
          <MonitorUp className="size-4" />
        </ControlBtn>
        <ControlBtn active={handRaised} onClick={onToggleHand} label="Raise hand">
          <Hand className="size-4" />
        </ControlBtn>
      </div>
    </div>
  );
}

function ControlBtn({
  children,
  onClick,
  active,
  label,
}: {
  children: React.ReactNode;
  onClick: () => void;
  active: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      title={label}
      onClick={onClick}
      className={cn(
        "inline-flex size-10 items-center justify-center rounded-full border transition-colors",
        active
          ? "border-brand-orange bg-brand-orange text-white"
          : "border-border bg-background text-foreground hover:bg-muted"
      )}
    >
      {children}
    </button>
  );
}
