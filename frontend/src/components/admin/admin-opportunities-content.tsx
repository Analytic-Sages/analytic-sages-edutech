"use client";

import { useEffect, useState } from "react";
import { Briefcase, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiError } from "@/lib/api";
import {
  formatDeadline,
  getAdminOpportunities,
  getAdminOpportunityOverview,
  publishAdminOpportunity,
  rejectAdminOpportunity,
  sendAdminOpportunityDigest,
  syncAdminOpportunitySources,
  TYPE_LABELS,
  type OpportunityAdmin,
  type OpportunityAdminOverview,
  type OpportunityStatus,
  type OpportunitySyncAllResult,
} from "@/lib/opportunities";
import { isOpportunitiesPublic } from "@/lib/feature-flags";

const STATUS_LABEL: Record<OpportunityStatus, string> = {
  draft: "Draft",
  published: "Published",
  rejected: "Rejected",
  expired: "Expired",
  archived: "Archived",
};

type Tab = "all" | "review";

export function AdminOpportunitiesContent() {
  const [tab, setTab] = useState<Tab>("all");
  const [rows, setRows] = useState<OpportunityAdmin[]>([]);
  const [overview, setOverview] = useState<OpportunityAdminOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [digesting, setDigesting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncSummary, setSyncSummary] = useState<OpportunitySyncAllResult | null>(null);
  const [actingId, setActingId] = useState<string | null>(null);

  function load(nextTab: Tab = tab) {
    return Promise.all([
      getAdminOpportunities(nextTab === "review" ? { review: true } : {}),
      getAdminOpportunityOverview(),
    ]).then(([list, counts]) => {
      setRows(list.items);
      setOverview(counts);
    });
  }

  useEffect(() => {
    let cancelled = false;
    load(tab)
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load opportunities.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  function selectTab(next: Tab) {
    if (next === tab) return;
    setError(null);
    setLoading(true);
    setTab(next);
  }

  async function fetchNewListings() {
    setSyncing(true);
    setError(null);
    setSyncSummary(null);
    try {
      const result = await syncAdminOpportunitySources();
      setSyncSummary(result);
      if (result.created > 0 && tab !== "review") {
        setLoading(true);
        setTab("review");
      } else {
        await load(tab);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not sync sources.");
    } finally {
      setSyncing(false);
    }
  }

  async function sendDigest() {
    setDigesting(true);
    setError(null);
    try {
      const result = await sendAdminOpportunityDigest(true);
      setError(null);
      if (result.status === "skipped") {
        setError(result.detail || "Digest was skipped.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not send weekly digest.");
    } finally {
      setDigesting(false);
    }
  }

  async function act(id: string, action: "publish" | "reject") {
    setActingId(id);
    try {
      if (action === "publish") await publishAdminOpportunity(id);
      else await rejectAdminOpportunity(id, "Rejected from review queue");
      await load(tab);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update opportunity.");
    } finally {
      setActingId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading opportunities…
      </div>
    );
  }

  if (error && rows.length === 0) {
    return (
      <EmptyState
        icon={<Briefcase className="size-5" />}
        title="Could not load opportunities"
        description={error}
        action={{ label: "Back to admin", href: "/admin" }}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Opportunities"
        description="Create listings by hand, or ingest official RSS, Greenhouse, Ashby, and Lever boards into a review queue. Ingested items stay drafts until you publish."
        action={
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={fetchNewListings} disabled={syncing || digesting}>
              {syncing ? "Fetching…" : "Fetch new listings"}
            </Button>
            {isOpportunitiesPublic() ? (
              <Button variant="outline" onClick={sendDigest} disabled={digesting || syncing}>
                {digesting ? "Sending digest…" : "Send weekly digest"}
              </Button>
            ) : null}
            <ButtonLink href="/admin/opportunities/discover" variant="outline">
              Discover
            </ButtonLink>
            <ButtonLink href="/admin/opportunities/sources" variant="outline">
              Sources
            </ButtonLink>
            <ButtonLink href="/admin/opportunities/new" className="bg-brand-orange text-white hover:bg-brand-orange/90">
              New opportunity
            </ButtonLink>
          </div>
        }
      />
      {!isOpportunitiesPublic() ? (
        <p className="mb-6 rounded-lg border border-brand-navy/15 bg-brand-surface px-4 py-3 text-sm text-muted-foreground">
          The public hub is private until go-live. Published listings stay in admin only — they are not on the site, in search, or announced.
        </p>
      ) : null}
      {overview ? (
        <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <OverviewCard label="Published" value={overview.published} />
          <OverviewCard label="Pending review" value={overview.review} />
          <OverviewCard label="Drafts" value={overview.draft} />
          <OverviewCard label="Ingested today" value={overview.ingested_today} />
        </div>
      ) : null}
      <div className="mb-4 flex gap-2">
        <Button variant={tab === "all" ? "default" : "outline"} size="sm" onClick={() => selectTab("all")}>
          All
        </Button>
        <Button variant={tab === "review" ? "default" : "outline"} size="sm" onClick={() => selectTab("review")}>
          Pending review{overview && overview.review > 0 ? ` (${overview.review})` : ""}
        </Button>
      </div>
      {syncing ? (
        <p className="mb-4 text-sm text-muted-foreground">
          Fetching official boards. New rows stay drafts until you publish.
        </p>
      ) : null}
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      {syncSummary ? (
        <p className="mb-4 text-sm text-muted-foreground">
          {syncSummary.sources === 0
            ? "No automated sources to sync. Add a board on Sources."
            : `Synced ${syncSummary.sources} source${syncSummary.sources === 1 ? "" : "s"} · ${syncSummary.created} new draft${syncSummary.created === 1 ? "" : "s"} · ${syncSummary.updated} updated · ${syncSummary.duplicates} already in queue${syncSummary.failed ? ` · ${syncSummary.failed} failed` : ""}. Nothing was published.`}
        </p>
      ) : null}
      {rows.length === 0 ? (
        <EmptyState
          icon={<Briefcase className="size-5" />}
          title={tab === "review" ? "Nothing waiting for review" : "No opportunities yet"}
          description={
            tab === "review"
              ? "Use Fetch new listings, or sync a board on Sources. Ingested items stay drafts until you publish."
              : "Add a role by hand, or fetch official boards. Nothing is public until you publish."
          }
          action={
            tab === "review"
              ? { label: "Manage sources", href: "/admin/opportunities/sources" }
              : { label: "New opportunity", href: "/admin/opportunities/new" }
          }
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Opportunity</TableHead>
                <TableHead>Type</TableHead>
                {tab === "review" ? <TableHead>Relevance</TableHead> : <TableHead>Deadline</TableHead>}
                <TableHead>Status</TableHead>
                <TableHead>{tab === "review" ? "Flags" : "Trust"}</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>
                    <div className="font-medium">{row.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {row.organization_name}
                      {row.source ? ` · ${row.source.name}` : ""}
                    </div>
                  </TableCell>
                  <TableCell>{TYPE_LABELS[row.opportunity_type]}</TableCell>
                  <TableCell className="whitespace-nowrap text-sm">
                    {tab === "review"
                      ? row.relevance_score != null
                        ? String(row.relevance_score)
                        : "—"
                      : formatDeadline(row.deadline)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={row.status === "published" ? "default" : "outline"}>
                      {STATUS_LABEL[row.status]}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {tab === "review" ? (
                      (row.risk_flags ?? []).length ? (
                        (row.risk_flags ?? []).map((flag) => flag.flag_type.replaceAll("_", " ")).join(", ")
                      ) : (
                        "None"
                      )
                    ) : (
                      <>
                        {row.trust_status.replaceAll("_", " ")}
                        {row.relevance_score != null ? ` · rel ${row.relevance_score}` : ""}
                      </>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      {tab === "review" ? (
                        <>
                          <Button
                            size="sm"
                            disabled={actingId === row.id}
                            onClick={() => act(row.id, "publish")}
                          >
                            {actingId === row.id ? "…" : "Publish"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={actingId === row.id}
                            onClick={() => act(row.id, "reject")}
                          >
                            Reject
                          </Button>
                        </>
                      ) : null}
                      <ButtonLink href={`/admin/opportunities/${row.id}`} variant="ghost" size="sm">
                        Edit
                      </ButtonLink>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function OverviewCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border bg-background px-4 py-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold tracking-tight">{value}</div>
    </div>
  );
}
