"use client";

import { motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

const stats = [
  { value: 4000, suffix: "+", label: "Learners trained" },
  { value: 700, suffix: "+", label: "Community members" },
  { value: 92, suffix: "%", label: "Completion rate" },
  { value: 18, suffix: "+", label: "Countries reached" },
];

function AnimatedStat({
  value,
  suffix,
  label,
}: {
  value: number;
  suffix: string;
  label: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const reducedMotion = useReducedMotion();
  const [display, setDisplay] = useState(reducedMotion ? value : 0);

  useEffect(() => {
    if (!isInView || reducedMotion) {
      setDisplay(value);
      return;
    }

    const duration = 1200;
    const start = performance.now();

    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(value * eased));
      if (progress < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
  }, [isInView, reducedMotion, value]);

  const formatted =
    suffix === "%"
      ? `${display}${suffix}`
      : `${display.toLocaleString()}${suffix}`;

  return (
    <motion.div
      ref={ref}
      initial={reducedMotion ? false : { opacity: 0, y: 12 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col items-center justify-center bg-brand-surface px-6 py-12 text-center sm:px-8 sm:py-16 md:py-20"
    >
      <p className="font-heading text-4xl font-bold tracking-tight text-brand-navy sm:text-5xl">
        {formatted}
      </p>
      <p className="mt-3 text-sm font-medium text-muted-foreground sm:text-base">
        {label}
      </p>
    </motion.div>
  );
}

export function TrustStats() {
  return (
    <div className="border-y border-border/60 bg-brand-surface">
      <div className="mx-auto grid max-w-screen-2xl grid-cols-2 gap-px bg-border/40 md:grid-cols-4">
        {stats.map((stat) => (
          <AnimatedStat key={stat.label} {...stat} />
        ))}
      </div>
    </div>
  );
}
