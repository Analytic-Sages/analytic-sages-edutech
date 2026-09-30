import { InsightsPageContent } from "@/components/insights/insights-page-content";
import { JsonLd } from "@/components/seo/json-ld";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Insights",
  description:
    "Research, tutorials, case studies and practical insights on blockchain data, DeFi, AI, quantitative finance and software engineering.",
  path: "/insights",
});

export default function InsightsPage() {
  return (
    <>
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "Insights", path: "/insights" },
        ])}
      />
      <InsightsPageContent />
    </>
  );
}
