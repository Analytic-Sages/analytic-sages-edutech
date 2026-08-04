import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

export const LOGO_SRC = "/Analytic-Sages.PNG";
export const LOGO_SRC_DARK = "/Analytic-Sages_white.png";

const LOGO_LIGHT = { width: 2028, height: 573 };
const LOGO_DARK = { width: 2171, height: 724 };

type LogoProps = {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  href?: string | null;
};

const sizes = {
  sm: { className: "h-7 w-auto max-w-[140px]" },
  md: { className: "h-9 w-auto max-w-[180px]" },
  lg: { className: "h-11 w-auto max-w-[220px]" },
  xl: { className: "h-10 w-auto max-w-[200px] sm:h-12 sm:max-w-[240px]" },
};

export function Logo({ size = "md", className, href = "/" }: LogoProps) {
  const { className: sizeClass } = sizes[size];

  const image = (
    <>
      <Image
        src={LOGO_SRC}
        alt="Analytic Sages"
        width={LOGO_LIGHT.width}
        height={LOGO_LIGHT.height}
        priority
        className={cn(sizeClass, "dark:hidden", className)}
      />
      <Image
        src={LOGO_SRC_DARK}
        alt="Analytic Sages"
        width={LOGO_DARK.width}
        height={LOGO_DARK.height}
        priority
        className={cn(sizeClass, "hidden dark:block", className)}
      />
    </>
  );

  if (href === null) return image;

  return (
    <Link
      href={href}
      className="inline-flex shrink-0 items-center"
      aria-label="Analytic Sages home"
    >
      {image}
    </Link>
  );
}
