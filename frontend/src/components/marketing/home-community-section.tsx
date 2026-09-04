"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { ArrowRight, ExternalLink, MessageCircle, Play } from "lucide-react";
import { ButtonAnchor } from "@/components/ui/button-anchor";
import { ButtonLink } from "@/components/ui/button-link";
import { siteConfig } from "@/config/site";
import { SectionBackground } from "@/components/marketing/section-background";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

const channels = [
  {
    name: "X",
    href: siteConfig.links.x,
    icon: ExternalLink,
    accent: "bg-foreground/10 text-foreground",
  },
  {
    name: "Discord",
    href: siteConfig.links.discord,
    icon: MessageCircle,
    accent: "bg-indigo-500/10 text-indigo-600",
  },
  {
    name: "Telegram",
    href: siteConfig.links.telegram,
    icon: MessageCircle,
    accent: "bg-sky-500/10 text-sky-600",
  },
  {
    name: "YouTube",
    href: siteConfig.links.youtube,
    icon: Play,
    accent: "bg-red-500/10 text-red-600",
  },
];

export function HomeCommunitySection() {
  const reducedMotion = useReducedMotion();

  const textReveal = reducedMotion
    ? {}
    : {
        initial: { opacity: 0, y: 24 },
        whileInView: { opacity: 1, y: 0 },
        viewport: { once: true, margin: "-80px" },
        transition: { duration: 0.6, ease: "easeOut" as const },
      };

  const imageReveal = reducedMotion
    ? {}
    : {
        initial: { opacity: 0, y: 24, scale: 0.98 },
        whileInView: { opacity: 1, y: 0, scale: 1 },
        viewport: { once: true, margin: "-80px" },
        transition: { duration: 0.7, delay: 0.15, ease: "easeOut" as const },
      };

  return (
    <section className="relative overflow-hidden bg-brand-surface py-28 sm:py-32">
      <SectionBackground variant="dots" />
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="grid gap-14 lg:grid-cols-2 lg:items-center lg:gap-16 xl:gap-20">
          {/* Text content: first on mobile and desktop-left */}
          <motion.div {...textReveal}>
            <p className="text-base font-semibold uppercase tracking-wide text-brand-orange sm:text-lg">
              The Analytic Sages Community
            </p>
            <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem] lg:leading-[1.1]">
              Learn with people who are building too.
            </h2>
            <p className="mt-6 max-w-lg text-lg leading-relaxed text-muted-foreground">
              From hands-on workshops to online learning, Analytic Sages brings
              together analysts, engineers, researchers, and builders learning
              practical technology skills together, reviewing projects, sharing
              opportunities, and solving real blockchain problems every day.
            </p>

            <div className="mt-8">
              <ButtonLink
                href="/community"
                size="lg"
                className="group h-12 bg-brand-orange px-8 text-base text-white shadow-card transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-elevated"
              >
                Join the Community
                <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
              </ButtonLink>
            </div>

            <div className="mt-10 flex flex-wrap gap-3">
              {channels.map((channel) => (
                <ButtonAnchor
                  key={channel.name}
                  href={channel.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  variant="outline"
                  size="sm"
                  className="gap-2 transition-all hover:-translate-y-0.5"
                >
                  <span
                    className={`flex size-5 items-center justify-center rounded-md ${channel.accent}`}
                  >
                    <channel.icon className="size-3" />
                  </span>
                  {channel.name}
                  <ExternalLink className="size-3 text-muted-foreground" />
                </ButtonAnchor>
              ))}
            </div>
          </motion.div>

          {/* Workshop photograph: editorial treatment */}
          <motion.div {...imageReveal} className="relative xl:-mr-4">
            {/* Subtle brand accent behind the photo */}
            <div
              aria-hidden
              className="absolute -bottom-5 -right-5 h-2/3 w-2/3 rounded-[28px] bg-brand-orange/10"
            />
            <div className="group relative aspect-[4/3] overflow-hidden rounded-[24px] shadow-elevated">
              <Image
                src="/4.png"
                alt="Analytic Sages community members gathered at an in-person workshop"
                fill
                className="object-cover object-center transition-transform duration-500 ease-out group-hover:scale-[1.015]"
                sizes="(max-width: 1024px) 100vw, 50vw"
              />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
