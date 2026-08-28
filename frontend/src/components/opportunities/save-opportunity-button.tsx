"use client";

import { useEffect, useState } from "react";
import { Bookmark, BookmarkCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { useIsSignedIn } from "@/hooks/use-access-token";
import { ApiError } from "@/lib/api";
import {
  markOpportunityApplied,
  saveOpportunity,
  unsaveOpportunity,
} from "@/lib/opportunities";

type Props = {
  opportunityId: string;
  initiallySaved?: boolean;
  initiallyApplied?: boolean;
};

export function SaveOpportunityButton({ opportunityId, initiallySaved, initiallyApplied }: Props) {
  const signedIn = useIsSignedIn();
  const [saved, setSaved] = useState(Boolean(initiallySaved));
  const [applied, setApplied] = useState(Boolean(initiallyApplied));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSaved(Boolean(initiallySaved));
    setApplied(Boolean(initiallyApplied));
  }, [initiallySaved, initiallyApplied]);

  if (!signedIn) {
    const next = typeof window === "undefined" ? "/opportunities" : window.location.pathname;
    return (
      <ButtonLink href={`/login?next=${encodeURIComponent(next)}`} variant="outline" className="w-full">
        Sign in to save
      </ButtonLink>
    );
  }

  async function toggle() {
    setBusy(true);
    setError(null);
    try {
      if (saved) {
        await unsaveOpportunity(opportunityId);
        setSaved(false);
        setApplied(false);
      } else {
        await saveOpportunity(opportunityId);
        setSaved(true);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update saved list.");
    } finally {
      setBusy(false);
    }
  }

  async function appliedNow() {
    setBusy(true);
    setError(null);
    try {
      await markOpportunityApplied(opportunityId);
      setSaved(true);
      setApplied(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not mark as applied.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <Button variant="outline" className="w-full" onClick={toggle} disabled={busy}>
        {busy ? <Loader2 className="mr-2 size-4 animate-spin" /> : saved ? <BookmarkCheck className="mr-2 size-4" /> : <Bookmark className="mr-2 size-4" />}
        {saved ? "Saved" : "Save opportunity"}
      </Button>
      <Button variant="ghost" className="w-full" onClick={appliedNow} disabled={busy || applied}>
        {applied ? "Marked applied" : "I applied on the official site"}
      </Button>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
