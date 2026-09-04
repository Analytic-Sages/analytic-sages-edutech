import Link from "next/link";
import { ArrowLeft, CalendarDays, Clock3, MapPin, Trophy, Wallet } from "lucide-react";
import { OpportunityDescription } from "@/components/opportunities/opportunity-description";
import { ApplySafetyButton } from "@/components/opportunities/apply-safety-modal";
import { OpportunityRow } from "@/components/opportunities/opportunity-card";
import { OrganizationLogo } from "@/components/opportunities/organization-logo";
import { OpportunityTrustBadge } from "@/components/opportunities/opportunity-trust-badge";
import { SaveOpportunityButton } from "@/components/opportunities/save-opportunity-button";
import { Badge } from "@/components/ui/badge";
import {
  compensationLabel,
  formatDeadline,
  formatPostedRelative,
  learningPathForOpportunity,
  REGION_LABELS,
  resolveOrganizationLogoUrl,
  SAFETY_NOTICE,
  TYPE_LABELS,
  WORKPLACE_LABELS,
  type LocationRegion,
  type OpportunityDetail,
} from "@/lib/opportunities";

function ProseBlock({ title, text }: { title: string; text: string | null | undefined }) {
  if (!text?.trim()) return null;
  return (
    <section className="border-t border-border/70 pt-8 first:border-0 first:pt-0">
      <h2 className="mb-4 font-heading text-lg font-semibold text-brand-navy dark:text-foreground">
        {title}
      </h2>
      <OpportunityDescription text={text} />
    </section>
  );
}

function MetaRow({ opportunity }: { opportunity: OpportunityDetail }) {
  const compensation = compensationLabel(opportunity);
  const posted = formatPostedRelative(opportunity.published_at);
  return (
    <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted-foreground">
      <span className="inline-flex items-center gap-1.5">
        <MapPin className="size-4 shrink-0" />
        {WORKPLACE_LABELS[opportunity.workplace_type]}
        {opportunity.region && opportunity.region in REGION_LABELS
          ? ` · ${REGION_LABELS[opportunity.region as LocationRegion]}`
          : opportunity.location
            ? ` · ${opportunity.location}`
            : ""}
      </span>
      {compensation ? (
        <span className="inline-flex items-center gap-1.5">
          {opportunity.opportunity_type === "hackathon" ||
          opportunity.opportunity_type === "grant" ||
          opportunity.opportunity_type === "bounty" ? (
            <Trophy className="size-4 shrink-0" />
          ) : (
            <Wallet className="size-4 shrink-0" />
          )}
          {compensation}
        </span>
      ) : null}
      {posted ? (
        <span className="inline-flex items-center gap-1.5">
          <Clock3 className="size-4 shrink-0" />
          Posted {posted}
        </span>
      ) : null}
      {opportunity.deadline ? (
        <span className="inline-flex items-center gap-1.5">
          <CalendarDays className="size-4 shrink-0" />
          Deadline {formatDeadline(opportunity.deadline)}
        </span>
      ) : null}
    </div>
  );
}

export function OpportunityDetailView({ opportunity }: { opportunity: OpportunityDetail }) {
  const primary =
    opportunity.career_paths.find((item) => item.is_primary) || opportunity.primary_career_path;
  const learn = learningPathForOpportunity(opportunity);
  const skillPreview = opportunity.skills.slice(0, 12);
  const logoUrl = resolveOrganizationLogoUrl(opportunity);

  return (
    <div className="bg-[#F7F9FC] pb-16 dark:bg-background">
      <div className="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
        <Link
          href="/opportunities"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-brand-orange"
        >
          <ArrowLeft className="size-4" />
          Back to all opportunities
        </Link>

        <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="space-y-6">
            <section className="rounded-2xl border border-border/80 bg-card p-6 shadow-sm sm:p-8">
              <div className="flex flex-wrap items-center gap-2">
                <Badge className="bg-brand-orange text-white">
                  {TYPE_LABELS[opportunity.opportunity_type]}
                </Badge>
                <Badge variant="outline">{WORKPLACE_LABELS[opportunity.workplace_type]}</Badge>
                {opportunity.closing_soon ? <Badge variant="outline">Closing soon</Badge> : null}
                <OpportunityTrustBadge badge={opportunity.public_badge} />
              </div>

              <h1 className="mt-4 font-heading text-3xl font-bold tracking-tight text-brand-navy dark:text-foreground sm:text-4xl">
                {opportunity.title}
              </h1>

              <div className="mt-4 flex items-center gap-3">
                <OrganizationLogo
                  name={opportunity.organization_name}
                  logoUrl={logoUrl}
                  size="lg"
                />
                <div>
                  <p className="font-heading text-lg font-semibold">{opportunity.organization_name}</p>
                  {opportunity.source?.name ? (
                    <p className="text-sm text-muted-foreground">Source: {opportunity.source.name}</p>
                  ) : null}
                </div>
              </div>

              <MetaRow opportunity={opportunity} />

              <div className="mt-5 flex flex-wrap gap-1.5">
                {primary ? (
                  <span className="rounded-full bg-brand-orange/10 px-2.5 py-1 text-xs font-medium text-brand-orange">
                    {primary.name}
                  </span>
                ) : null}
                {skillPreview.map((skill) => (
                  <Link
                    key={skill.id}
                    href={`/opportunities?skill=${encodeURIComponent(skill.slug)}`}
                    className="rounded-full border border-border/80 bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground hover:border-brand-orange hover:text-brand-orange"
                  >
                    {skill.name}
                  </Link>
                ))}
              </div>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
                <ApplySafetyButton
                  href={opportunity.application_url}
                  domain={opportunity.application_domain}
                  opportunityType={opportunity.opportunity_type}
                  className="sm:w-auto sm:min-w-[10rem]"
                />
                <SaveOpportunityButton
                  key={opportunity.id}
                  opportunityId={opportunity.id}
                  initiallySaved={opportunity.saved}
                  initiallyApplied={opportunity.applied}
                />
              </div>
            </section>

            <section className="rounded-2xl border border-border/80 bg-card p-6 shadow-sm sm:p-8">
              <h2 className="font-heading text-xl font-semibold text-brand-navy dark:text-foreground">
                Opportunity details
              </h2>
              <div className="mt-6 space-y-2">
                <ProseBlock title={`About ${opportunity.organization_name}`} text={opportunity.description} />
                <ProseBlock title="Responsibilities" text={opportunity.responsibilities} />
                <ProseBlock title="Requirements" text={opportunity.requirements} />
                <ProseBlock title="Benefits" text={opportunity.benefits} />
              </div>

              {opportunity.career_paths.length > 0 ? (
                <div className="mt-8 border-t border-border/70 pt-8">
                  <h3 className="font-heading text-lg font-semibold">Best for</h3>
                  <p className="mt-2 text-muted-foreground">
                    {primary ? primary.name : opportunity.career_paths[0].name}
                  </p>
                  {opportunity.career_paths.length > 1 ? (
                    <p className="mt-1 text-sm text-muted-foreground">
                      Also related:{" "}
                      {opportunity.career_paths
                        .filter((item) => !item.is_primary)
                        .map((item) => item.name)
                        .join(" · ")}
                    </p>
                  ) : null}
                </div>
              ) : null}

              {opportunity.skills.length > 0 ? (
                <div className="mt-8 border-t border-border/70 pt-8">
                  <h3 className="font-heading text-lg font-semibold">Why this matches our community</h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    This opportunity aligns with skills Analytic Sages learners build across data,
                    AI, and quantitative careers.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {opportunity.skills.map((skill) => (
                      <Link
                        key={skill.id}
                        href={`/opportunities?skill=${encodeURIComponent(skill.slug)}`}
                        className="rounded-full border border-border/80 px-3 py-1.5 text-sm hover:border-brand-orange hover:text-brand-orange"
                      >
                        {skill.name}
                      </Link>
                    ))}
                  </div>
                </div>
              ) : null}

              <p className="mt-8 rounded-xl border bg-brand-surface/70 p-4 text-sm text-muted-foreground">
                {SAFETY_NOTICE}
              </p>
            </section>
          </div>

          <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
            {opportunity.similar.length > 0 ? (
              <section className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm">
                <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Similar opportunities
                </h2>
                <div className="mt-3">
                  {opportunity.similar.map((item) => (
                    <OpportunityRow key={item.id} opportunity={item} compact />
                  ))}
                </div>
              </section>
            ) : null}

            <section className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <OrganizationLogo
                  name={opportunity.organization_name}
                  logoUrl={logoUrl}
                />
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">{opportunity.title}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    {opportunity.organization_name}
                  </p>
                </div>
              </div>
              <div className="mt-4">
                <ApplySafetyButton
                  href={opportunity.application_url}
                  domain={opportunity.application_domain}
                  opportunityType={opportunity.opportunity_type}
                />
              </div>
              {opportunity.source_url ? (
                <div className="mt-3 text-center">
                  <ApplySafetyButton
                    href={opportunity.source_url}
                    label="View original listing"
                    variant="text"
                  />
                </div>
              ) : null}
              <OpportunityTrustBadge badge={opportunity.public_badge} showMeaning />
            </section>

            {learn ? (
              <section className="rounded-2xl border border-brand-navy/15 bg-[#EEF3FA] p-5 dark:bg-brand-navy/20">
                <p className="text-sm font-semibold text-brand-navy dark:text-foreground">
                  Want to land this role?
                </p>
                <p className="mt-2 font-heading text-base font-semibold">{learn.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{learn.body}</p>
                <Link
                  href={learn.href}
                  className="mt-4 inline-flex text-sm font-semibold text-brand-orange hover:underline"
                >
                  Explore programme →
                </Link>
              </section>
            ) : null}
          </aside>
        </div>
      </div>
    </div>
  );
}
