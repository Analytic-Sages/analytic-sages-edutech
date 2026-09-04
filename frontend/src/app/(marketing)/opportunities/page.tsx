import { Suspense } from "react";
import { notFound } from "next/navigation";
import { OpportunitiesHub } from "@/components/opportunities/opportunities-hub";
import { isOpportunitiesPublic } from "@/lib/feature-flags";
import { pageMetadata } from "@/lib/seo";

export const metadata = isOpportunitiesPublic()
  ? pageMetadata({
      title: "Opportunities",
      description:
        "Discover high-signal opportunities in Web3, blockchain data, AI and quantitative finance. Jobs, hackathons, grants, fellowships and bounties for Analytic Sages learners.",
      path: "/opportunities",
    })
  : { robots: { index: false, follow: false } };

export default function OpportunitiesPage() {
  if (!isOpportunitiesPublic()) notFound();
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-sm text-muted-foreground">Loading opportunities…</div>
      }
    >
      <OpportunitiesHub />
    </Suspense>
  );
}
