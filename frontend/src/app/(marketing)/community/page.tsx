import { ExternalLink, MessageCircle, Play } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ButtonAnchor } from "@/components/ui/button-anchor";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { siteConfig } from "@/config/site";
import { pageMetadata } from "@/lib/seo";

const channels = [
  {
    name: "YouTube",
    description: "Free tutorials, webinars, and technical deep dives.",
    href: siteConfig.links.youtube,
    icon: Play,
    color: "text-red-600",
  },
  {
    name: "Telegram",
    description: "Daily updates, job alerts, and community discussions.",
    href: siteConfig.links.telegram,
    icon: MessageCircle,
    color: "text-blue-500",
  },
  {
    name: "Discord",
    description: "Study groups, mentor Q&A, and cohort channels.",
    href: siteConfig.links.discord,
    icon: MessageCircle,
    color: "text-indigo-500",
  },
];

export const metadata = pageMetadata({
  title: "Community",
  description:
    "Join the Analytic Sages community on YouTube, Telegram, and Discord for tutorials, study groups, and cohort updates.",
  path: "/community",
});

export default function CommunityPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="Join the Community"
        description="Connect with learners, mentors, and builders around the world"
      />
      <div className="grid gap-6 sm:grid-cols-3">
        {channels.map((channel) => (
          <Card key={channel.name} className="shadow-card">
            <CardHeader>
              <channel.icon className={`size-8 ${channel.color}`} />
              <CardTitle className="mt-2">{channel.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">{channel.description}</p>
              <ButtonAnchor
                href={channel.href}
                target="_blank"
                rel="noopener noreferrer"
                variant="outline"
                className="gap-2"
              >
                Join <ExternalLink className="size-3.5" />
              </ButtonAnchor>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
