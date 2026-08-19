import { Mail, LifeBuoy } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { siteConfig } from "@/config/site";

export const metadata = { title: "Contact" };

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="Contact Us"
        description="Have questions about courses, partnerships, or enterprise plans?"
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <a
          href={`mailto:${siteConfig.emails.admin}`}
          className="group flex items-center gap-3 rounded-xl border bg-brand-surface/50 p-4 transition-colors hover:bg-brand-surface"
        >
          <div className="flex size-10 items-center justify-center rounded-lg bg-brand-orange/10 text-brand-orange">
            <Mail className="size-5" />
          </div>
          <div>
            <p className="text-sm font-semibold">General inquiries</p>
            <p className="text-sm text-muted-foreground group-hover:text-foreground">
              {siteConfig.emails.admin}
            </p>
          </div>
        </a>
        <a
          href={`mailto:${siteConfig.emails.support}`}
          className="group flex items-center gap-3 rounded-xl border bg-brand-surface/50 p-4 transition-colors hover:bg-brand-surface"
        >
          <div className="flex size-10 items-center justify-center rounded-lg bg-brand-navy/10 text-brand-navy dark:bg-brand-orange/10 dark:text-brand-orange">
            <LifeBuoy className="size-5" />
          </div>
          <div>
            <p className="text-sm font-semibold">Student support</p>
            <p className="text-sm text-muted-foreground group-hover:text-foreground">
              {siteConfig.emails.support}
            </p>
          </div>
        </a>
      </div>
      <Card className="shadow-card">
        <CardContent className="pt-6">
          <form className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input id="name" placeholder="Your name" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="you@example.com" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input id="subject" placeholder="How can we help?" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="message">Message</Label>
              <Textarea id="message" rows={5} placeholder="Tell us more..." />
            </div>
            <Button className="w-full bg-brand-navy text-white hover:bg-brand-navy/90">
              Send Message
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
