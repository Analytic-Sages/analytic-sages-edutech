import { PageHeader } from "@/components/layout/page-header";
import { siteConfig } from "@/config/site";

export const metadata = { title: "About" };

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <PageHeader
        title="About Analytic Sages"
        description="We're building a premium platform for technical education in blockchain, data, and quantitative finance."
      />
      <div className="prose prose-neutral max-w-none space-y-6 text-muted-foreground">
        <p className="text-lg text-foreground">
          {siteConfig.name} exists to create job-ready engineers, researchers, analysts,
          and builders, not just course completers.
        </p>
        <p>
          Through project-based learning, industry-aligned curriculum, and a focus on
          real outcomes, we help learners go from curiosity to career. Our mission is
          simple: {siteConfig.tagline}
        </p>
        <p>
          We believe the most valuable education platforms don&apos;t just serve videos.
          They orchestrate complete learning journeys with assessments, projects,
          certificates, and pathways into fellowships and employment.
        </p>
      </div>
    </div>
  );
}
