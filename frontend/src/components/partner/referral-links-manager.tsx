"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  ApiError,
  completePartnerOnboarding,
  createPartnerReferralLink,
  getPartnerReferralLinkTargets,
  getPartnerReferralLinks,
  getReferralProgramGuide,
  patchPartnerReferralLink,
  type ReferralLink,
  type ReferralLinkTargets,
  type ReferralProgramGuide,
} from "@/lib/api";

export function ReferralLinksManager({
  onboarding = false,
  onActivated,
}: {
  onboarding?: boolean;
  onActivated?: () => void | Promise<void>;
}) {
  const [links, setLinks] = useState<ReferralLink[]>([]);
  const [targets, setTargets] = useState<ReferralLinkTargets>({ courses: [], programmes: [] });
  const [guide, setGuide] = useState<ReferralProgramGuide | null>(null);
  const [target, setTarget] = useState("");
  const [campaign, setCampaign] = useState("");
  const [channel, setChannel] = useState("");
  const [filterCourse, setFilterCourse] = useState("");
  const [filterCampaign, setFilterCampaign] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterLinkId, setFilterLinkId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [terms, setTerms] = useState(false);
  const [guidelines, setGuidelines] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    const [nextLinks, nextTargets] = await Promise.all([
      getPartnerReferralLinks(),
      getPartnerReferralLinkTargets(),
    ]);
    setLinks(nextLinks);
    setTargets(nextTargets);
    if (!target) {
      if (nextTargets.courses[0]) setTarget(`course:${nextTargets.courses[0].id}`);
      else if (nextTargets.programmes[0]) setTarget(`programme:${nextTargets.programmes[0].id}`);
    }
  }

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getPartnerReferralLinks(),
      getPartnerReferralLinkTargets(),
      getReferralProgramGuide().catch(() => null),
    ])
      .then(([nextLinks, nextTargets, nextGuide]) => {
        if (cancelled) return;
        setLinks(nextLinks);
        setTargets(nextTargets);
        setGuide(nextGuide);
        if (nextTargets.courses[0]) setTarget(`course:${nextTargets.courses[0].id}`);
        else if (nextTargets.programmes[0]) setTarget(`programme:${nextTargets.programmes[0].id}`);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load referral links.");
      });
    return () => { cancelled = true; };
  }, []);

  async function applyFilters() {
    setError(null);
    try {
      const start_at = startDate ? new Date(`${startDate}T00:00:00.000Z`).toISOString() : undefined;
      const end_at = endDate ? new Date(new Date(`${endDate}T00:00:00.000Z`).getTime() + 24 * 60 * 60 * 1000).toISOString() : undefined;
      const rows = await getPartnerReferralLinks({
        start_at, end_at,
        course_id: filterCourse || undefined,
        campaign: filterCampaign.trim() || undefined,
        status: filterStatus || undefined,
        link_id: filterLinkId || undefined,
      });
      setLinks(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not filter referral link performance.");
    }
  }

  async function clearFilters() {
    setFilterCourse("");
    setFilterCampaign("");
    setFilterStatus("");
    setFilterLinkId("");
    setStartDate("");
    setEndDate("");
    try { setLinks(await getPartnerReferralLinks()); }
    catch (err) { setError(err instanceof ApiError ? err.detail : "Could not reload referral links."); }
  }

  async function createLink(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    const [kind, id] = target.split(":");
    if (!id || !["course", "programme"].includes(kind)) {
      setError("Choose an eligible course or programme.");
      return;
    }
    setBusy(true);
    try {
      const created = await createPartnerReferralLink({
        ...(kind === "course" ? { course_id: id } : { cohort_id: id }),
        campaign_label: campaign.trim() || undefined,
        campaign_channel: channel.trim() || undefined,
      });
      setLinks((current) => [created, ...current]);
      setCampaign("");
      setChannel("");
      setMessage(onboarding ? "Link created. It remains inactive until onboarding is complete." : "Referral link created.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create referral link.");
    } finally {
      setBusy(false);
    }
  }

  async function revoke(link: ReferralLink) {
    setError(null);
    try {
      const updated = await patchPartnerReferralLink(link.id, "revoked", "Revoked by partner");
      setLinks((current) => current.map((row) => row.id === updated.id ? updated : row));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not revoke referral link.");
    }
  }

  async function activate() {
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      await completePartnerOnboarding({
        profile_completed: true,
        terms_accepted: terms,
        marketing_guidelines_accepted: guidelines,
        terms_version: guide?.terms_version || "referral-partner-v1",
      });
      setMessage("Onboarding completed. Your referral links are active.");
      await load();
      await onActivated?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not complete onboarding.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">My Referral Links</h2>
        <p className="mt-1 text-sm text-muted-foreground">Create separate course and campaign links under one partner account. Commission remains attached to your partner profile.</p>
      </div>
      <form onSubmit={createLink} className="grid gap-3 rounded-lg border p-4 sm:grid-cols-2">
        <div className="space-y-1 sm:col-span-2">
          <label className="text-sm font-medium">Course or programme</label>
          <select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={target} onChange={(e) => setTarget(e.target.value)} required>
            <option value="">Choose an eligible destination</option>
            {targets.courses.length ? <optgroup label="Courses">{targets.courses.map((row) => <option key={row.id} value={`course:${row.id}`}>{row.title}</option>)}</optgroup> : null}
            {targets.programmes.length ? <optgroup label="Programmes">{targets.programmes.map((row) => <option key={row.id} value={`programme:${row.id}`}>{row.title}</option>)}</optgroup> : null}
          </select>
        </div>
        <div className="space-y-1"><label className="text-sm font-medium">Campaign label</label><Input value={campaign} onChange={(e) => setCampaign(e.target.value)} maxLength={120} placeholder="e.g. LinkedIn October" /></div>
        <div className="space-y-1"><label className="text-sm font-medium">Promotion channel</label><Input value={channel} onChange={(e) => setChannel(e.target.value)} maxLength={80} placeholder="e.g. LinkedIn" /></div>
        <div className="sm:col-span-2"><Button type="submit" disabled={busy || !target}>{busy ? "Saving…" : "Create referral link"}</Button></div>
      </form>
      {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
      {message ? <p role="status" className="text-sm text-muted-foreground">{message}</p> : null}
      <div className="grid gap-3 rounded-lg border p-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="space-y-1"><label className="text-sm font-medium">Course</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={filterCourse} onChange={(e) => setFilterCourse(e.target.value)}><option value="">All courses</option>{targets.courses.map((row) => <option key={row.id} value={row.id}>{row.title}</option>)}</select></div>
        <div className="space-y-1"><label className="text-sm font-medium">Campaign or channel</label><Input value={filterCampaign} onChange={(e) => setFilterCampaign(e.target.value)} placeholder="Search campaign" /></div>
        <div className="space-y-1"><label className="text-sm font-medium">Link status</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}><option value="">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option><option value="revoked">Revoked</option></select></div>
        <div className="space-y-1"><label className="text-sm font-medium">Specific link</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={filterLinkId} onChange={(e) => setFilterLinkId(e.target.value)}><option value="">All links</option>{links.map((row) => <option key={row.id} value={row.id}>{row.course_title || row.cohort_name || row.destination_path} · {row.campaign_label || row.code}</option>)}</select></div>
        <div className="space-y-1"><label className="text-sm font-medium">From date</label><Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></div>
        <div className="space-y-1"><label className="text-sm font-medium">To date</label><Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></div>
        <div className="flex items-end gap-2"><Button type="button" variant="outline" onClick={applyFilters}>Apply filters</Button><Button type="button" variant="ghost" onClick={clearFilters}>Clear</Button></div>
      </div>
      {links.length ? (
        <Table>
          <TableHeader><TableRow><TableHead>Destination</TableHead><TableHead>Campaign</TableHead><TableHead>Clicks</TableHead><TableHead>Paid enrollments</TableHead><TableHead>Commission</TableHead><TableHead>Status</TableHead><TableHead>Referral URL</TableHead><TableHead>Action</TableHead></TableRow></TableHeader>
          <TableBody>{links.map((row) => (
            <TableRow key={row.id}>
              <TableCell>{row.course_title || row.cohort_name || "All programmes"}</TableCell>
              <TableCell>{row.campaign_label || row.campaign_channel || "—"}</TableCell>
              <TableCell>{row.clicks}</TableCell>
              <TableCell>{row.paid_enrollments}</TableCell>
              <TableCell>{Object.keys(row.commission_by_currency || {}).length ? Object.entries(row.commission_by_currency).map(([currency, amount]) => `${currency} ${amount}`).join(" · ") : "—"}</TableCell>
              <TableCell className="capitalize" title={row.unavailable_reason || undefined}>{row.target_available ? row.status : "Unavailable"}</TableCell>
              <TableCell><div className="flex flex-wrap gap-2"><code className="max-w-[220px] break-all text-xs">{row.url}</code><Button size="sm" variant="outline" onClick={() => navigator.clipboard.writeText(row.url)}>Copy</Button></div></TableCell>
              <TableCell>{row.status !== "revoked" ? <Button size="sm" variant="outline" onClick={() => revoke(row)}>Revoke</Button> : "—"}</TableCell>
            </TableRow>
          ))}</TableBody>
        </Table>
      ) : <p className="text-sm text-muted-foreground">No referral links have been created yet.</p>}
      {guide ? <div className="rounded-lg border bg-muted/20 p-4 text-sm"><h3 className="font-semibold">Programme guide</h3><p className="mt-2">{guide.commission_policy}</p><p className="mt-2">{guide.attribution_policy}</p><p className="mt-2">{guide.payout_policy}</p><p className="mt-2">{guide.marketing_guidelines}</p><p className="mt-2 text-muted-foreground">Questions: {guide.support_contact}</p></div> : null}
      {onboarding ? (
        <div className="space-y-3 rounded-lg border p-4">
          <h3 className="font-semibold">Activation checklist</h3>
          <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} className="mt-1" /><span>I accept the current Referral Partner programme terms ({guide?.terms_version || "referral-partner-v1"}).</span></label>
          <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={guidelines} onChange={(e) => setGuidelines(e.target.checked)} className="mt-1" /><span>I have read and will follow the marketing guidelines, avoid spam and misleading claims, and make no unapproved promises.</span></label>
          <Button onClick={activate} disabled={busy || !terms || !guidelines || links.length === 0}>{busy ? "Completing…" : "Complete onboarding and activate"}</Button>
        </div>
      ) : null}
    </section>
  );
}
