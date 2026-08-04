import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { VariantProps } from "class-variance-authority";

type ButtonAnchorProps = React.ComponentProps<"a"> &
  VariantProps<typeof buttonVariants> & {
    className?: string;
  };

export function ButtonAnchor({
  className,
  variant,
  size,
  children,
  ...props
}: ButtonAnchorProps) {
  return (
    <a {...props} className={cn(buttonVariants({ variant, size, className }))}>
      {children}
    </a>
  );
}
