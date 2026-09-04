import Link from "next/link";
import { ArrowUpRight, MapPin } from "lucide-react";
import { OpportunityTrustBadge } from "@/components/opportunities/opportunity-trust-badge";
import { Badge } from "@/components/ui/badge";
import {
  formatDeadline,
  formatPosted,
  HACKATHON_FORMAT_LABELS,
  REGION_LABELS,
  TYPE_LABELS,
  WORKPLACE_LABELS,
  type HackathonEventFormat,
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
  const hackathon = opportunity.hackathon;
  const bounty = opportunity.bounty;
  const formatLabel =
    hackathon?.event_format && hackathon.event_format in HACKATHON_FORMAT_LABELS
      ? HACKATHON_FORMAT_LABELS[hackathon.event_format as HackathonEventFormat]
      : null;
  const closesIn =
    hackathon?.registration_closes_in_days != null
      ? hackathon.registration_closes_in_days
      : bounty?.closes_in_days != null
        ? bounty.closes_in_days
        : null;
  const prize = hackathon?.prize_pool_raw || bounty?.reward_raw || null;
  const isEvent =
    opportunity.opportunity_type === "hackathon" || opportunity.opportunity_type === "challenge";
  const isBounty = opportunity.opportunity_type === "bounty";

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
          {isEvent && formatLabel && formatLabel !== "Format TBA" ? (
            <Badge variant="outline">{formatLabel}</Badge>
          ) : null}
          {isEvent && hackathon?.derived_phase === "open" ? (
            <Badge variant="outline">Registration open</Badge>
          ) : null}
          {isEvent && hackathon?.derived_phase === "ongoing" ? (
            <Badge variant="outline">Ongoing</Badge>
          ) : null}
          {isBounty && bounty?.derived_phase === "open" ? (
            <Badge variant="outline">Open</Badge>
          ) : null}
          {isBounty && bounty?.derived_phase === "closing_soon" ? (
            <Badge variant="outline">Closing soon</Badge>
          ) : null}
          {isBounty && bounty?.category && bounty.category !== "unknown" ? (
            <Badge variant="outline">{bounty.category.replaceAll("_", " ")}</Badge>
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
            {regionLabel
              ? ` · ${regionLabel}`
              : opportunity.location_scope && opportunity.location_scope !== "unknown"
                ? ` · ${opportunity.location_scope.replaceAll("_", " ")}`
                : opportunity.location
                  ? ` · ${opportunity.location}`
                  : ""}
          </span>
          {opportunity.employment_type && !isEvent ? (
            <span>{opportunity.employment_type.replaceAll("_", " ")}</span>
          ) : null}
          {prize ? <span>Prize {prize}</span> : null}
          {opportunity.primary_career_path ? (
            <span>{opportunity.primary_career_path.name}</span>
          ) : null}
          {opportunity.source?.name ? <span>Source: {opportunity.source.name}</span> : null}
          {posted ? <span>Posted {posted}</span> : null}
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
          {isEvent && closesIn != null
            ? closesIn === 0
              ? "Registration closes today"
              : `Registration closes in ${closesIn} day${closesIn === 1 ? "" : "s"}`
            : isBounty && closesIn != null
              ? closesIn === 0
                ? "Closes today"
                : `Closes in ${closesIn} day${closesIn === 1 ? "" : "s"}`
              : `Deadline ${formatDeadline(opportunity.deadline)}`}
        </p>
        <span className="inline-flex items-center gap-1 text-sm font-medium text-brand-navy group-hover:text-brand-orange dark:text-brand-orange">
          View
          <ArrowUpRight className="size-3.5" />
        </span>
      </div>
    </Link>
  );
}
