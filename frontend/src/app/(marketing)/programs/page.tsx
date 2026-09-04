import { ProgramsPageContent } from "@/components/marketing/programs-page-content";
import { JsonLd } from "@/components/seo/json-ld";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Our Programs",
  description:
    "Choose Instructor-Led live cohorts or Self-Paced courses from Analytic Sages - global programmes in blockchain data, AI, and quantitative finance.",
  path: "/programs",
});

export default function ProgramsPage() {
  return (
    <>
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "Our Programs", path: "/programs" },
        ])}
      />
      <ProgramsPageContent />
    </>
  );
}
