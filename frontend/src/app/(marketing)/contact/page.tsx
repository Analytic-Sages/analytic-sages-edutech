import { Mail, LifeBuoy } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ContactForm } from "@/components/marketing/contact-form";
import { siteConfig } from "@/config/site";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Contact",
  description:
    "Contact Analytic Sages about courses, partnerships, or student support. Email admin@analyticsages.io or support@analyticsages.io.",
  path: "/contact",
});

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
      <ContactForm />
    </div>
  );
}
