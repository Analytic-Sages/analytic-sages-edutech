"use client";

import { useEffect, useState } from "react";
import { Rss, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";
import {
  createAdminOpportunitySource,
  listAdminOpportunitySources,
  syncAdminOpportunitySource,
  updateAdminOpportunitySource,
  type OpportunitySourceAdmin,
} from "@/lib/opportunities";

type ConnectorType = "rss" | "greenhouse" | "ashby" | "lever";

const EMPTY_FORM = {
  name: "",
  website_url: "",
  connector_type: "rss" as ConnectorType,
  feed_url: "",
  board_token: "",
  trust_level: "medium" as "high" | "medium" | "low",
  automation_enabled: true,
  auto_publish_allowed: false,
};

export function AdminOpportunitySourcesContent() {
  const [rows, setRows] = useState<OpportunitySourceAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  function load() {
    return listAdminOpportunitySources().then((data) => setRows(data.items));
  }

  useEffect(() => {
    let cancelled = false;
    load()
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load sources.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createAdminOpportunitySource({
        name: form.name,
        website_url: form.website_url || null,
        trust_level: form.trust_level,
        automation_enabled: form.automation_enabled,
        auto_publish_allowed: form.auto_publish_allowed,
        connector_type: form.connector_type,
        config:
          form.connector_type === "rss"
            ? { feed_url: form.feed_url }
            : { board_token: form.board_token },
      });
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create source.");
    } finally {
      setSaving(false);
    }
  }

  async function runSync(id: string) {
    setSyncingId(id);
    setError(null);
    try {
      const run = await syncAdminOpportunitySource(id);
      await load();
      if (run.status === "failed") {
        setError(run.error_message || "Sync failed.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not run sync.");
    } finally {
      setSyncingId(null);
    }
  }

  async function toggle(source: OpportunitySourceAdmin, field: "is_active" | "automation_enabled" | "auto_publish_allowed") {
    setError(null);
    try {
      await updateAdminOpportunitySource(source.id, { [field]: !source[field] });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update source.");
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading sources…
      </div>
    );
  }

  const connectors = rows.filter((row) =>
    ["rss", "greenhouse", "ashby", "lever"].includes(row.connector_type),
  );

  return (
    <div>
      <PageHeader
        title="Opportunity sources"
        description="Company career boards (Greenhouse, Ashby, Lever, RSS) for jobs. Use Discover for internships, fellowships, hackathons, grants, bounties, and research."
        action={
          <div className="flex flex-wrap gap-2">
            <ButtonLink href="/admin/opportunities/discover" variant="outline">
              Discover
            </ButtonLink>
            <ButtonLink href="/admin/opportunities" variant="outline">
              Back to opportunities
            </ButtonLink>
          </div>
        }
      />
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}

      <form onSubmit={onCreate} className="mb-8 grid gap-4 rounded-xl border p-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <h2 className="text-sm font-semibold">Add a source</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Auto-publish stays off unless you turn it on. Even then, only high-trust, high-relevance items with no serious risk flags can go live.
          </p>
        </div>
        <div>
          <Label htmlFor="source-name">Name</Label>
          <Input
            id="source-name"
            required
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="Company careers RSS"
          />
        </div>
        <div>
          <Label htmlFor="source-website">Website</Label>
          <Input
            id="source-website"
            value={form.website_url}
            onChange={(event) => setForm({ ...form, website_url: event.target.value })}
            placeholder="https://example.com"
          />
        </div>
        <div>
          <Label htmlFor="source-connector">Connector</Label>
          <select
            id="source-connector"
            className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
            value={form.connector_type}
            onChange={(event) => setForm({ ...form, connector_type: event.target.value as ConnectorType })}
          >
            <option value="rss">RSS / Atom feed</option>
            <option value="greenhouse">Greenhouse public board</option>
            <option value="ashby">Ashby public board</option>
            <option value="lever">Lever public board</option>
          </select>
        </div>
        <div>
          <Label htmlFor="source-trust">Trust level</Label>
          <select
            id="source-trust"
            className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
            value={form.trust_level}
            onChange={(event) => setForm({ ...form, trust_level: event.target.value as "high" | "medium" | "low" })}
          >
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        {form.connector_type === "rss" ? (
          <div className="md:col-span-2">
            <Label htmlFor="source-feed">Feed URL</Label>
            <Input
              id="source-feed"
              required
              value={form.feed_url}
              onChange={(event) => setForm({ ...form, feed_url: event.target.value })}
              placeholder="https://example.com/jobs.rss"
            />
          </div>
        ) : (
          <div className="md:col-span-2">
            <Label htmlFor="source-board">
              {form.connector_type === "ashby"
                ? "Ashby board token"
                : form.connector_type === "lever"
                  ? "Lever site token"
                  : "Greenhouse board token"}
            </Label>
            <Input
              id="source-board"
              required
              value={form.board_token}
              onChange={(event) => setForm({ ...form, board_token: event.target.value })}
              placeholder={
                form.connector_type === "ashby" ? "dune" : form.connector_type === "lever" ? "company-slug" : "nansen"
              }
            />
            <p className="mt-1 text-xs text-muted-foreground">
              {form.connector_type === "ashby"
                ? "Public job board API only — no Ashby API key. Token is the slug in jobs.ashbyhq.com/…"
                : form.connector_type === "lever"
                  ? "Public postings API only — no Lever API key. Token is the slug in jobs.lever.co/…"
                  : "Public boards API only — no Greenhouse API key. Token is the board slug in boards.greenhouse.io/…"}
            </p>
          </div>
        )}
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.automation_enabled}
            onChange={(event) => setForm({ ...form, automation_enabled: event.target.checked })}
          />
          Enable for scheduled / token sync
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.auto_publish_allowed}
            onChange={(event) => setForm({ ...form, auto_publish_allowed: event.target.checked })}
          />
          Allow auto-publish (strict gates still apply)
        </label>
        <div className="md:col-span-2">
          <Button type="submit" disabled={saving} className="bg-brand-orange text-white hover:bg-brand-orange/90">
            {saving ? "Saving…" : "Add source"}
          </Button>
        </div>
      </form>

      {connectors.length === 0 ? (
        <EmptyState
          icon={<Rss className="size-5" />}
          title="No ingest sources yet"
          description="Nansen, Dune, and TRM Labs are seeded on API startup. You can also add another official Greenhouse or Ashby board."
        />
      ) : (
        <div className="space-y-4">
          <div className="overflow-x-auto rounded-xl border">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Source</th>
                  <th className="px-3 py-2 font-medium">Last sync</th>
                  <th className="px-3 py-2 font-medium text-right">Found</th>
                  <th className="px-3 py-2 font-medium text-right">Published</th>
                  <th className="px-3 py-2 font-medium text-right">Review</th>
                  <th className="px-3 py-2 font-medium text-right">Rejected</th>
                </tr>
              </thead>
              <tbody>
                {connectors.map((source) => (
                  <tr key={`stats-${source.id}`} className="border-b last:border-0">
                    <td className="px-3 py-2">{source.name}</td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {source.last_checked_at ? new Date(source.last_checked_at).toLocaleString() : "Never"}
                      {source.last_error ? " · error" : ""}
                    </td>
                    <td className="px-3 py-2 text-right">{source.latest_sync?.found ?? "—"}</td>
                    <td className="px-3 py-2 text-right">{source.published_count ?? 0}</td>
                    <td className="px-3 py-2 text-right">{source.review_count ?? 0}</td>
                    <td className="px-3 py-2 text-right">{source.rejected_count ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {connectors.map((source) => (
            <div key={source.id} className="rounded-xl border p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-medium">{source.name}</h3>
                    <Badge variant="outline">{source.connector_type}</Badge>
                    <Badge variant={source.is_active ? "default" : "outline"}>
                      {source.is_active ? "Active" : "Disabled"}
                    </Badge>
                    <Badge variant="outline">{source.trust_level} trust</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {source.connector_type === "rss"
                      ? source.config.feed_url
                      : `Board: ${source.config.board_token || "—"}`}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Last sync: {source.last_checked_at ? new Date(source.last_checked_at).toLocaleString() : "Never"}
                    {source.latest_sync
                      ? ` · ${source.latest_sync.status} · found ${source.latest_sync.found}, created ${source.latest_sync.created}, rejected ${source.latest_sync.rejected}`
                      : ""}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Published {source.published_count ?? 0} · Pending review {source.review_count ?? 0} · Rejected{" "}
                    {source.rejected_count ?? 0}
                  </p>
                  {source.last_error ? (
                    <p className="mt-1 text-xs text-destructive">{source.last_error}</p>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    onClick={() => runSync(source.id)}
                    disabled={syncingId === source.id || source.connector_type === "manual"}
                  >
                    {syncingId === source.id ? "Syncing…" : "Run sync"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => toggle(source, "is_active")}>
                    {source.is_active ? "Disable" : "Enable"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => toggle(source, "auto_publish_allowed")}>
                    Auto-publish {source.auto_publish_allowed ? "on" : "off"}
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
