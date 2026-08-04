import { cn } from "@/lib/utils";

type SectionBackgroundProps = {
  variant?: "glow" | "dots" | "grid" | "lines" | "none";
  className?: string;
};

export function SectionBackground({
  variant = "none",
  className,
}: SectionBackgroundProps) {
  if (variant === "none") return null;

  return (
    <div
      aria-hidden
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
    >
      {variant === "glow" && (
        <>
          <div className="absolute -top-32 -right-32 size-[32rem] rounded-full bg-brand-orange/[0.04] blur-3xl animate-pulse-glow" />
          <div className="absolute top-1/2 -left-40 size-96 rounded-full bg-brand-navy/[0.03] blur-3xl" />
          <div className="absolute bottom-0 right-1/4 size-64 rounded-full bg-brand-orange/[0.03] blur-3xl" />
        </>
      )}
      {variant === "dots" && (
        <div
          className="absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage:
              "radial-gradient(circle, #101a8a 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />
      )}
      {variant === "grid" && (
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `
              linear-gradient(to right, #101a8a 1px, transparent 1px),
              linear-gradient(to bottom, #101a8a 1px, transparent 1px)
            `,
            backgroundSize: "56px 56px",
          }}
        />
      )}
      {variant === "lines" && (
        <svg
          className="absolute inset-0 size-full opacity-[0.025]"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="none"
        >
          <defs>
            <pattern id="blockchain-lines" width="120" height="120" patternUnits="userSpaceOnUse">
              <path
                d="M0 60h40M80 60h40M60 0v40M60 80v40"
                stroke="#101a8a"
                strokeWidth="1"
                fill="none"
              />
              <circle cx="60" cy="60" r="3" fill="#101a8a" />
              <circle cx="0" cy="60" r="2" fill="#f58220" />
              <circle cx="120" cy="60" r="2" fill="#f58220" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#blockchain-lines)" />
        </svg>
      )}
    </div>
  );
}
