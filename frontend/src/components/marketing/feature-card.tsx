"use client";

import Link from "next/link";
import { ArrowRight, type LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { cn } from "@/lib/utils";

type FeatureCardProps = {
  icon: LucideIcon;
  title: string;
  description: string;
  stat: string;
  href?: string;
  className?: string;
};

export function FeatureCard({
  icon: Icon,
  title,
  description,
  stat,
  href = "/courses",
  className,
}: FeatureCardProps) {
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      whileHover={reducedMotion ? undefined : { y: -6 }}
      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "group flex flex-col rounded-2xl border bg-card p-8 shadow-card transition-shadow duration-300 hover:shadow-float",
        className
      )}
    >
      <div className="mb-6 flex size-16 items-center justify-center rounded-2xl bg-brand-navy/10 transition-all duration-300 group-hover:rotate-3 group-hover:bg-brand-navy/15 dark:bg-brand-navy/20">
        <Icon className="size-8 text-brand-navy dark:text-brand-orange" />
      </div>
      <h3 className="font-heading text-2xl font-semibold">{title}</h3>
      <p className="mt-3 flex-1 text-lg leading-relaxed text-muted-foreground">
        {description}
      </p>
      <div className="mt-8 flex items-center justify-between border-t pt-5">
        <span className="text-sm font-medium text-brand-navy dark:text-brand-orange">{stat}</span>
        <Link
          href={href}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-orange transition-transform group-hover:translate-x-1"
        >
          Learn more
          <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </motion.div>
  );
}
