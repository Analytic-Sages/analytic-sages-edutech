import { notFound } from "next/navigation";
import { MyOpportunitiesContent } from "@/components/opportunities/my-opportunities-content";
import { isOpportunitiesPublic } from "@/lib/feature-flags";

export const metadata = isOpportunitiesPublic()
  ? { title: "My Opportunities" }
  : { robots: { index: false, follow: false } };

export default function MyOpportunitiesPage() {
  if (!isOpportunitiesPublic()) notFound();
  return <MyOpportunitiesContent />;
}
