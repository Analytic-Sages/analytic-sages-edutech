import { OpportunitiesHub } from "@/components/opportunities/opportunities-hub";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Opportunities",
  description:
    "Career intelligence for Analytic Sages learners. Discover jobs, internships, fellowships, hackathons, grants and bounties relevant to your skills.",
  path: "/opportunities",
});

export default function OpportunitiesPage() {
  return <OpportunitiesHub />;
}
