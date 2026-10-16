"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Eye, EyeOff, Loader2, Plus, Save, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ApiError, getAdminCoursePlacements, getCoursePlacementOptions, saveAdminCoursePlacements, type CoursePlacementOption, type CoursePlacementRow } from "@/lib/api";

const PAGES = [
  { value: "home", label: "Homepage" },
  { value: "courses", label: "Course catalogue" },
  { value: "instructor-led", label: "Instructor-led programmes" },
  { value: "programs", label: "Programmes" },
  { value: "opportunities", label: "Opportunities" },
  { value: "insights", label: "Insights" },
];

export function AdminCoursePlacementsContent() {
  const [options, setOptions] = useState<CoursePlacementOption[]>([]);
  const [rows, setRows] = useState<CoursePlacementRow[]>([]);
  const [page, setPage] = useState("home");
  const [section, setSection] = useState("main");
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    getCoursePlacementOptions()
      .then(setOptions)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Could not load course options."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    let cancelled = false;
    getAdminCoursePlacements(page, section)
      .then((items) => { if (!cancelled) setRows(items); })
      .catch((err) => { if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load this placement."); });
    return () => { cancelled = true; };
  }, [page, section]);

  const available = useMemo(
    () => options.filter((course) => !rows.some((row) => row.course_id === course.id)),
    [options, rows]
  );

  function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= rows.length) return;
    const next = [...rows];
    [next[index], next[target]] = [next[target], next[index]];
    setRows(next.map((row, sort_order) => ({ ...row, sort_order })));
  }

  function addCourse() {
    const course = options.find((item) => item.id === selected);
    if (!course) return;
    setRows((current) => [...current, {
      ...course,
      course_id: course.id,
      page_key: page,
      section_key: section,
      sort_order: current.length,
      visible: true,
    }]);
    setSelected("");
    setMessage(null);
  }

  async function save() {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const saved = await saveAdminCoursePlacements(page, section, rows.map((row) => ({
        course_id: row.course_id,
        visible: row.visible,
      })));
      setRows(saved);
      setMessage("Course card placements saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save course placements.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="flex min-h-[35vh] items-center justify-center gap-2 text-muted-foreground"><Loader2 className="size-5 animate-spin" />Loading placement manager…</div>;

  return (
    <div className="space-y-6">
      <PageHeader title="Course Card Placements" description="Choose the courses shown in each page section, control visibility, and arrange their order. A course can appear in multiple places without duplicating its course record." />
      <div className="grid gap-4 rounded-xl border bg-card p-5 md:grid-cols-3">
        <label className="space-y-2 text-sm font-medium">Page
          <select className="w-full rounded-md border bg-background px-3 py-2 font-normal" value={page} onChange={(event) => setPage(event.target.value)}>
            {PAGES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </label>
        <label className="space-y-2 text-sm font-medium">Section key
          <input className="w-full rounded-md border bg-background px-3 py-2 font-normal" value={section} onChange={(event) => setSection(event.target.value.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "-"))} placeholder="main" maxLength={80} />
        </label>
        <div className="flex items-end gap-2">
          <select aria-label="Course to add" className="min-w-0 flex-1 rounded-md border bg-background px-3 py-2 text-sm" value={selected} onChange={(event) => setSelected(event.target.value)}>
            <option value="">Add a course…</option>
            {available.map((item) => <option key={item.id} value={item.id}>{item.title}{item.published ? "" : " (draft)"}</option>)}
          </select>
          <button type="button" onClick={addCourse} disabled={!selected} className="inline-flex items-center gap-1 rounded-md bg-brand-orange px-3 py-2 text-sm font-medium text-white disabled:opacity-50"><Plus className="size-4" />Add</button>
        </div>
      </div>
      {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{error}</p>}
      {message && <p role="status" className="rounded-md border border-emerald-500/30 p-3 text-sm text-emerald-700">{message}</p>}
      <div className="rounded-xl border">
        <div className="flex items-center justify-between border-b p-4">
          <div><h2 className="font-semibold">{PAGES.find((item) => item.value === page)?.label ?? page} / {section}</h2><p className="text-sm text-muted-foreground">{rows.length} course card{rows.length === 1 ? "" : "s"} · order is top to bottom</p></div>
          <button type="button" onClick={save} disabled={saving} className="inline-flex items-center gap-2 rounded-md bg-brand-orange px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}Save changes</button>
        </div>
        {rows.length === 0 ? <div className="p-10 text-center"><p className="font-medium">No course cards configured for this section.</p><p className="mt-1 text-sm text-muted-foreground">Add one or more courses above, then save.</p></div> : (
          <ol className="divide-y">
            {rows.map((row, index) => <li key={row.course_id} className="flex items-center gap-3 p-4">
              <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold">{index + 1}</span>
              {row.thumbnail ? <><span className="sr-only">Course thumbnail</span>{/* eslint-disable-next-line @next/next/no-img-element */}<img src={row.thumbnail} alt="" className="size-14 rounded-md border object-cover" /></> : <div className="flex size-14 items-center justify-center rounded-md border text-xs text-muted-foreground">Course</div>}
              <div className="min-w-0 flex-1"><p className="truncate font-medium">{row.title}</p><p className="text-xs text-muted-foreground">{row.slug} · {row.delivery_type} · {row.published ? "Published" : "Draft"}</p></div>
              <button type="button" title={row.visible ? "Hide card" : "Show card"} aria-label={row.visible ? `Hide ${row.title}` : `Show ${row.title}`} onClick={() => setRows((current) => current.map((item) => item.course_id === row.course_id ? { ...item, visible: !item.visible } : item))} className="rounded-md border p-2 text-muted-foreground hover:bg-muted">{row.visible ? <Eye className="size-4" /> : <EyeOff className="size-4" />}</button>
              <button type="button" title="Move up" aria-label={`Move ${row.title} up`} disabled={index === 0} onClick={() => move(index, -1)} className="rounded-md border p-2 disabled:opacity-30"><ArrowUp className="size-4" /></button>
              <button type="button" title="Move down" aria-label={`Move ${row.title} down`} disabled={index === rows.length - 1} onClick={() => move(index, 1)} className="rounded-md border p-2 disabled:opacity-30"><ArrowDown className="size-4" /></button>
              <button type="button" title="Remove from section" aria-label={`Remove ${row.title}`} onClick={() => setRows((current) => current.filter((item) => item.course_id !== row.course_id).map((item, sort_order) => ({ ...item, sort_order })))} className="rounded-md border p-2 text-destructive hover:bg-destructive/5"><Trash2 className="size-4" /></button>
            </li>)}
          </ol>
        )}
      </div>
      <p className="text-sm text-muted-foreground">Saving replaces only this page/section&apos;s placement list. It never deletes a course. Draft courses can be staged here, but the public placement endpoint only returns published courses.</p>
    </div>
  );
}
