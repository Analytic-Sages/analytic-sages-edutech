import { InsightsPageContent } from "@/components/insights/insights-page-content";
import { JsonLd } from "@/components/seo/json-ld";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Insights",
  description:
    "Research, tutorials, career notes, and industry analysis from Analytic Sages - a global blockchain data and tech education platform.",
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
