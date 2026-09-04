"use client";

import { useState } from "react";
import { organizationInitials } from "@/lib/opportunities";
import { cn } from "@/lib/utils";

export function OrganizationLogo({
  name,
  logoUrl,
  size = "md",
  className,
}: {
  name: string;
  logoUrl?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const [failed, setFailed] = useState(false);
  const dim = size === "sm" ? "size-9" : size === "lg" ? "size-14" : "size-12";
  const text = size === "sm" ? "text-xs" : size === "lg" ? "text-base" : "text-sm";
  const showImage = Boolean(logoUrl) && !failed;

  return (
    <div
      className={cn(
        "relative flex shrink-0 items-center justify-center overflow-hidden rounded-xl border border-border/80 bg-[#F4F7FB] font-heading font-semibold text-brand-navy",
        dim,
        text,
        className,
      )}
      aria-hidden={showImage ? undefined : true}
    >
      {showImage ? (
        // eslint-disable-next-line @next/next/no-img-element -- logos come from arbitrary employer domains
        <img
          src={logoUrl!}
          alt=""
          className="size-full object-cover"
          onError={() => setFailed(true)}
        />
      ) : (
        <span>{organizationInitials(name)}</span>
      )}
    </div>
  );
}
