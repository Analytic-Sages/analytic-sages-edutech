"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";

type EmptyStateProps = {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
  className?: string;
};

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed bg-brand-surface/50 px-6 py-16 text-center",
        className
      )}
    >
      <div className="mb-4 flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
        {icon}
      </div>
      <h3 className="font-heading text-lg font-semibold">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">{description}</p>
      {action &&
        (action.href ? (
          <ButtonLink
            href={action.href}
            className="mt-6 bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            {action.label}
          </ButtonLink>
        ) : (
          <Button
            className="mt-6 bg-brand-orange text-white hover:bg-brand-orange/90"
            onClick={action.onClick}
          >
            {action.label}
          </Button>
        ))}
    </div>
  );
}
