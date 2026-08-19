import { ProgramsPageContent } from "@/components/marketing/programs-page-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Our Programs",
  description:
    "Choose Instructor-Led live cohorts or Self-Paced courses in blockchain data, AI, and quantitative finance.",
  path: "/programs",
});

export default function ProgramsPage() {
  return <ProgramsPageContent />;
}
