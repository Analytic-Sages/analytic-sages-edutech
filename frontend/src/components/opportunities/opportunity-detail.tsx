import { CalendarDays, MapPin } from "lucide-react";
import { OpportunityDescription } from "@/components/opportunities/opportunity-description";
import { ApplySafetyButton } from "@/components/opportunities/apply-safety-modal";
import { OpportunityRow } from "@/components/opportunities/opportunity-card";
import { OpportunityTrustBadge } from "@/components/opportunities/opportunity-trust-badge";
import { SaveOpportunityButton } from "@/components/opportunities/save-opportunity-button";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import {
  formatDeadline,
  formatPosted,
  REGION_LABELS,
  SAFETY_NOTICE,
  TYPE_LABELS,
  WORKPLACE_LABELS,
  type LocationRegion,
  type OpportunityDetail,
} from "@/lib/opportunities";

function ProseBlock({ title, text }: { title: string; text: string | null | undefined }) {
  if (!text?.trim()) return null;
  return (
    <section>
      <h2 className="mb-4 font-heading text-lg font-semibold">{title}</h2>
      <OpportunityDescription text={text} />
    </section>
  );
}

export function OpportunityDetailView({ opportunity }: { opportunity: OpportunityDetail }) {
  const primary =
    opportunity.career_paths.find((item) => item.is_primary) || opportunity.primary_career_path;

  return (
    <div className="pb-16">
      <div className="border-b bg-brand-surface">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <PageHeader
            breadcrumbs={[
              { label: "Opportunities", href: "/opportunities" },
              { label: TYPE_LABELS[opportunity.opportunity_type] },
              { label: opportunity.title },
            ]}
            title={opportunity.title}
            description={opportunity.organization_name}
          />
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Badge className="bg-brand-orange text-white">
              {TYPE_LABELS[opportunity.opportunity_type]}
            </Badge>
            <Badge variant="outline">{WORKPLACE_LABELS[opportunity.workplace_type]}</Badge>
            {opportunity.closing_soon ? <Badge variant="outline">Closing soon</Badge> : null}
            <OpportunityTrustBadge badge={opportunity.public_badge} />
          </div>
          <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-2">
              <MapPin className="size-4" />
              {WORKPLACE_LABELS[opportunity.workplace_type]}
              {opportunity.region && opportunity.region in REGION_LABELS
                ? ` · ${REGION_LABELS[opportunity.region as LocationRegion]}`
                : opportunity.location
                  ? ` · ${opportunity.location}`
                  : ""}
            </span>
            <span className="inline-flex items-center gap-2">
              <CalendarDays className="size-4" />
              Deadline {formatDeadline(opportunity.deadline)}
            </span>
            {formatPosted(opportunity.published_at) ? (
              <span>Added {formatPosted(opportunity.published_at)}</span>
            ) : null}
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[minmax(0,1fr)_20rem] lg:px-8">
        <div className="space-y-8">
          <ProseBlock title="About this opportunity" text={opportunity.description} />
          <ProseBlock title="Responsibilities" text={opportunity.responsibilities} />
          <ProseBlock title="Requirements" text={opportunity.requirements} />
          <ProseBlock title="Benefits" text={opportunity.benefits} />

          {opportunity.career_paths.length > 0 ? (
            <section>
              <h2 className="font-heading text-lg font-semibold">Best for</h2>
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
            </section>
          ) : null}

          {opportunity.skills.length > 0 ? (
            <section>
              <h2 className="font-heading text-lg font-semibold">Related skills</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {opportunity.skills.map((skill) => (
                  <Badge key={skill.id} variant="outline">
                    {skill.name}
                  </Badge>
                ))}
              </div>
            </section>
          ) : null}

          <p className="rounded-xl border bg-brand-surface/70 p-4 text-sm text-muted-foreground">
            {SAFETY_NOTICE}
          </p>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <div className="rounded-2xl border bg-card p-5 shadow-card">
            <p className="text-sm font-medium text-brand-navy dark:text-foreground">
              {opportunity.organization_name}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {WORKPLACE_LABELS[opportunity.workplace_type]}
              {opportunity.location ? ` · ${opportunity.location}` : ""}
            </p>
            <div className="mt-5">
              <ApplySafetyButton
                href={opportunity.application_url}
                domain={opportunity.application_domain}
                opportunityType={opportunity.opportunity_type}
              />
            </div>
            <div className="mt-3">
              <SaveOpportunityButton
                key={opportunity.id}
                opportunityId={opportunity.id}
                initiallySaved={opportunity.saved}
                initiallyApplied={opportunity.applied}
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
            <p className="mt-4 text-xs text-muted-foreground">
              Last updated{" "}
              {new Intl.DateTimeFormat("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              }).format(new Date(opportunity.updated_at))}
            </p>
          </div>
        </aside>
      </div>

      {opportunity.similar.length > 0 ? (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="mb-2 font-heading text-xl font-semibold">Similar opportunities</h2>
          <div className="border-t">
            {opportunity.similar.map((item) => (
              <OpportunityRow key={item.id} opportunity={item} />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
