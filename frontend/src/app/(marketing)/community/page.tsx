import { ExternalLink, MessageCircle, Play } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { JsonLd } from "@/components/seo/json-ld";
import { ButtonAnchor } from "@/components/ui/button-anchor";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { siteConfig } from "@/config/site";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";

const channels = [
  {
    name: "X",
    description: "Product updates, programme news, and onchain education threads.",
    href: siteConfig.links.x,
    icon: ExternalLink,
    color: "text-foreground",
  },
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
    "Join the Analytic Sages global community on X, YouTube, Telegram, and Discord for tutorials, study groups, and cohort updates.",
  path: "/community",
});

export default function CommunityPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "Community", path: "/community" },
        ])}
      />
      <PageHeader
        title="Join the Community"
        description="Connect with learners, mentors, and builders around the world"
      />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
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
