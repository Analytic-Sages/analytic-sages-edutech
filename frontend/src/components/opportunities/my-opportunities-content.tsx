"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Bookmark, Loader2 } from "lucide-react";
import { OpportunityRow } from "@/components/opportunities/opportunity-card";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import {
  getMyOpportunityInterests,
  getOpportunityFilters,
  listMyOpportunities,
  updateMyOpportunityInterests,
  type CareerPathPublic,
  type OpportunitySaveItem,
} from "@/lib/opportunities";

type Bucket = "saved" | "applied" | "closed";

export function MyOpportunitiesContent() {
  const [bucket, setBucket] = useState<Bucket>("saved");
  const [rows, setRows] = useState<OpportunitySaveItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paths, setPaths] = useState<CareerPathPublic[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [savingInterests, setSavingInterests] = useState(false);

  useEffect(() => {
    getOpportunityFilters()
      .then((data) => setPaths(data.career_paths.map((item) => ({ id: item.id, name: item.name, slug: item.slug, description: "" }))))
      .catch(() => setPaths([]));
    getMyOpportunityInterests()
      .then((data) => setSelected(data.career_paths.map((item) => item.id)))
      .catch(() => setSelected([]));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listMyOpportunities(bucket)
      .then((data) => {
        if (cancelled) return;
        setRows(data.items);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.detail : "Could not load saved opportunities.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [bucket]);

  async function saveInterests() {
    setSavingInterests(true);
    try {
      const data = await updateMyOpportunityInterests(selected);
      setSelected(data.career_paths.map((item) => item.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save career interests.");
    } finally {
      setSavingInterests(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="My opportunities"
        description="Saved listings, applications you marked yourself, and roles that have closed. Matching uses the career paths you choose below."
      />

      <section className="mb-8 rounded-xl border p-4">
        <h2 className="text-sm font-semibold">Career interests</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Used to sort the public hub with “For you”. This is not a job application profile.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {paths.map((path) => {
            const on = selected.includes(path.id);
            return (
              <button
                key={path.id}
                type="button"
                onClick={() =>
                  setSelected((current) =>
                    on ? current.filter((id) => id !== path.id) : [...current, path.id],
                  )
                }
                className={`rounded-full border px-3 py-1 text-xs ${on ? "border-brand-orange bg-brand-orange text-white" : "border-input"}`}
              >
                {path.name}
              </button>
            );
          })}
        </div>
        <Button size="sm" className="mt-3" onClick={saveInterests} disabled={savingInterests}>
          {savingInterests ? "Saving…" : "Save interests"}
        </Button>
      </section>

      <div className="mb-4 flex flex-wrap gap-2">
        {(["saved", "applied", "closed"] as Bucket[]).map((item) => (
          <Button key={item} size="sm" variant={bucket === item ? "default" : "outline"} onClick={() => setBucket(item)}>
            {item === "saved" ? "Saved" : item === "applied" ? "Applied" : "Closed"}
          </Button>
        ))}
      </div>

      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center gap-2 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Loading…
        </div>
      ) : rows.length === 0 ? (
        <EmptyState
          icon={<Bookmark className="size-5" />}
          title={bucket === "saved" ? "Nothing saved yet" : bucket === "applied" ? "No applications marked" : "Nothing closed"}
          description="Save a listing from an opportunity page. Applied only means you marked that you applied on the official site."
        />
      ) : (
        <div>
          {rows.map((row) => (
            <OpportunityRow key={row.id} opportunity={row.opportunity} />
          ))}
        </div>
      )}
      <p className="mt-6 text-sm text-muted-foreground">
        Browse the public hub: <Link href="/opportunities" className="text-brand-orange">Opportunities</Link>
      </p>
    </div>
  );
}
