import { ShowcaseContent } from "@/components/marketing/showcase-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Student Projects",
  description: "Real projects built by Analytic Sages learners in live cohorts.",
  path: "/showcase",
});

export default function ShowcasePage() {
  return <ShowcaseContent />;
}
