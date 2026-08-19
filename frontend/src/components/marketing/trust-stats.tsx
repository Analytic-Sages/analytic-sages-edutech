"use client";

import { motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

type NumericStat = {
  type: "numeric";
  value: number;
  suffix: string;
  label: string;
};

type TextStat = {
  type: "text";
  display: string;
  label: string;
};

type Stat = NumericStat | TextStat;

const stats: Stat[] = [
  { type: "numeric", value: 2000, suffix: "+", label: "Community members" },
  { type: "numeric", value: 18, suffix: "+", label: "Countries represented" },
  { type: "numeric", value: 450, suffix: "+", label: "Blockchain analysts trained" },
  { type: "numeric", value: 8, suffix: "", label: "Successful cohorts" },
  { type: "numeric", value: 92, suffix: "%", label: "Course completion rate" },
  { type: "text", display: "Growing", label: "Research community" },
];

function AnimatedNumericStat({ value, suffix, label }: NumericStat) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const reducedMotion = useReducedMotion();
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    if (reducedMotion) {
      queueMicrotask(() => setDisplay(value));
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

    const handle = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(handle);
  }, [isInView, reducedMotion, value]);

  const formatted =
    suffix === "%"
      ? `${display}${suffix}`
      : suffix
        ? `${display.toLocaleString()}${suffix}`
        : display.toLocaleString();

  return (
    <motion.div
      ref={ref}
      initial={reducedMotion ? false : { opacity: 0, y: 12 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col items-center justify-center bg-brand-surface px-4 py-10 text-center sm:px-6 sm:py-14 md:py-16"
    >
      <p className="font-heading text-3xl font-bold tracking-tight text-brand-navy sm:text-4xl lg:text-5xl dark:text-brand-orange">
        {formatted}
      </p>
      <p className="mt-2 text-sm font-medium text-muted-foreground sm:text-base">{label}</p>
    </motion.div>
  );
}

function TextStatBlock({ display, label }: TextStat) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      ref={ref}
      initial={reducedMotion ? false : { opacity: 0, y: 12 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col items-center justify-center bg-brand-surface px-4 py-10 text-center sm:px-6 sm:py-14 md:py-16"
    >
      <p className="font-heading text-3xl font-bold tracking-tight text-brand-orange sm:text-4xl lg:text-5xl">
        {display}
      </p>
      <p className="mt-2 text-sm font-medium text-muted-foreground sm:text-base">{label}</p>
    </motion.div>
  );
}

export function TrustStats() {
  return (
    <div className="border-y border-border/60 bg-brand-surface">
      <div className="mx-auto grid max-w-screen-2xl grid-cols-2 gap-px bg-border/40 md:grid-cols-3 lg:grid-cols-6">
        {stats.map((stat) =>
          stat.type === "numeric" ? (
            <AnimatedNumericStat key={stat.label} {...stat} />
          ) : (
            <TextStatBlock key={stat.label} {...stat} />
          )
        )}
      </div>
    </div>
  );
}
