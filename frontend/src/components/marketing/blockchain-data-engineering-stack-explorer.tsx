"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  ArrowDown,
  ArrowRight,
  Boxes,
  Check,
  Hammer,
  Layers,
  Workflow,
} from "lucide-react";
import { ButtonLink } from "@/components/ui/button-link";
import {
  DEFAULT_STACK_TOOL_ID,
  STACK_CATEGORIES,
  STACK_FLOW_LAYERS,
  STACK_PATH,
  STACK_TOOLS,
  type StackCategoryId,
  type StackTool,
} from "@/lib/blockchain-data-engineering-stack";
import { cn } from "@/lib/utils";

type Props = {
  title: string;
  intro: string;
  curriculumHref: string;
};

function TechLogo({ tool, size = 28 }: { tool: StackTool; size?: number }) {
  const [failed, setFailed] = useState(false);
  const initials = tool.name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  if (!tool.iconSlug || failed) {
    return (
      <span
        className="inline-flex items-center justify-center rounded-md font-heading text-xs font-bold text-white"
        style={{ width: size, height: size, backgroundColor: tool.brandColor }}
        aria-hidden
      >
        {initials}
      </span>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element -- Simple Icons CDN; avoid next/image remote config
    <img
      src={`https://cdn.simpleicons.org/${tool.iconSlug}`}
      alt=""
      width={size}
      height={size}
      className="object-contain transition-transform duration-200 group-hover:scale-110"
      style={{ width: size, height: size }}
      onError={() => setFailed(true)}
    />
  );
}

export function BlockchainDataEngineeringStackExplorer({
  title,
  intro,
  curriculumHref,
}: Props) {
  const reduceMotion = useReducedMotion();
  const [category, setCategory] = useState<StackCategoryId | "all">("all");
  const [selectedId, setSelectedId] = useState(DEFAULT_STACK_TOOL_ID);
  const [showFlow, setShowFlow] = useState(false);

  const filtered = useMemo(() => {
    if (category === "all") return STACK_TOOLS;
    return STACK_TOOLS.filter((tool) => tool.categoryId === category);
  }, [category]);

  const selected =
    filtered.find((tool) => tool.id === selectedId) ??
    filtered[0] ??
    STACK_TOOLS.find((tool) => tool.id === DEFAULT_STACK_TOOL_ID)!;

  function selectCategory(next: StackCategoryId | "all") {
    setCategory(next);
    const list = next === "all" ? STACK_TOOLS : STACK_TOOLS.filter((t) => t.categoryId === next);
    if (!list.some((t) => t.id === selectedId) && list[0]) {
      setSelectedId(list[0].id);
    }
  }

  return (
    <section
      id="tech-stack"
      className="scroll-mt-24 border-y border-border/60 bg-[#F7F9FC] dark:bg-transparent"
    >
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-orange">
          Tech stack
        </p>
        <h2 className="mt-3 font-heading text-3xl font-bold text-[#0B1F3A] sm:text-4xl dark:text-foreground">
          {title}
        </h2>
        <p className="mt-3 max-w-2xl text-muted-foreground">{intro}</p>

        <ul className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-[#0B1F3A]/80 dark:text-foreground/80">
          <li className="inline-flex items-center gap-2">
            <Boxes className="size-4 text-brand-orange" aria-hidden />
            Industry-relevant tools
          </li>
          <li className="inline-flex items-center gap-2">
            <Hammer className="size-4 text-brand-orange" aria-hidden />
            Hands-on learning
          </li>
          <li className="inline-flex items-center gap-2">
            <Workflow className="size-4 text-brand-orange" aria-hidden />
            Build real projects
          </li>
        </ul>

        <div
          className="mt-10 flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          role="tablist"
          aria-label="Stack categories"
        >
          {STACK_CATEGORIES.map((item) => {
            const active = category === item.id;
            return (
              <button
                key={item.id}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => selectCategory(item.id)}
                className={cn(
                  "shrink-0 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange",
                  active
                    ? "border-brand-orange bg-brand-orange text-white"
                    : "border-[#0B1F3A]/15 bg-background text-[#0B1F3A] hover:border-brand-orange/50 dark:border-white/15 dark:text-foreground",
                )}
              >
                {item.label}
              </button>
            );
          })}
        </div>

        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={() => setShowFlow((v) => !v)}
            className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-orange hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
          >
            <Layers className="size-4" aria-hidden />
            {showFlow ? "Hide stack flow" : "View stack flow"}
          </button>
        </div>

        <AnimatePresence initial={false}>
          {showFlow ? (
            <motion.div
              key="flow"
              initial={reduceMotion ? false : { opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={reduceMotion ? undefined : { opacity: 0, height: 0 }}
              className="mt-4 overflow-hidden rounded-xl border border-[#0B1F3A]/12 bg-background p-5 dark:border-white/12"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">
                How the stack connects
              </p>
              <ol className="mt-4 space-y-0">
                {STACK_FLOW_LAYERS.map((layer, index) => (
                  <li key={layer.label} className="flex flex-col items-center text-center">
                    <div className="w-full max-w-md rounded-lg border border-[#0B1F3A]/10 bg-[#F7F9FC] px-4 py-3 dark:border-white/10 dark:bg-muted/30">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                        {layer.label}
                      </p>
                      <p className="mt-1 text-sm font-medium text-[#0B1F3A] dark:text-foreground">
                        {layer.tools.join(" · ")}
                      </p>
                    </div>
                    {index < STACK_FLOW_LAYERS.length - 1 ? (
                      <ArrowDown className="my-1.5 size-4 text-brand-orange" aria-hidden />
                    ) : null}
                  </li>
                ))}
              </ol>
            </motion.div>
          ) : null}
        </AnimatePresence>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-start">
          <div
            className="grid grid-cols-2 gap-2.5 sm:grid-cols-3"
            role="listbox"
            aria-label="Technologies"
          >
            {filtered.map((tool) => {
              const active = tool.id === selected.id;
              return (
                <button
                  key={tool.id}
                  type="button"
                  role="option"
                  aria-selected={active}
                  onClick={() => setSelectedId(tool.id)}
                  className={cn(
                    "group flex flex-col items-start gap-2 rounded-xl border bg-background p-3 text-left transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange",
                    active
                      ? "border-brand-orange shadow-md ring-1 ring-brand-orange/30"
                      : "border-[#0B1F3A]/12 hover:-translate-y-0.5 hover:border-[#0B1F3A]/30 hover:shadow-sm dark:border-white/12",
                  )}
                >
                  <TechLogo tool={tool} />
                  <span className="font-heading text-sm font-semibold text-[#0B1F3A] dark:text-foreground">
                    {tool.name}
                  </span>
                  <span className="line-clamp-2 text-[11px] leading-snug text-muted-foreground">
                    {tool.categoryLabel}
                  </span>
                </button>
              );
            })}
          </div>

          <AnimatePresence mode="wait">
            <motion.aside
              key={selected.id}
              initial={reduceMotion ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduceMotion ? undefined : { opacity: 0, y: -6 }}
              transition={{ duration: 0.2 }}
              className="rounded-xl border border-[#0B1F3A]/12 bg-background p-5 shadow-sm dark:border-white/12 lg:sticky lg:top-24"
              aria-live="polite"
            >
              <div className="flex items-start gap-3">
                <TechLogo tool={selected} size={36} />
                <div>
                  <h3 className="font-heading text-xl font-bold text-[#0B1F3A] dark:text-foreground">
                    {selected.name}
                  </h3>
                  <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">
                    {selected.categoryLabel}
                  </p>
                </div>
              </div>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">{selected.summary}</p>

              <p className="mt-5 text-xs font-semibold uppercase tracking-wide text-[#0B1F3A] dark:text-foreground">
                What you&apos;ll use it for
              </p>
              <ul className="mt-2 space-y-1.5">
                {selected.uses.map((use) => (
                  <li key={use} className="flex gap-2 text-sm">
                    <Check className="mt-0.5 size-4 shrink-0 text-brand-orange" strokeWidth={2.5} />
                    {use}
                  </li>
                ))}
              </ul>

              <p className="mt-5 text-xs font-semibold uppercase tracking-wide text-[#0B1F3A] dark:text-foreground">
                Where it fits
              </p>
              <ol className="mt-2 space-y-0 text-sm">
                {STACK_PATH.map((node, index) => {
                  const highlight = node === selected.pathHighlight;
                  return (
                    <li key={node} className="flex flex-col items-start">
                      <span
                        className={cn(
                          "rounded px-2 py-0.5",
                          highlight
                            ? "bg-brand-orange/15 font-semibold text-brand-orange"
                            : "text-muted-foreground",
                        )}
                      >
                        {node}
                      </span>
                      {index < STACK_PATH.length - 1 ? (
                        <ArrowDown className="my-0.5 ml-3 size-3 text-[#0B1F3A]/30 dark:text-white/30" />
                      ) : null}
                    </li>
                  );
                })}
              </ol>
            </motion.aside>
          </AnimatePresence>
        </div>

        <div className="mt-14 max-w-2xl border-t border-[#0B1F3A]/10 pt-10 dark:border-white/10">
          <h3 className="font-heading text-2xl font-bold text-[#0B1F3A] dark:text-foreground">
            These tools are more powerful when you understand how they work together.
          </h3>
          <p className="mt-3 text-muted-foreground">
            You will explore the technologies behind modern data systems and apply them as you build
            practical blockchain data projects.
          </p>
          <ButtonLink href={curriculumHref} variant="ghost" className="mt-4 px-0 text-brand-orange">
            Explore the programme curriculum
            <ArrowRight className="ml-1 size-4" />
          </ButtonLink>
        </div>
      </div>
    </section>
  );
}
