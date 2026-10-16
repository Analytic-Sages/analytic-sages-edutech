"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { ArrowDown, ArrowUp, Eye, EyeOff, Loader2, Save } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { MANAGED_COURSE_CARDS } from "@/lib/course-card-registry";
import { ApiError, listAdminCourseCardPlacements, saveCourseCardPlacements } from "@/lib/api";

const PAGE_OPTIONS = [
  { key: "insights", label: "Insights" },
  { key: "opportunities", label: "Opportunities" },
] as const;

type Placement = { card_key: string; visible: boolean };

export function AdminCourseCardsContent() {
  const [pageKey, setPageKey] = useState<string>("insights");
  const [placements, setPlacements] = useState<Placement[]>(
    MANAGED_COURSE_CARDS.map((card) => ({ card_key: card.key, visible: true })),
  );
  const [loadedPage, setLoadedPage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listAdminCourseCardPlacements()
      .then((rows) => {
        if (cancelled) return;
        setError(null);
        const current = rows
          .filter((row) => row.page_key === pageKey && row.section_key === "sidebar")
          .sort((a, b) => a.position - b.position)
          .map((row) => ({ card_key: row.card_key, visible: row.visible }));
        setPlacements(current.length ? current : MANAGED_COURSE_CARDS.map((card) => ({ card_key: card.key, visible: true })));
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load course card settings.");
      })
      .finally(() => { if (!cancelled) setLoadedPage(pageKey); });
    return () => { cancelled = true; };
  }, [pageKey]);

  const cardMap = useMemo(() => new Map(MANAGED_COURSE_CARDS.map((card) => [card.key, card])), []);

  function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= placements.length) return;
    setPlacements((current) => {
      const next = [...current];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
    setMessage(null);
  }

  function addCard(key: string) {
    if (!key || placements.some((item) => item.card_key === key)) return;
    setPlacements((current) => [...current, { card_key: key, visible: true }]);
    setMessage(null);
  }

  async function save() {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await saveCourseCardPlacements(pageKey, "sidebar", placements);
      setMessage("Course card order and visibility saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save course card settings.");
    } finally {
      setSaving(false);
    }
  }

  const available = MANAGED_COURSE_CARDS.filter((card) => !placements.some((item) => item.card_key === card.key));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Course Card Manager"
        description="Choose which course cards appear in each page sidebar, control visibility, and set their display order."
      />
      <div className="rounded-xl border bg-card p-5">
        <label htmlFor="placement-page" className="mb-2 block text-sm font-semibold">Page</label>
        <select id="placement-page" value={pageKey} onChange={(event) => setPageKey(event.target.value)} className="h-10 w-full max-w-sm rounded-md border bg-background px-3 text-sm">
          {PAGE_OPTIONS.map((page) => <option key={page.key} value={page.key}>{page.label} — sidebar</option>)}
        </select>
      </div>

      {loadedPage !== pageKey ? (
        <div className="flex items-center gap-2 py-10 text-muted-foreground"><Loader2 className="size-4 animate-spin" />Loading placements…</div>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-heading text-xl font-bold">Displayed cards</h2>
              <p className="text-sm text-muted-foreground">The top card appears first. Hidden cards stay in your configuration but do not appear publicly.</p>
            </div>
            <span className="text-sm text-muted-foreground">{placements.filter((item) => item.visible).length} visible · {placements.length} selected</span>
          </div>

          {placements.length === 0 ? <div className="rounded-xl border border-dashed p-8 text-sm text-muted-foreground">No cards selected for this page.</div> : null}
          {placements.map((placement, index) => {
            const card = cardMap.get(placement.card_key);
            if (!card) return null;
            return (
              <article key={placement.card_key} className="flex flex-col gap-4 rounded-xl border bg-card p-4 sm:flex-row sm:items-center">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted font-heading text-lg font-bold">{index + 1}</div>
                <div className="relative h-24 w-full shrink-0 overflow-hidden rounded-md bg-muted sm:w-36">
                  <Image src={card.image} alt="" fill sizes="(min-width: 640px) 144px, 100vw" className="object-cover" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold">{card.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{card.description}</p>
                  <p className="mt-2 text-xs text-muted-foreground">{card.duration} · {card.price}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Button type="button" variant="outline" size="icon" aria-label="Move card up" disabled={index === 0} onClick={() => move(index, -1)}><ArrowUp className="size-4" /></Button>
                  <Button type="button" variant="outline" size="icon" aria-label="Move card down" disabled={index === placements.length - 1} onClick={() => move(index, 1)}><ArrowDown className="size-4" /></Button>
                  <Button type="button" variant="outline" onClick={() => setPlacements((current) => current.map((item) => item.card_key === placement.card_key ? { ...item, visible: !item.visible } : item))}>
                    {placement.visible ? <><EyeOff className="mr-2 size-4" />Hide</> : <><Eye className="mr-2 size-4" />Show</>}
                  </Button>
                  <Button type="button" variant="ghost" onClick={() => setPlacements((current) => current.filter((item) => item.card_key !== placement.card_key))} disabled={placements.length === 1}>Remove</Button>
                </div>
              </article>
            );
          })}

          <div className="flex flex-col gap-3 rounded-xl border border-dashed p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-semibold">Add another course card</h3>
              <p className="text-sm text-muted-foreground">Select a card to include it in this page section.</p>
            </div>
            <select aria-label="Add course card" defaultValue="" onChange={(event) => { addCard(event.target.value); event.target.value = ""; }} className="h-10 w-full rounded-md border bg-background px-3 text-sm sm:max-w-sm">
              <option value="">Choose a course…</option>
              {available.map((card) => <option key={card.key} value={card.key}>{card.title}</option>)}
            </select>
          </div>

          {error ? <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{error}</p> : null}
          {message ? <p role="status" className="rounded-lg border border-green-600/20 bg-green-600/5 p-3 text-sm text-green-700">{message}</p> : null}
          <div className="flex justify-end">
            <Button onClick={save} disabled={saving}><Save className="mr-2 size-4" />{saving ? "Saving…" : "Save placements"}</Button>
          </div>
        </div>
      )}
    </div>
  );
}
