"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Award,
  BookOpen,
  CheckCircle2,
  Circle,
  FolderKanban,
  MessageSquare,
  Route,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { cn } from "@/lib/utils";

const STATE_DURATION_MS = 4500;
const EXIT_MS = 260;

type ShowcaseState = {
  id: string;
  label: string;
  icon: typeof BookOpen;
};

const states: ShowcaseState[] = [
  { id: "learning", label: "Continue Learning", icon: BookOpen },
  { id: "path", label: "Learning Path", icon: Route },
  { id: "project", label: "Projects", icon: FolderKanban },
  { id: "qa", label: "Lesson Q&A", icon: MessageSquare },
  { id: "certificate", label: "Certificate", icon: Award },
];

const pathSteps = [
  { name: "SQL", status: "done" },
  { name: "Python", status: "done" },
  { name: "Dune", status: "current" },
  { name: "Blockchain APIs", status: "upcoming" },
  { name: "RPCs", status: "upcoming" },
  { name: "Capstone Project", status: "upcoming" },
] as const;

const projectSteps = [
  { name: "Data collection", done: true },
  { name: "SQL analytics", done: true },
  { name: "Dashboard", done: false },
] as const;

function StateHeader({ icon: Icon, label }: { icon: typeof BookOpen; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="flex size-7 items-center justify-center rounded-lg bg-brand-navy/10 text-brand-navy dark:bg-brand-orange/10 dark:text-brand-orange">
        <Icon className="size-4" />
      </span>
      <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
    </div>
  );
}

function ContinueLearningState() {
  return (
    <div>
      <StateHeader icon={BookOpen} label="My Learning" />
      <div className="mt-4 flex items-center gap-4">
        <div className="relative aspect-video w-28 shrink-0 overflow-hidden rounded-lg border">
          <Image
            src="/python-for-blockchain-analytics.png"
            alt="Python for Blockchain Data Analytics course postcard"
            fill
            className="object-cover"
            sizes="112px"
          />
        </div>
        <div className="min-w-0">
          <h3 className="font-heading text-lg font-bold leading-snug">
            Python for Blockchain Data Analytics
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">8 weeks · Beginner</p>
        </div>
      </div>
      <div className="mt-5 space-y-1.5">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Course progress</span>
          <span className="font-semibold">68%</span>
        </div>
        <Progress value={68} className="h-2" />
      </div>
      <div className="mt-5 flex items-center justify-between gap-4 rounded-xl border bg-brand-surface/60 p-3.5">
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">Continue</p>
          <p className="truncate text-sm font-medium">Reading Etherscan with Python</p>
        </div>
        <span className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-brand-orange">
          Resume Lesson
          <ArrowRight className="size-3.5" />
        </span>
      </div>
    </div>
  );
}

function LearningPathState() {
  return (
    <div>
      <StateHeader icon={Route} label="Learning Path" />
      <h3 className="mt-4 font-heading text-lg font-bold">Blockchain Analytics</h3>
      <ul className="mt-4 space-y-2.5">
        {pathSteps.map((step) => (
          <li key={step.name} className="flex items-center gap-2.5 text-sm">
            {step.status === "done" && (
              <CheckCircle2 className="size-4 shrink-0 text-success" />
            )}
            {step.status === "current" && (
              <ArrowRight className="size-4 shrink-0 text-brand-orange" />
            )}
            {step.status === "upcoming" && (
              <Circle className="size-4 shrink-0 text-muted-foreground/40" />
            )}
            <span
              className={cn(
                step.status === "current" && "font-semibold text-brand-orange",
                step.status === "upcoming" && "text-muted-foreground"
              )}
            >
              {step.name}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-4 border-t pt-3 text-sm text-muted-foreground">
        <span className="font-semibold text-foreground">2 / 6</span> completed
      </p>
    </div>
  );
}

function ProjectState() {
  return (
    <div>
      <StateHeader icon={FolderKanban} label="Your Projects" />
      <h3 className="mt-4 font-heading text-lg font-bold">DeFi Analytics Dashboard</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Capstone · Python for Blockchain Data Analytics
      </p>
      <ul className="mt-4 space-y-2.5">
        {projectSteps.map((step) => (
          <li key={step.name} className="flex items-center gap-2.5 text-sm">
            {step.done ? (
              <CheckCircle2 className="size-4 shrink-0 text-success" />
            ) : (
              <Circle className="size-4 shrink-0 text-brand-orange" />
            )}
            <span className={cn(!step.done && "font-medium")}>{step.name}</span>
            {!step.done && (
              <span className="rounded-full bg-brand-orange/10 px-2 py-0.5 text-[0.68rem] font-semibold text-brand-orange">
                In progress
              </span>
            )}
          </li>
        ))}
      </ul>
      <p className="mt-5 inline-flex items-center gap-1 text-sm font-semibold text-brand-navy dark:text-brand-orange">
        View Project
        <ArrowRight className="size-3.5" />
      </p>
    </div>
  );
}

function CommunityQaState() {
  return (
    <div>
      <StateHeader icon={MessageSquare} label="Lesson Q&A" />
      <div className="mt-4 space-y-3">
        <div className="flex items-start gap-2.5">
          <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-surface text-[0.65rem] font-semibold">
            TJ
          </span>
          <div className="rounded-xl rounded-tl-sm border bg-brand-surface/60 px-3.5 py-2.5">
            <p className="text-sm">Why does this query group swaps by day instead of block?</p>
          </div>
        </div>
        <div className="flex items-start gap-2.5">
          <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-navy text-[0.65rem] font-semibold text-white">
            AO
          </span>
          <div className="rounded-xl rounded-tl-sm border border-brand-navy/15 bg-brand-navy/5 px-3.5 py-2.5">
            <p className="text-xs font-semibold text-brand-navy dark:text-brand-orange">
              Instructor
            </p>
            <p className="mt-1 text-sm">
              Daily buckets smooth out block-level noise, so trends are easier to read on a
              dashboard.
            </p>
          </div>
        </div>
      </div>
      <p className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-brand-navy dark:text-brand-orange">
        Ask the community
        <ArrowRight className="size-3.5" />
      </p>
    </div>
  );
}

function CertificateState() {
  return (
    <div className="flex h-full flex-col items-center justify-center py-2 text-center">
      <span className="flex size-14 items-center justify-center rounded-2xl bg-brand-navy/10 text-brand-navy dark:bg-brand-orange/10 dark:text-brand-orange">
        <Award className="size-7" />
      </span>
      <p className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-success/10 px-3 py-1 text-xs font-semibold text-success">
        <CheckCircle2 className="size-3.5" />
        Verified Certificate
      </p>
      <h3 className="mt-3 font-heading text-xl font-bold">SQL for Blockchain Analytics</h3>
      <p className="mt-1 text-sm text-muted-foreground">Issued by Analytic Sages</p>
      <p className="mt-5 text-xs font-mono text-muted-foreground">
        Credential ID · AS-SQL-2841
      </p>
    </div>
  );
}

const stateComponents = [
  ContinueLearningState,
  LearningPathState,
  ProjectState,
  CommunityQaState,
  CertificateState,
];

export function HeroVisual() {
  const reducedMotion = useReducedMotion();
  const [index, setIndex] = useState(0);
  const [phase, setPhase] = useState<"in" | "out" | "pre">("in");
  const [paused, setPaused] = useState(false);
  const transitioning = useRef(false);

  const goTo = useCallback(
    (next: number) => {
      if (next === index || transitioning.current) return;
      if (reducedMotion) {
        setIndex(next);
        return;
      }
      transitioning.current = true;
      setPhase("out");
      setTimeout(() => {
        setIndex(next);
        setPhase("pre");
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            setPhase("in");
            transitioning.current = false;
          });
        });
      }, EXIT_MS);
    },
    [index, reducedMotion]
  );

  useEffect(() => {
    if (reducedMotion || paused) return;
    const timer = setInterval(() => {
      goTo((index + 1) % states.length);
    }, STATE_DURATION_MS);
    return () => clearInterval(timer);
  }, [index, paused, reducedMotion, goTo]);

  const CurrentState = stateComponents[index];

  return (
    <div
      className="relative mx-auto w-full max-w-lg lg:max-w-xl"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={() => setPaused(false)}
      aria-label="Analytic Sages learning experience preview"
    >
      {/* Supporting card: continue learning strip (desktop only) */}
      <div className="absolute -top-8 left-4 z-20 hidden w-64 items-center gap-3 rounded-2xl border bg-card px-4 py-3 shadow-card sm:flex">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-orange/10 text-brand-orange">
          <BookOpen className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-semibold">Python for Blockchain Analytics</p>
          <Progress value={68} className="mt-1.5 h-1" />
        </div>
        <span className="text-xs font-bold text-brand-navy dark:text-brand-orange">68%</span>
      </div>

      {/* Supporting card: certificate chip (desktop only) */}
      <div className="absolute -bottom-7 right-4 z-20 hidden items-center gap-2.5 rounded-2xl border bg-card px-4 py-3 shadow-card sm:flex">
        <span className="flex size-8 items-center justify-center rounded-lg bg-success/10 text-success">
          <CheckCircle2 className="size-4" />
        </span>
        <div>
          <p className="text-xs font-semibold">Certificate verified</p>
          <p className="text-[0.68rem] text-muted-foreground">SQL for Blockchain Analytics</p>
        </div>
      </div>

      {/* Main product card */}
      <div className="relative z-10 rounded-3xl border bg-card p-6 shadow-elevated sm:p-7">
        <div
          className={cn(
            "min-h-[300px]",
            phase === "in" &&
              "translate-y-0 scale-100 opacity-100 transition-all duration-500 ease-out",
            phase === "out" &&
              "-translate-y-2 scale-[0.98] opacity-0 transition-all duration-300 ease-in",
            phase === "pre" && "translate-y-2 scale-[0.98] opacity-0 transition-none"
          )}
        >
          <CurrentState />
        </div>

        {/* State indicators */}
        <div
          className="mt-5 flex items-center justify-center gap-2 border-t pt-4"
          role="tablist"
          aria-label="Learning experience previews"
        >
          {states.map((state, i) => (
            <button
              key={state.id}
              type="button"
              role="tab"
              aria-selected={i === index}
              aria-label={`Show ${state.label}`}
              onClick={() => goTo(i)}
              className={cn(
                "h-1.5 rounded-full transition-all duration-300",
                i === index
                  ? "w-6 bg-brand-orange"
                  : "w-1.5 bg-muted-foreground/25 hover:bg-muted-foreground/50"
              )}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
