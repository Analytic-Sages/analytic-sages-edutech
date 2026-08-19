import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

/** Transparent brand mark — navy + orange. Use on light backgrounds. */
export const LOGO_SRC = "/logo-colored.png";
/** Transparent white mark — use on dark backgrounds. */
export const LOGO_SRC_DARK = "/logo-white.png";
/** Transparent black mark — monochrome on light backgrounds. */
export const LOGO_SRC_BLACK = "/logo-black.png";

const LOGO_COLORED = { width: 2044, height: 658 };
const LOGO_WHITE = { width: 1974, height: 740 };
const LOGO_BLACK = { width: 1668, height: 805 };

type LogoProps = {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  href?: string | null;
  /** `brand` = colored in light / white in dark. `mono` = black in light / white in dark. */
  tone?: "brand" | "mono";
};

const sizes = {
  sm: { className: "h-7 w-auto max-w-[140px]" },
  md: { className: "h-9 w-auto max-w-[180px]" },
  lg: { className: "h-11 w-auto max-w-[220px]" },
  xl: { className: "h-10 w-auto max-w-[200px] sm:h-12 sm:max-w-[240px]" },
};

export function Logo({ size = "md", className, href = "/", tone = "brand" }: LogoProps) {
  const { className: sizeClass } = sizes[size];
  const light = tone === "mono" ? { src: LOGO_SRC_BLACK, dim: LOGO_BLACK } : { src: LOGO_SRC, dim: LOGO_COLORED };

  const image = (
    <>
      <Image
        src={light.src}
        alt="Analytic Sages"
        width={light.dim.width}
        height={light.dim.height}
        priority
        className={cn(sizeClass, "bg-transparent object-contain dark:hidden", className)}
      />
      <Image
        src={LOGO_SRC_DARK}
        alt="Analytic Sages"
        width={LOGO_WHITE.width}
        height={LOGO_WHITE.height}
        priority
        className={cn(sizeClass, "hidden bg-transparent object-contain dark:block", className)}
      />
    </>
  );

  if (href === null) return image;

  return (
    <Link
      href={href}
      className="inline-flex shrink-0 items-center bg-transparent"
      aria-label="Analytic Sages home"
    >
      {image}
    </Link>
  );
}
