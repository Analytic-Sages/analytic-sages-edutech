import { useId } from "react";
import { cn } from "@/lib/utils";
import { PatternBackground } from "@/components/marketing/pattern-background";

type SectionBackgroundProps = {
  variant?: "glow" | "dots" | "grid" | "lines" | "diamonds" | "none";
  className?: string;
};

export function SectionBackground({
  variant = "none",
  className,
}: SectionBackgroundProps) {
  const uid = useId().replace(/:/g, "");

  if (variant === "none") return null;

  if (variant === "diamonds") {
    return <PatternBackground className={className} />;
  }

  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden text-brand-navy dark:text-white",
        className,
      )}
    >
      {variant === "glow" && (
        <>
          <div className="absolute -top-32 -right-32 size-[32rem] rounded-full bg-brand-orange/[0.04] blur-3xl animate-pulse-glow" />
          <div className="absolute top-1/2 -left-40 size-96 rounded-full bg-brand-navy/[0.03] blur-3xl dark:bg-brand-orange/[0.05]" />
          <div className="absolute bottom-0 right-1/4 size-64 rounded-full bg-brand-orange/[0.03] blur-3xl" />
        </>
      )}
      {variant === "dots" && (
        <div
          className="absolute inset-0 opacity-[0.035] dark:opacity-[0.06]"
          style={{
            backgroundImage: "radial-gradient(circle, currentColor 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />
      )}
      {variant === "grid" && (
        <div
          className="absolute inset-0 opacity-[0.03] dark:opacity-[0.055]"
          style={{
            backgroundImage: `
              linear-gradient(to right, currentColor 1px, transparent 1px),
              linear-gradient(to bottom, currentColor 1px, transparent 1px)
            `,
            backgroundSize: "56px 56px",
          }}
        />
      )}
      {variant === "lines" && (
        <svg
          className="absolute inset-0 size-full opacity-[0.025] dark:opacity-[0.05]"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="none"
        >
          <defs>
            <pattern
              id={`blockchain-lines-${uid}`}
              width="120"
              height="120"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M0 60h40M80 60h40M60 0v40M60 80v40"
                stroke="currentColor"
                strokeWidth="1"
                fill="none"
              />
              <circle cx="60" cy="60" r="3" fill="currentColor" />
              <circle cx="0" cy="60" r="2" fill="#f58220" />
              <circle cx="120" cy="60" r="2" fill="#f58220" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill={`url(#blockchain-lines-${uid})`} />
        </svg>
      )}
    </div>
  );
}
