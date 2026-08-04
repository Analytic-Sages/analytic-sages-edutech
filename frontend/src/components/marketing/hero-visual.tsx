"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import {
  Award,
  ArrowRight,
  BookOpen,
  Clock,
  LayoutDashboard,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { courses } from "@/lib/mock-data";

const enrolledCourse = courses.find((c) => c.enrolled) ?? courses[2];
const featuredCourse =
  courses.find((c) => c.slug === "applied-ai-for-blockchain") ?? courses[0];

const floatTransition = {
  duration: 5,
  repeat: Infinity,
  ease: "easeInOut" as const,
};

export function HeroVisual() {
  const reducedMotion = useReducedMotion();

  const float = (delay: number) =>
    reducedMotion
      ? {}
      : { animate: { y: [0, -8, 0] }, transition: { ...floatTransition, delay } };

  return (
    <div className="relative mx-auto flex w-full max-w-md flex-col items-center lg:max-w-lg xl:max-w-xl">
      {/* 1. Continue Learning — compact entry point */}
      <motion.div
        {...float(0)}
        whileHover={reducedMotion ? undefined : { y: -4, scale: 1.01 }}
        className="relative z-40 w-[88%] rotate-[-2deg] rounded-2xl border bg-card/95 p-4 shadow-elevated backdrop-blur-sm"
      >
        <div className="flex items-center gap-3">
          <div className="relative size-11 shrink-0 overflow-hidden rounded-lg">
            <Image
              src={enrolledCourse.thumbnail}
              alt=""
              fill
              className="object-cover"
              sizes="44px"
            />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium uppercase tracking-wide text-brand-orange">
              Continue learning
            </p>
            <p className="truncate text-sm font-semibold">{enrolledCourse.title}</p>
          </div>
          <span className="font-heading text-lg font-bold text-brand-navy">
            {enrolledCourse.progress}%
          </span>
        </div>
      </motion.div>

      {/* 2. Course Preview — hero focal point (largest) */}
      <motion.div
        {...float(0.6)}
        whileHover={reducedMotion ? undefined : { y: -6, scale: 1.015 }}
        className="relative z-30 -mt-4 w-full rotate-[0.5deg] rounded-2xl border bg-card p-5 shadow-float sm:p-6"
      >
        <div className="mb-3 flex items-center justify-between gap-2">
          <Badge className="bg-brand-orange/10 text-brand-orange">Course preview</Badge>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="size-3" />
            {featuredCourse.duration}
          </span>
        </div>
        <p className="font-heading text-lg font-semibold leading-snug sm:text-xl">
          {featuredCourse.title}
        </p>
        <p className="mt-2 line-clamp-2 text-sm text-muted-foreground sm:text-base">
          {featuredCourse.description}
        </p>
        <div className="relative mt-4 aspect-[16/10] overflow-hidden rounded-xl">
          <Image
            src={featuredCourse.thumbnail}
            alt={featuredCourse.title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 420px"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />
          <div className="absolute bottom-3 left-3 right-3">
            <Progress value={34} className="h-1.5 bg-white/20" />
            <p className="mt-1.5 text-xs font-medium text-white/90">
              Lesson 4 of 12 · On-chain data pipelines
            </p>
          </div>
        </div>
        <Link
          href={`/courses/${featuredCourse.slug}`}
          className="group mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-brand-orange transition-transform hover:translate-x-1"
        >
          Preview course
          <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
        </Link>
      </motion.div>

      {/* 3 & 4. Certificate + Dashboard — journey outcomes */}
      <div className="relative z-20 -mt-3 flex w-full gap-3 sm:gap-4">
        <motion.div
          {...float(1.2)}
          whileHover={reducedMotion ? undefined : { y: -4, scale: 1.02 }}
          className="flex-1 rotate-[-1.5deg] rounded-2xl border border-brand-navy/15 bg-gradient-to-br from-brand-navy/5 to-brand-orange/5 p-4 shadow-elevated"
        >
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-full bg-brand-navy/10">
              <Award className="size-4 text-brand-navy" />
            </div>
            <div>
              <p className="text-sm font-semibold">Certificate</p>
              <p className="text-xs text-success">Verified</p>
            </div>
          </div>
          <p className="mt-2 text-xs text-muted-foreground line-clamp-1">
            SQL for Blockchain Analytics
          </p>
        </motion.div>

        <motion.div
          {...float(1.8)}
          whileHover={reducedMotion ? undefined : { y: -4, scale: 1.02 }}
          className="flex-1 rotate-[1.5deg] rounded-2xl border bg-card p-4 shadow-elevated"
        >
          <div className="flex items-center gap-2">
            <LayoutDashboard className="size-4 text-brand-navy" />
            <p className="text-sm font-semibold">Dashboard</p>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <div className="rounded-lg bg-brand-surface px-2 py-1.5">
              <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <BookOpen className="size-2.5" />
                Courses
              </p>
              <p className="font-heading text-sm font-bold text-brand-navy">1</p>
            </div>
            <div className="rounded-lg bg-brand-surface px-2 py-1.5">
              <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <TrendingUp className="size-2.5" />
                Progress
              </p>
              <p className="font-heading text-sm font-bold text-brand-navy">68%</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
