import { useId } from "react";
import { cn } from "@/lib/utils";

type PatternBackgroundProps = {
  /** Extra classes on the absolute overlay (e.g. opacity tweaks). */
  className?: string;
};

/**
 * Subtle repeating diamond grid for Analytic Sages marketing surfaces.
 * Decorative only: sits behind content. Prefer white/editorial sections.
 */
export function PatternBackground({ className }: PatternBackgroundProps) {
  const uid = useId().replace(/:/g, "");
  const patternId = `as-diamonds-${uid}`;

  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden text-[rgb(15_23_42)] dark:text-white",
        className
      )}
    >
      <svg
        className="absolute inset-0 size-full opacity-[0.9] max-md:opacity-[0.75]"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern
            id={patternId}
            width="58"
            height="58"
            patternUnits="userSpaceOnUse"
          >
            {/* Outlined diamond */}
            <path
              d="M14.5 9.5 L20.5 15.5 L14.5 21.5 L8.5 15.5 Z"
              fill="none"
              stroke="currentColor"
              strokeOpacity="0.05"
              strokeWidth="1"
              strokeLinejoin="miter"
            />
            {/* Filled diamond: offset for subtle variation */}
            <path
              d="M43.5 37.5 L49 43 L43.5 48.5 L38 43 Z"
              fill="currentColor"
              fillOpacity="0.065"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill={`url(#${patternId})`} />
      </svg>
    </div>
  );
}
