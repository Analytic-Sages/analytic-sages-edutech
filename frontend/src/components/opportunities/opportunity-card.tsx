import Link from "next/link";
import { CalendarDays, Clock3, MapPin, Trophy, Wallet } from "lucide-react";
import { OrganizationLogo } from "@/components/opportunities/organization-logo";
import { OpportunityTrustBadge } from "@/components/opportunities/opportunity-trust-badge";
import { Badge } from "@/components/ui/badge";
import {
  compensationLabel,
  formatDeadline,
  formatPostedRelative,
  HACKATHON_FORMAT_LABELS,
  REGION_LABELS,
  resolveOrganizationLogoUrl,
  TYPE_LABELS,
  viewCtaLabel,
  WORKPLACE_LABELS,
  type HackathonEventFormat,
  type LocationRegion,
  type OpportunityCard,
} from "@/lib/opportunities";

function locationLine(opportunity: OpportunityCard) {
  const workplace = WORKPLACE_LABELS[opportunity.workplace_type];
  const regionLabel =
    opportunity.region && opportunity.region in REGION_LABELS
      ? REGION_LABELS[opportunity.region as LocationRegion]
      : null;
  if (regionLabel) return `${workplace} · ${regionLabel}`;
  if (opportunity.location) return `${workplace} · ${opportunity.location}`;
  return workplace;
}

export function OpportunityRow({
  opportunity,
  compact = false,
}: {
  opportunity: OpportunityCard;
  compact?: boolean;
}) {
  const href = `/opportunities/${opportunity.slug}`;
  const posted = formatPostedRelative(opportunity.published_at);
  const compensation = compensationLabel(opportunity);
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
  const isEvent =
    opportunity.opportunity_type === "hackathon" || opportunity.opportunity_type === "challenge";
  const isBounty = opportunity.opportunity_type === "bounty";
  const visibleSkills = opportunity.skills.slice(0, compact ? 3 : 5);
  const extraSkills = Math.max(0, opportunity.skills.length - visibleSkills.length);
  const logoUrl = resolveOrganizationLogoUrl(opportunity);

  if (compact) {
    return (
      <Link
        href={href}
        className="flex gap-3 border-b border-border/70 py-3 last:border-0 hover:bg-brand-surface/50"
      >
        <OrganizationLogo
          name={opportunity.organization_name}
          logoUrl={logoUrl}
          size="sm"
        />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-brand-navy dark:text-foreground">
            {opportunity.title}
          </p>
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            {opportunity.organization_name}
            {opportunity.location ? ` · ${opportunity.location}` : ""}
            {posted ? ` · ${posted}` : ""}
          </p>
        </div>
      </Link>
    );
  }

  return (
    <article className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm transition-colors hover:border-brand-navy/25 sm:p-6">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-stretch sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex gap-4">
            <OrganizationLogo
              name={opportunity.organization_name}
              logoUrl={logoUrl}
            />
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                {opportunity.featured ? (
                  <Badge className="bg-brand-orange text-white">Featured</Badge>
                ) : null}
                {opportunity.closing_soon ? <Badge variant="outline">Closing soon</Badge> : null}
                {isEvent && formatLabel && formatLabel !== "Format TBA" ? (
                  <Badge variant="outline">{formatLabel}</Badge>
                ) : null}
                <OpportunityTrustBadge badge={opportunity.public_badge} />
              </div>
              <h3 className="mt-1 font-heading text-xl font-semibold tracking-tight text-brand-navy dark:text-foreground">
                <Link href={href} className="hover:text-brand-orange">
                  {opportunity.title}
                </Link>
              </h3>
              <p className="mt-1 text-sm font-medium text-muted-foreground">
                {opportunity.organization_name}
              </p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <MapPin className="size-3.5 shrink-0" />
              {locationLine(opportunity)}
            </span>
            {compensation ? (
              <span className="inline-flex items-center gap-1.5">
                {isEvent || isBounty || opportunity.opportunity_type === "grant" ? (
                  <Trophy className="size-3.5 shrink-0" />
                ) : (
                  <Wallet className="size-3.5 shrink-0" />
                )}
                {compensation}
              </span>
            ) : null}
            {posted ? (
              <span className="inline-flex items-center gap-1.5">
                <Clock3 className="size-3.5 shrink-0" />
                {posted}
              </span>
            ) : null}
            {closesIn != null ? (
              <span className="inline-flex items-center gap-1.5">
                <CalendarDays className="size-3.5 shrink-0" />
                {closesIn === 0
                  ? "Closes today"
                  : `Closes in ${closesIn} day${closesIn === 1 ? "" : "s"}`}
              </span>
            ) : opportunity.deadline ? (
              <span className="inline-flex items-center gap-1.5">
                <CalendarDays className="size-3.5 shrink-0" />
                Deadline {formatDeadline(opportunity.deadline)}
              </span>
            ) : null}
          </div>

          <div className="mt-4 flex flex-wrap gap-1.5">
            <span className="rounded-full bg-brand-navy/8 px-2.5 py-1 text-xs font-medium text-brand-navy dark:bg-white/10 dark:text-foreground">
              {TYPE_LABELS[opportunity.opportunity_type]}
            </span>
            <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-800 dark:text-emerald-300">
              {WORKPLACE_LABELS[opportunity.workplace_type]}
            </span>
            {opportunity.primary_career_path ? (
              <span className="rounded-full bg-brand-orange/10 px-2.5 py-1 text-xs font-medium text-brand-orange">
                {opportunity.primary_career_path.name}
              </span>
            ) : null}
            {visibleSkills.map((skill) => (
              <Link
                key={skill.id}
                href={`/opportunities?skill=${encodeURIComponent(skill.slug)}`}
                className="rounded-full border border-border/80 bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground hover:border-brand-orange hover:text-brand-orange"
              >
                {skill.name}
              </Link>
            ))}
            {extraSkills > 0 ? (
              <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                +{extraSkills}
              </span>
            ) : null}
          </div>
        </div>

        <div className="flex shrink-0 items-center sm:pl-4">
          <Link
            href={href}
            className="inline-flex h-11 w-full items-center justify-center rounded-xl bg-brand-navy px-5 text-sm font-semibold text-white transition-colors hover:bg-brand-navy/90 sm:w-auto"
          >
            {viewCtaLabel(opportunity.opportunity_type)}
          </Link>
        </div>
      </div>
    </article>
  );
}
