import { ExternalLink, MessageCircle, Play } from "lucide-react";
import { ButtonAnchor } from "@/components/ui/button-anchor";
import { siteConfig } from "@/config/site";
import { SectionBackground } from "@/components/marketing/section-background";

const channels = [
  {
    name: "YouTube",
    description: "Free tutorials, webinars, and technical deep dives.",
    href: siteConfig.links.youtube,
    icon: Play,
    accent: "bg-red-500/10 text-red-600",
  },
  {
    name: "Telegram",
    description: "Daily updates, live sessions, and community discussions.",
    href: siteConfig.links.telegram,
    icon: MessageCircle,
    accent: "bg-sky-500/10 text-sky-600",
  },
  {
    name: "Discord",
    description: "Study groups, mentor Q&A, and cohort channels.",
    href: siteConfig.links.discord,
    icon: MessageCircle,
    accent: "bg-indigo-500/10 text-indigo-600",
  },
];

export function HomeCommunitySection() {
  return (
    <section className="relative overflow-hidden bg-brand-surface py-28 sm:py-32">
      <SectionBackground variant="dots" />
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="grid gap-14 lg:grid-cols-2 lg:items-center lg:gap-20">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-brand-orange">
              Community
            </p>
            <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem]">
              Learn together, grow faster
            </h2>
            <p className="mt-6 max-w-lg text-lg text-muted-foreground">
              Join 700+ builders, analysts, and researchers. Attend live sessions,
              ask questions, and stay ahead in blockchain analytics.
            </p>
          </div>
          <div className="grid gap-5 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
            {channels.map((channel) => (
              <div
                key={channel.name}
                className="group rounded-2xl border bg-card p-6 shadow-card transition-all duration-300 hover:-translate-y-1 hover:shadow-elevated"
              >
                <div
                  className={`mb-4 flex size-14 items-center justify-center rounded-2xl transition-transform duration-300 group-hover:rotate-3 ${channel.accent}`}
                >
                  <channel.icon className="size-6" />
                </div>
                <h3 className="font-heading text-lg font-semibold">{channel.name}</h3>
                <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                  {channel.description}
                </p>
                <ButtonAnchor
                  href={channel.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  variant="outline"
                  size="sm"
                  className="mt-5 w-full gap-1.5 transition-all hover:-translate-y-0.5"
                >
                  Join
                  <ExternalLink className="size-3.5" />
                </ButtonAnchor>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
