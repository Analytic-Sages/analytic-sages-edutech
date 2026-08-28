"use client";

import { useState } from "react";
import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { APPLY_SAFETY_POINTS, SAFETY_NOTICE, applyCtaLabel, type OpportunityType } from "@/lib/opportunities";
import { cn } from "@/lib/utils";

type Props = {
  href: string;
  domain?: string | null;
  opportunityType?: OpportunityType;
  label?: string;
  className?: string;
  variant?: "primary" | "text";
};

export function ApplySafetyButton({
  href,
  domain,
  opportunityType = "job",
  label,
  className,
  variant = "primary",
}: Props) {
  const [open, setOpen] = useState(false);
  const cta = label || applyCtaLabel(opportunityType);
  const host = domain || safeHost(href);

  function continueToSource() {
    setOpen(false);
    window.open(href, "_blank", "noopener,noreferrer");
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {variant === "primary" ? (
        <DialogTrigger
          render={
            <Button className={cn("w-full bg-brand-orange text-white hover:bg-brand-orange/90", className)}>
              {cta}
              <ExternalLink className="size-4" />
            </Button>
          }
        />
      ) : (
        <DialogTrigger
          render={
            <button
              type="button"
              className={cn("text-sm text-muted-foreground hover:text-foreground", className)}
            >
              {cta}
            </button>
          }
        />
      )}
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Before you continue</DialogTitle>
          <DialogDescription>
            You are leaving Analytic Sages to visit the original opportunity source.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <p className="rounded-lg border bg-brand-surface px-3 py-2 font-mono text-sm">
            {host || "external site"}
          </p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {APPLY_SAFETY_POINTS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p className="text-xs text-muted-foreground">{SAFETY_NOTICE}</p>
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            type="button"
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
            onClick={continueToSource}
          >
            Continue
            <ExternalLink className="size-4" />
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function safeHost(url: string) {
  try {
    return new URL(url).hostname;
  } catch {
    return null;
  }
}
