import { InsightsPageContent } from "@/components/insights/insights-page-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Insights",
  description:
    "Research, tutorials, career notes, and industry analysis from Analytic Sages.",
  path: "/insights",
});

export default function InsightsPage() {
  return <InsightsPageContent />;
}
