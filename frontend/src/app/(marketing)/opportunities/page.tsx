import { notFound } from "next/navigation";
import { OpportunitiesHub } from "@/components/opportunities/opportunities-hub";
import { isOpportunitiesPublic } from "@/lib/feature-flags";
import { pageMetadata } from "@/lib/seo";

export const metadata = isOpportunitiesPublic()
  ? pageMetadata({
      title: "Opportunities",
      description:
        "Career intelligence for Analytic Sages learners. Discover jobs, internships, fellowships, hackathons, grants and bounties relevant to your skills.",
      path: "/opportunities",
    })
  : { robots: { index: false, follow: false } };

export default function OpportunitiesPage() {
  if (!isOpportunitiesPublic()) notFound();
  return <OpportunitiesHub />;
}
