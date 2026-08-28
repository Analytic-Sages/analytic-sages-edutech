"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";
import {
  DISCOVERY_TYPES,
  TYPE_LABELS,
  discoverAdminOpportunities,
  importAdminDiscoveredOpportunities,
  reclassifyAdminOpportunityTypes,
  type OpportunityDiscoverCandidate,
  type OpportunityType,
} from "@/lib/opportunities";

export function AdminOpportunityDiscoverContent() {
  const [types, setTypes] = useState<OpportunityType[]>([...DISCOVERY_TYPES]);
  const [query, setQuery] = useState("");
  const [candidates, setCandidates] = useState<OpportunityDiscoverCandidate[]>([]);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [notes, setNotes] = useState<string | null>(null);
  const [grounded, setGrounded] = useState<boolean | null>(null);
  const [provider, setProvider] = useState<string | null>(null);
  const [typesUpdated, setTypesUpdated] = useState(0);
  const [dropped, setDropped] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [importing, setImporting] = useState(false);
  const [reclassifying, setReclassifying] = useState(false);
  const [importedCount, setImportedCount] = useState<number | null>(null);

  function toggleType(type: OpportunityType) {
    setTypes((current) =>
      current.includes(type) ? current.filter((item) => item !== type) : [...current, type]
    );
  }

  async function search() {
    setSearching(true);
    setError(null);
    setImportedCount(null);
    try {
      const result = await discoverAdminOpportunities(types.length ? types : DISCOVERY_TYPES, query);
      setCandidates(result.candidates);
      setSelected(
        Object.fromEntries(
          result.candidates
            .filter((row) => !row.already_imported)
            .map((row) => [row.application_url, true])
        )
      );
      setNotes(result.notes);
      setGrounded(result.grounded);
      setProvider(result.provider);
      setTypesUpdated(result.types_updated);
      setDropped(result.dropped);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Discovery is not available.");
      setCandidates([]);
      setNotes(null);
      setGrounded(null);
      setProvider(null);
    } finally {
      setSearching(false);
    }
  }

  async function reclassify() {
    setReclassifying(true);
    setError(null);
    try {
      const result = await reclassifyAdminOpportunityTypes();
      setTypesUpdated(result.updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not reclassify drafts.");
    } finally {
      setReclassifying(false);
    }
  }

  async function importSelected() {
    const rows = candidates.filter((row) => selected[row.application_url] && !row.already_imported);
    if (!rows.length) return;
    setImporting(true);
    setError(null);
    try {
      const result = await importAdminDiscoveredOpportunities(rows);
      setImportedCount(result.imported);
      setCandidates((current) =>
        current.map((row) =>
          rows.some((item) => item.application_url === row.application_url)
            ? { ...row, already_imported: true }
            : row
        )
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not import drafts.");
    } finally {
      setImporting(false);
    }
  }

  const selectedCount = candidates.filter((row) => selected[row.application_url] && !row.already_imported).length;

  return (
    <div>
      <PageHeader
        title="Discover opportunities"
        description="Find internships, fellowships, hackathons, grants, bounties, and research listings. Everything lands as a draft for review. Nothing is published automatically."
        action={
          <ButtonLink href="/admin/opportunities" variant="outline">
            Review queue
          </ButtonLink>
        }
      />

      <div className="mb-6 rounded-xl border bg-background p-5">
        <p className="text-sm font-medium">Types to find</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {DISCOVERY_TYPES.map((type) => {
            const on = types.includes(type);
            return (
              <button
                key={type}
                type="button"
                onClick={() => toggleType(type)}
                className={
                  on
                    ? "rounded-full bg-brand-navy px-3 py-1 text-sm text-white"
                    : "rounded-full border px-3 py-1 text-sm text-muted-foreground"
                }
              >
                {TYPE_LABELS[type]}
              </button>
            );
          })}
        </div>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Optional focus, e.g. SQL internships or ETHGlobal"
          />
          <Button onClick={search} disabled={searching || types.length === 0}>
            {searching ? "Searching…" : "Find listings"}
          </Button>
          <Button variant="outline" onClick={reclassify} disabled={reclassifying}>
            {reclassifying ? "Fixing types…" : "Fix draft types"}
          </Button>
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          Uses OpenAI first, then Gemini if OpenAI is missing or fails. Official https pages
          only — LinkedIn, Indeed, and Web3.career are blocked.
        </p>
      </div>

      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      {typesUpdated ? (
        <p className="mb-4 text-sm text-muted-foreground">Reclassified {typesUpdated} draft listings.</p>
      ) : null}
      {importedCount != null ? (
        <p className="mb-4 text-sm text-muted-foreground">
          Imported {importedCount} drafts. Open Pending review to publish.
        </p>
      ) : null}
      {notes ? <p className="mb-4 text-sm text-amber-700">{notes}</p> : null}
      {grounded === true ? (
        <p className="mb-4 text-sm text-muted-foreground">
          Search used live web results{provider ? ` via ${provider === "gemini" ? "Gemini" : "OpenAI"}` : ""}.
          Still open each official URL before you publish.
        </p>
      ) : null}

      {searching ? (
        <div className="flex min-h-[20vh] items-center justify-center gap-2 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Searching official programs…
        </div>
      ) : null}

      {!searching && candidates.length === 0 && !error ? (
        <EmptyState
          icon={<Search className="size-5" />}
          title="No candidates yet"
          description="Choose types and search. Company job boards stay on Sources. This inbox is for internships, fellowships, hackathons, grants, bounties, and research."
        />
      ) : null}

      {candidates.length ? (
        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <p className="text-sm text-muted-foreground">
              {candidates.length} candidates{dropped ? ` · ${dropped} dropped` : ""}
            </p>
            <Button onClick={importSelected} disabled={importing || selectedCount === 0}>
              {importing ? "Importing…" : `Import ${selectedCount} as drafts`}
            </Button>
          </div>
          <ul className="space-y-3">
            {candidates.map((row) => (
              <li key={row.application_url} className="rounded-xl border bg-background p-4">
                <label className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    className="mt-1"
                    disabled={row.already_imported}
                    checked={row.already_imported || Boolean(selected[row.application_url])}
                    onChange={(event) =>
                      setSelected((current) => ({ ...current, [row.application_url]: event.target.checked }))
                    }
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium">{row.title}</p>
                      <Badge variant="outline">{TYPE_LABELS[row.opportunity_type]}</Badge>
                      {row.already_imported ? <Badge>Already a draft</Badge> : null}
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {row.organization_name}
                      {row.source_host ? ` · ${row.source_host}` : ""}
                    </p>
                    {row.why_relevant ? <p className="mt-2 text-sm">{row.why_relevant}</p> : null}
                    <a
                      href={row.application_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-sm text-brand-navy underline"
                    >
                      Open official page
                    </a>
                  </div>
                </label>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
