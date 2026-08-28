import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { OpportunitiesHub } from "@/components/opportunities/opportunities-hub";
import { OpportunityDetailView } from "@/components/opportunities/opportunity-detail";
import { ApiError } from "@/lib/api";
import { isOpportunitiesPublic } from "@/lib/feature-flags";
import {
  getOpportunity,
  TYPE_LABELS,
  TYPE_ROUTES,
  typeFromPath,
  type OpportunityDetail,
} from "@/lib/opportunities";
import { pageMetadata } from "@/lib/seo";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ slug: string }> };

async function loadOpportunity(slug: string): Promise<OpportunityDetail | null> {
  try {
    return await getOpportunity(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  if (!isOpportunitiesPublic()) return { robots: { index: false, follow: false } };
  const { slug } = await params;
  const type = typeFromPath(slug);
  if (type) {
    const route = TYPE_ROUTES.find((item) => item.type === type);
    return pageMetadata({
      title: route?.label || "Opportunities",
      description: `${route?.label || "Opportunities"} mapped to Analytic Sages career pathways.`,
      path: `/opportunities/${slug}`,
    });
  }
  const opportunity = await loadOpportunity(slug);
  if (!opportunity) return { title: "Opportunity" };
  return pageMetadata({
    title: opportunity.title,
    description: `${opportunity.organization_name} · ${TYPE_LABELS[opportunity.opportunity_type]}`,
    path: `/opportunities/${opportunity.slug}`,
  });
}

export default async function OpportunitySlugPage({ params }: Props) {
  if (!isOpportunitiesPublic()) notFound();
  const { slug } = await params;
  const type = typeFromPath(slug);
  if (type) {
    const route = TYPE_ROUTES.find((item) => item.type === type);
    return (
      <OpportunitiesHub
        initialType={type}
        title={route?.label || "Opportunities"}
        description={`${route?.label || "Opportunities"} selected for Analytic Sages learners and mapped to our career pathways.`}
      />
    );
  }

  const opportunity = await loadOpportunity(slug);
  if (!opportunity) notFound();
  return <OpportunityDetailView opportunity={opportunity} />;
}
