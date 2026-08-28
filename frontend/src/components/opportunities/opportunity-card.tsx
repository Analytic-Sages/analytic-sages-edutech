import Link from "next/link";
import { ArrowUpRight, MapPin } from "lucide-react";
import { OpportunityTrustBadge } from "@/components/opportunities/opportunity-trust-badge";
import { Badge } from "@/components/ui/badge";
import {
  formatDeadline,
  formatPosted,
  REGION_LABELS,
  TYPE_LABELS,
  WORKPLACE_LABELS,
  type LocationRegion,
  type OpportunityCard,
} from "@/lib/opportunities";

export function OpportunityRow({ opportunity }: { opportunity: OpportunityCard }) {
  const href = `/opportunities/${opportunity.slug}`;
  const posted = formatPosted(opportunity.published_at);
  const regionLabel =
    opportunity.region && opportunity.region in REGION_LABELS
      ? REGION_LABELS[opportunity.region as LocationRegion]
      : null;
  return (
    <Link
      href={href}
      className="group grid gap-4 border-b border-border/80 py-6 transition-colors hover:bg-brand-surface/60 sm:grid-cols-[7rem_1fr_auto] sm:items-start sm:gap-8"
    >
      <div className="text-xs font-semibold uppercase tracking-wide text-brand-orange">
        {TYPE_LABELS[opportunity.opportunity_type]}
      </div>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          {opportunity.featured ? (
            <Badge className="bg-brand-orange text-white">Featured</Badge>
          ) : null}
          {opportunity.closing_soon ? (
            <Badge variant="outline">Closing soon</Badge>
          ) : null}
          <OpportunityTrustBadge badge={opportunity.public_badge} />
        </div>
        <h3 className="mt-1 font-heading text-xl font-semibold tracking-tight text-brand-navy group-hover:text-brand-orange dark:text-foreground">
          {opportunity.title}
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">{opportunity.organization_name}</p>
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <MapPin className="size-3.5" />
            {WORKPLACE_LABELS[opportunity.workplace_type]}
            {regionLabel ? ` · ${regionLabel}` : opportunity.location ? ` · ${opportunity.location}` : ""}
          </span>
          {opportunity.primary_career_path ? (
            <span>Best for {opportunity.primary_career_path.name}</span>
          ) : null}
          {posted ? <span>Added {posted}</span> : null}
        </div>
        {opportunity.skills.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {opportunity.skills.slice(0, 4).map((skill) => (
              <Badge key={skill.id} variant="outline">
                {skill.name}
              </Badge>
            ))}
          </div>
        ) : null}
      </div>
      <div className="flex items-center justify-between gap-4 sm:flex-col sm:items-end sm:justify-start">
        <p className="text-sm text-muted-foreground">
          Deadline {formatDeadline(opportunity.deadline)}
        </p>
        <span className="inline-flex items-center gap-1 text-sm font-medium text-brand-navy group-hover:text-brand-orange dark:text-brand-orange">
          View
          <ArrowUpRight className="size-3.5" />
        </span>
      </div>
    </Link>
  );
}
