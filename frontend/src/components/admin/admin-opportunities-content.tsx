"use client";

import { useEffect, useMemo, useState } from "react";
import { Briefcase, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Checkbox } from "@/components/ui/checkbox";
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
  bulkPublishAdminOpportunities,
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

function isBulkEligible(row: OpportunityAdmin): boolean {
  if (row.status !== "draft") return false;
  if (row.trust_status === "high_risk") return false;
  if (!row.application_url?.trim()) return false;
  if (!row.description?.trim()) return false;
  if (row.deadline) {
    const due = new Date(row.deadline).getTime();
    if (!Number.isNaN(due) && due < Date.now()) return false;
  }
  return true;
}

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
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkPublishing, setBulkPublishing] = useState(false);
  const [bulkSummary, setBulkSummary] = useState<string | null>(null);

  const eligibleIds = useMemo(
    () => (tab === "review" ? rows.filter(isBulkEligible).map((row) => row.id) : []),
    [rows, tab],
  );
  const selectedEligibleCount = useMemo(
    () => eligibleIds.filter((id) => selected.has(id)).length,
    [eligibleIds, selected],
  );
  const allEligibleSelected =
    eligibleIds.length > 0 && eligibleIds.every((id) => selected.has(id));

  function load(nextTab: Tab = tab) {
    return Promise.all([
      getAdminOpportunities(nextTab === "review" ? { review: true } : {}),
      getAdminOpportunityOverview(),
    ]).then(([list, counts]) => {
      setRows(list.items);
      setOverview(counts);
      setSelected(new Set());
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
    setBulkSummary(null);
    setLoading(true);
    setTab(next);
  }

  function toggleRow(id: string, checked: boolean) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function toggleSelectAllEligible(checked: boolean) {
    setSelected((prev) => {
      const next = new Set(prev);
      for (const id of eligibleIds) {
        if (checked) next.add(id);
        else next.delete(id);
      }
      return next;
    });
  }

  async function fetchNewListings() {
    setSyncing(true);
    setError(null);
    setSyncSummary(null);
    setBulkSummary(null);
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
    setBulkSummary(null);
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

  async function publishSelected() {
    const ids = eligibleIds.filter((id) => selected.has(id));
    if (ids.length === 0) return;
    const confirmed = window.confirm(
      `Publish ${ids.length} listing${ids.length === 1 ? "" : "s"}?\n\nHigh-risk and incomplete rows are skipped. Per-row Publish / Reject still works.`,
    );
    if (!confirmed) return;
    setBulkPublishing(true);
    setError(null);
    setBulkSummary(null);
    try {
      const result = await bulkPublishAdminOpportunities(ids);
      const skipNote =
        result.skipped > 0
          ? ` Skipped ${result.skipped}: ${result.skipped_items
              .slice(0, 3)
              .map((item) => `${item.title} (${item.reason})`)
              .join("; ")}${result.skipped_items.length > 3 ? "…" : ""}`
          : "";
      setBulkSummary(`Published ${result.published}.${skipNote}`);
      await load(tab);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not bulk publish.");
    } finally {
      setBulkPublishing(false);
    }
  }

  async function publishAllEligible() {
    if (eligibleIds.length === 0) return;
    const confirmed = window.confirm(
      `Publish all ${eligibleIds.length} eligible listing${eligibleIds.length === 1 ? "" : "s"} on this page?\n\nHigh-risk and incomplete rows stay in the queue.`,
    );
    if (!confirmed) return;
    setSelected(new Set(eligibleIds));
    setBulkPublishing(true);
    setError(null);
    setBulkSummary(null);
    try {
      const result = await bulkPublishAdminOpportunities(eligibleIds);
      const skipNote =
        result.skipped > 0
          ? ` Skipped ${result.skipped}: ${result.skipped_items
              .slice(0, 3)
              .map((item) => `${item.title} (${item.reason})`)
              .join("; ")}${result.skipped_items.length > 3 ? "…" : ""}`
          : "";
      setBulkSummary(`Published ${result.published}.${skipNote}`);
      await load(tab);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not bulk publish.");
    } finally {
      setBulkPublishing(false);
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
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Button variant={tab === "all" ? "default" : "outline"} size="sm" onClick={() => selectTab("all")}>
          All
        </Button>
        <Button variant={tab === "review" ? "default" : "outline"} size="sm" onClick={() => selectTab("review")}>
          Pending review{overview && overview.review > 0 ? ` (${overview.review})` : ""}
        </Button>
        {tab === "review" && rows.length > 0 ? (
          <>
            <Button
              size="sm"
              variant="outline"
              disabled={bulkPublishing || selectedEligibleCount === 0}
              onClick={() => void publishSelected()}
            >
              {bulkPublishing
                ? "Publishing…"
                : `Publish selected${selectedEligibleCount ? ` (${selectedEligibleCount})` : ""}`}
            </Button>
            <Button
              size="sm"
              disabled={bulkPublishing || eligibleIds.length === 0}
              onClick={() => void publishAllEligible()}
            >
              {bulkPublishing ? "Publishing…" : `Publish all eligible (${eligibleIds.length})`}
            </Button>
          </>
        ) : null}
      </div>
      {tab === "review" && rows.length > 0 ? (
        <p className="mb-4 text-sm text-muted-foreground">
          Bulk publish skips high-risk and incomplete rows. Use per-row Publish for those.
        </p>
      ) : null}
      {syncing ? (
        <p className="mb-4 text-sm text-muted-foreground">
          Fetching official boards. New rows stay drafts until you publish.
        </p>
      ) : null}
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      {bulkSummary ? <p className="mb-4 text-sm text-muted-foreground">{bulkSummary}</p> : null}
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
                {tab === "review" ? (
                  <TableHead className="w-10">
                    <Checkbox
                      checked={allEligibleSelected}
                      disabled={eligibleIds.length === 0 || bulkPublishing}
                      onCheckedChange={(value) => toggleSelectAllEligible(value === true)}
                      aria-label="Select all eligible"
                    />
                  </TableHead>
                ) : null}
                <TableHead>Opportunity</TableHead>
                <TableHead>Type</TableHead>
                {tab === "review" ? <TableHead>Relevance</TableHead> : <TableHead>Deadline</TableHead>}
                <TableHead>Status</TableHead>
                <TableHead>{tab === "review" ? "Flags" : "Trust"}</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => {
                const eligible = isBulkEligible(row);
                return (
                  <TableRow key={row.id}>
                    {tab === "review" ? (
                      <TableCell>
                        <Checkbox
                          checked={selected.has(row.id)}
                          disabled={!eligible || bulkPublishing}
                          onCheckedChange={(value) => toggleRow(row.id, value === true)}
                          aria-label={`Select ${row.title}`}
                        />
                      </TableCell>
                    ) : null}
                    <TableCell>
                      <div className="font-medium">{row.title}</div>
                      <div className="text-xs text-muted-foreground">
                        {row.organization_name}
                        {row.source ? ` · ${row.source.name}` : ""}
                        {tab === "review" && !eligible ? " · not bulk-eligible" : ""}
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
                              disabled={actingId === row.id || bulkPublishing}
                              onClick={() => act(row.id, "publish")}
                            >
                              {actingId === row.id ? "…" : "Publish"}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={actingId === row.id || bulkPublishing}
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
                );
              })}
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
