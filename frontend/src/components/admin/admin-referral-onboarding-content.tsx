"use client";

import { useEffect, useState } from "react";
import { ApiError, getAdminReferralApplications, getAdminReferralCohorts, getAdminReferralLinks, patchAdminReferralApplication, patchAdminReferralCohort, createAdminReferralCohort, patchAdminReferralLink, getAdminReferralProgramGuide, updateAdminReferralProgramGuide, getAdminReferralAudit, getReferralEligibleCourses, type ReferralPartnerApplication, type ReferralCohort, type ReferralLink, type ReferralProgramGuide, type ReferralAuditRow } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const WEIGHTS: [string, string, number][] = [
  ["audience_relevance", "Relevance of audience", 30],
  ["promotion_strategy", "Promotion strategy", 25],
  ["credibility_engagement", "Credibility and engagement", 20],
  ["relevant_experience", "Relevant experience", 15],
  ["communication_professionalism", "Communication and professionalism", 10],
];

const TRANSITIONS: Record<string, string[]> = {
  submitted: ["under_review", "rejected", "waitlisted"],
  under_review: ["shortlisted", "interviewed", "rejected", "waitlisted"],
  shortlisted: ["interviewed", "rejected", "waitlisted", "under_review"],
  interviewed: ["approved", "rejected", "waitlisted", "under_review"],
  approved: ["onboarding", "rejected", "waitlisted"],
  onboarding: ["suspended", "inactive"],
  active: ["suspended", "inactive"],
  suspended: ["inactive"],
  waitlisted: ["under_review", "shortlisted", "rejected"],
  rejected: [],
  inactive: ["suspended"],
};

function ApplicationReviewRow({ application, cohorts, onSaved }: {
  application: ReferralPartnerApplication;
  cohorts: ReferralCohort[];
  onSaved: () => void;
}) {
  const [status, setStatus] = useState(application.status);
  const [cohortId, setCohortId] = useState(application.cohort_id || "");
  const [scores, setScores] = useState<Record<string, number>>(application.scores || {});
  const [reviewNotes, setReviewNotes] = useState(application.review_notes || "");
  const [rejectionReason, setRejectionReason] = useState(application.rejection_reason || "");
  const [interviewAt, setInterviewAt] = useState(application.interview_at?.slice(0, 16) || "");
  const [interviewStatus, setInterviewStatus] = useState(application.interview_status || "scheduled");
  const [interviewNotes, setInterviewNotes] = useState(application.interview_notes || "");
  const [interviewDecision, setInterviewDecision] = useState(application.interview_decision || "");
  const [interviewReason, setInterviewReason] = useState(application.interview_reason || "");
  const [followUpActions, setFollowUpActions] = useState(application.follow_up_actions || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await patchAdminReferralApplication(application.id, {
        status,
        cohort_id: cohortId || undefined,
        scores,
        review_notes: reviewNotes || undefined,
        rejection_reason: rejectionReason || undefined,
        interview_at: interviewAt ? new Date(interviewAt).toISOString() : undefined,
        interview_status: interviewStatus || undefined,
        interview_notes: interviewNotes || undefined,
        interview_decision: interviewDecision || undefined,
        interview_reason: interviewReason || undefined,
        follow_up_actions: followUpActions || undefined,
      });
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update application.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <details className="rounded-lg border p-4">
      <summary className="cursor-pointer list-none">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><p className="font-semibold">{application.full_name}</p><p className="text-sm text-muted-foreground">{application.email} · {application.country || "Country not supplied"}</p><p className="mt-1 text-xs text-muted-foreground">Submitted {new Date(application.created_at).toLocaleDateString()} · Score {application.score_total ?? "not scored"}/100</p></div>
          <span className="rounded-full border px-3 py-1 text-xs capitalize">{application.status.replaceAll("_", " ")}</span>
        </div>
      </summary>
      <div className="mt-4 space-y-4">
        <div className="grid gap-3 text-sm sm:grid-cols-2">
          <p><strong>Time zone:</strong> {application.timezone || "—"}</p>
          <p><strong>LinkedIn:</strong> {application.linkedin_url ? <a className="underline" href={application.linkedin_url} target="_blank" rel="noreferrer">{application.linkedin_url}</a> : "—"}</p>
          <p><strong>Communities:</strong> {application.communities || "—"}</p>
          <p><strong>Audience:</strong> {application.audience_size || "—"}</p>
          <p><strong>Engagement:</strong> {application.audience_engagement || "—"}</p>
          <p><strong>Interested courses:</strong> {application.interested_courses.join(", ") || "No preference specified"}</p>
          <p className="sm:col-span-2"><strong>Promotion channels:</strong> {application.promotion_channels.join(", ")}</p>
          <p className="sm:col-span-2"><strong>Marketing plan:</strong> {application.marketing_plan}</p>
          <p className="sm:col-span-2"><strong>Relevant experience:</strong> {application.relevant_experience || "—"}</p>
          <p className="sm:col-span-2"><strong>Partnership experience:</strong> {application.partnership_experience || "—"}</p>
          {application.social_profiles.map((item) => <p key={item.platform}><strong>{item.platform}:</strong> <a className="underline" href={item.url} target="_blank" rel="noreferrer">{item.url}</a></p>)}
        </div>
        <form onSubmit={save} className="space-y-4 border-t pt-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1"><label className="text-sm font-medium">Application status</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={status} onChange={(e) => setStatus(e.target.value)}><option value={application.status}>{application.status.replaceAll("_", " ")}</option>{(TRANSITIONS[application.status] || []).map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></div>
            <div className="space-y-1"><label className="text-sm font-medium">Cohort</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={cohortId} onChange={(e) => setCohortId(e.target.value)}><option value="">Assign default Cohort 1 on approval</option>{cohorts.map((cohort) => <option key={cohort.id} value={cohort.id} disabled={!cohort.is_active || (cohort.remaining_slots <= 0 && cohort.id !== application.cohort_id)}>{cohort.name} · {cohort.approved_count}/{cohort.capacity}</option>)}</select></div>
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold">Application score (100 points total)</h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{WEIGHTS.map(([key, label, max]) => <div key={key} className="space-y-1"><label className="text-xs text-muted-foreground">{label} (0–{max})</label><Input type="number" min={0} max={max} value={scores[key] ?? ""} onChange={(e) => setScores((old) => ({ ...old, [key]: e.target.value === "" ? 0 : Number(e.target.value) }))} /></div>)}</div>
            <p className="mt-2 text-sm">Score total: <strong>{WEIGHTS.reduce((sum, [key]) => sum + (scores[key] || 0), 0)}/100</strong></p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1"><label className="text-sm font-medium">Interview date and time</label><Input type="datetime-local" value={interviewAt} onChange={(e) => setInterviewAt(e.target.value)} /></div>
            <div className="space-y-1"><label className="text-sm font-medium">Interview status</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={interviewStatus} onChange={(e) => setInterviewStatus(e.target.value)}><option value="not_scheduled">Not scheduled</option><option value="scheduled">Scheduled</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option><option value="no_show">No show</option></select></div>
            <div className="space-y-1"><label className="text-sm font-medium">Interview decision</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={interviewDecision} onChange={(e) => setInterviewDecision(e.target.value)}><option value="">Not decided</option><option value="recommend">Recommend</option><option value="hold">Hold</option><option value="decline">Decline</option></select></div>
            <div className="space-y-1"><label className="text-sm font-medium">Review notes</label><textarea rows={2} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} /></div>
            <div className="space-y-1"><label className="text-sm font-medium">Interview notes</label><textarea rows={2} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={interviewNotes} onChange={(e) => setInterviewNotes(e.target.value)} /></div>
            <div className="space-y-1"><label className="text-sm font-medium">Decision reason</label><textarea rows={2} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={interviewReason} onChange={(e) => setInterviewReason(e.target.value)} /></div>
            <div className="space-y-1"><label className="text-sm font-medium">Follow-up actions</label><textarea rows={2} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={followUpActions} onChange={(e) => setFollowUpActions(e.target.value)} /></div>
            <div className="space-y-1"><label className="text-sm font-medium">Rejection reason (required when rejecting)</label><textarea rows={2} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={rejectionReason} onChange={(e) => setRejectionReason(e.target.value)} /></div>
          </div>
          {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
          <Button type="submit" disabled={busy}>{busy ? "Saving…" : "Save review and decision"}</Button>
        </form>
      </div>
    </details>
  );
}

export function AdminReferralOnboardingContent() {
  const [tab, setTab] = useState<"applications" | "cohorts" | "links" | "guide" | "audit">("applications");
  const [applications, setApplications] = useState<ReferralPartnerApplication[]>([]);
  const [applicationFilter, setApplicationFilter] = useState("");
  const [cohorts, setCohorts] = useState<ReferralCohort[]>([]);
  const [links, setLinks] = useState<ReferralLink[]>([]);
  const [eligibleCourses, setEligibleCourses] = useState<{ id: string; slug: string; title: string }[]>([]);
  const [linkFilterPartner, setLinkFilterPartner] = useState("");
  const [linkFilterCourse, setLinkFilterCourse] = useState("");
  const [linkFilterCampaign, setLinkFilterCampaign] = useState("");
  const [linkFilterStatus, setLinkFilterStatus] = useState("");
  const [linkFilterId, setLinkFilterId] = useState("");
  const [linkStartDate, setLinkStartDate] = useState("");
  const [linkEndDate, setLinkEndDate] = useState("");
  const [guide, setGuide] = useState<ReferralProgramGuide | null>(null);
  const [audit, setAudit] = useState<ReferralAuditRow[]>([]);
  const [guideSaving, setGuideSaving] = useState(false);
  const [newCohortName, setNewCohortName] = useState("");
  const [newCohortCapacity, setNewCohortCapacity] = useState("10");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setError(null);
    const [apps, nextCohorts, nextLinks, nextGuide, nextAudit, nextCourses] = await Promise.all([
      getAdminReferralApplications(), getAdminReferralCohorts(), getAdminReferralLinks(),
      getAdminReferralProgramGuide(), getAdminReferralAudit(), getReferralEligibleCourses().catch(() => []),
    ]);
    setApplications(apps);
    setCohorts(nextCohorts);
    setLinks(nextLinks);
    setGuide(nextGuide);
    setAudit(nextAudit);
    setEligibleCourses(nextCourses);
  }

  useEffect(() => {
    let cancelled = false;
    Promise.resolve().then(() => load()).catch((err) => {
      if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load onboarding data.");
    });
    return () => { cancelled = true; };
  }, []);

  async function createCohort(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createAdminReferralCohort({ name: newCohortName, capacity: Number(newCohortCapacity), is_active: true });
      setNewCohortName("");
      setNewCohortCapacity("10");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create cohort.");
    } finally { setBusy(false); }
  }

  async function updateCohort(cohort: ReferralCohort, updates: { capacity?: number; is_active?: boolean }) {
    setError(null);
    try { await patchAdminReferralCohort(cohort.id, updates); await load(); }
    catch (err) { setError(err instanceof ApiError ? err.detail : "Could not update cohort."); }
  }

  async function applyApplicationFilter() {
    setError(null);
    try { setApplications(await getAdminReferralApplications(applicationFilter || undefined)); }
    catch (err) { setError(err instanceof ApiError ? err.detail : "Could not filter applications."); }
  }

  async function applyLinkFilters() {
    setError(null);
    try {
      const start_at = linkStartDate ? new Date(`${linkStartDate}T00:00:00.000Z`).toISOString() : undefined;
      const end_at = linkEndDate ? new Date(new Date(`${linkEndDate}T00:00:00.000Z`).getTime() + 24 * 60 * 60 * 1000).toISOString() : undefined;
      setLinks(await getAdminReferralLinks({
        partner_id: linkFilterPartner.trim() || undefined,
        course_id: linkFilterCourse || undefined,
        campaign: linkFilterCampaign.trim() || undefined,
        status: linkFilterStatus || undefined,
        link_id: linkFilterId || undefined,
        start_at, end_at,
      }));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not filter referral links.");
    }
  }

  async function saveGuide(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!guide) return;
    setGuideSaving(true);
    setError(null);
    const form = new FormData(e.currentTarget);
    try {
      await updateAdminReferralProgramGuide({
        terms_version: String(form.get("terms_version") || ""),
        program_overview: String(form.get("program_overview") || ""),
        commission_policy: String(form.get("commission_policy") || ""),
        attribution_policy: String(form.get("attribution_policy") || ""),
        payout_policy: String(form.get("payout_policy") || ""),
        marketing_guidelines: String(form.get("marketing_guidelines") || ""),
        support_contact: String(form.get("support_contact") || ""),
      });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save the referral program guide.");
    } finally { setGuideSaving(false); }
  }

  async function updateLink(link: ReferralLink, status: "inactive" | "active" | "revoked") {
    setError(null);
    try { await patchAdminReferralLink(link.id, status, status === "revoked" ? "Revoked by admin" : undefined); await load(); }
    catch (err) { setError(err instanceof ApiError ? err.detail : "Could not update link."); }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">{(["applications", "cohorts", "links", "guide", "audit"] as const).map((key) => <Button key={key} size="sm" variant={tab === key ? "default" : "outline"} onClick={() => setTab(key)} className={tab === key ? "bg-brand-orange text-white hover:bg-brand-orange/90" : ""}>{key === "applications" ? "Applications" : key === "cohorts" ? "Cohorts" : key === "links" ? "Referral links" : key === "guide" ? "Program guide" : "Audit trail"}</Button>)}</div>
      {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
      {tab === "applications" ? <div className="space-y-3"><div className="flex flex-wrap items-end gap-2"><div className="space-y-1"><label className="text-sm font-medium">Filter applications by status</label><select className="h-10 rounded-md border border-input bg-background px-3 text-sm" value={applicationFilter} onChange={(e) => setApplicationFilter(e.target.value)}><option value="">All statuses</option>{["submitted","under_review","shortlisted","interviewed","approved","onboarding","active","rejected","waitlisted","suspended","inactive"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></div><Button variant="outline" onClick={applyApplicationFilter}>Apply filter</Button><Button variant="ghost" onClick={() => { setApplicationFilter(""); void getAdminReferralApplications().then(setApplications); }}>Clear</Button></div><p className="text-sm text-muted-foreground">Score applicants consistently; approval requires an interview decision and an available cohort. Activation remains a separate partner onboarding step.</p>{applications.length ? applications.map((app) => <ApplicationReviewRow key={`${app.id}:${app.updated_at}`} application={app} cohorts={cohorts} onSaved={() => load().catch((err) => setError(err instanceof ApiError ? err.detail : "Could not refresh applications."))} />) : <p className="text-sm text-muted-foreground">No applications submitted yet.</p>}</div> : null}
      {tab === "cohorts" ? <div className="space-y-4"><form onSubmit={createCohort} className="grid gap-3 rounded-lg border p-4 sm:grid-cols-[1fr_140px_auto]"><div className="space-y-1"><label className="text-sm font-medium">Cohort name</label><Input value={newCohortName} onChange={(e) => setNewCohortName(e.target.value)} minLength={2} required placeholder="e.g. Cohort 2" /></div><div className="space-y-1"><label className="text-sm font-medium">Capacity</label><Input type="number" min={1} max={1000} value={newCohortCapacity} onChange={(e) => setNewCohortCapacity(e.target.value)} required /></div><div className="flex items-end"><Button type="submit" disabled={busy || !newCohortName.trim()}>{busy ? "Creating…" : "Create cohort"}</Button></div></form><Table><TableHeader><TableRow><TableHead>Cohort</TableHead><TableHead>Approved / capacity</TableHead><TableHead>Remaining</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader><TableBody>{cohorts.map((row) => <TableRow key={row.id}><TableCell>{row.name}</TableCell><TableCell>{row.approved_count} / {row.capacity}</TableCell><TableCell>{row.remaining_slots}</TableCell><TableCell>{row.is_active ? "Active" : "Inactive"}</TableCell><TableCell className="flex flex-wrap gap-2"><Button size="sm" variant="outline" onClick={() => { const value = window.prompt("New cohort capacity", String(row.capacity)); if (value && Number.isInteger(Number(value))) void updateCohort(row, { capacity: Number(value) }); }}>Change capacity</Button><Button size="sm" variant="outline" onClick={() => void updateCohort(row, { is_active: !row.is_active })}>{row.is_active ? "Deactivate" : "Activate"}</Button></TableCell></TableRow>)}</TableBody></Table></div> : null}
      {tab === "guide" && guide ? <form onSubmit={saveGuide} className="space-y-4 rounded-lg border p-4"><div><h3 className="font-semibold">Referral program guide and terms</h3><p className="mt-1 text-sm text-muted-foreground">These settings feed the public programme page and partner onboarding. Changing the terms version identifies the current acknowledgement version; coordinate any policy change before publishing.</p></div><div className="space-y-1"><label className="text-sm font-medium">Terms version</label><Input name="terms_version" defaultValue={guide.terms_version} required maxLength={40} /></div>{([["program_overview","Programme overview"],["commission_policy","Commission policy"],["attribution_policy","Attribution policy"],["payout_policy","Payout policy"],["marketing_guidelines","Marketing guidelines"]] as const).map(([name,label]) => <div key={name} className="space-y-1"><label className="text-sm font-medium">{label}</label><textarea name={name} defaultValue={guide[name]} rows={4} required className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" /></div>)}<div className="space-y-1"><label className="text-sm font-medium">Support contact</label><Input name="support_contact" defaultValue={guide.support_contact} required maxLength={320} /></div><Button type="submit" disabled={guideSaving}>{guideSaving ? "Saving…" : "Save programme guide"}</Button></form> : null}
      {tab === "audit" ? <div className="space-y-3"><p className="text-sm text-muted-foreground">Administrative changes to applications, cohorts, links, guide settings and partner actions are recorded here.</p><Table><TableHeader><TableRow><TableHead>Time</TableHead><TableHead>Actor ID</TableHead><TableHead>Action</TableHead><TableHead>Target</TableHead><TableHead>Details</TableHead></TableRow></TableHeader><TableBody>{audit.map((row) => <TableRow key={row.id}><TableCell>{new Date(row.created_at).toLocaleString()}</TableCell><TableCell className="font-mono text-xs">{row.actor_id || "System"}</TableCell><TableCell>{row.action}</TableCell><TableCell>{row.entity_type}{row.entity_id ? ` · ${row.entity_id.slice(0, 8)}` : ""}</TableCell><TableCell><details><summary className="cursor-pointer text-sm">View</summary><pre className="mt-2 max-w-xl whitespace-pre-wrap break-words text-xs">{JSON.stringify({ note: row.note, before: row.before_json, after: row.after_json }, null, 2)}</pre></details></TableCell></TableRow>)}</TableBody></Table></div> : null}
      {tab === "links" ? <div className="space-y-3">
        <div className="grid gap-3 rounded-lg border p-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-1"><label className="text-sm font-medium">Partner ID</label><Input value={linkFilterPartner} onChange={(e) => setLinkFilterPartner(e.target.value)} placeholder="Exact partner UUID" /></div>
          <div className="space-y-1"><label className="text-sm font-medium">Course</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={linkFilterCourse} onChange={(e) => setLinkFilterCourse(e.target.value)}><option value="">All courses</option>{eligibleCourses.map((row) => <option key={row.id} value={row.id}>{row.title}</option>)}</select></div>
          <div className="space-y-1"><label className="text-sm font-medium">Campaign or channel</label><Input value={linkFilterCampaign} onChange={(e) => setLinkFilterCampaign(e.target.value)} placeholder="Search campaign" /></div>
          <div className="space-y-1"><label className="text-sm font-medium">Specific link</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={linkFilterId} onChange={(e) => setLinkFilterId(e.target.value)}><option value="">All links</option>{links.map((row) => <option key={row.id} value={row.id}>{row.course_title || row.cohort_name || row.destination_path} · {row.campaign_label || row.code}</option>)}</select></div>
          <div className="space-y-1"><label className="text-sm font-medium">Status</label><select className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={linkFilterStatus} onChange={(e) => setLinkFilterStatus(e.target.value)}><option value="">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option><option value="revoked">Revoked</option></select></div>
          <div className="space-y-1"><label className="text-sm font-medium">From date</label><Input type="date" value={linkStartDate} onChange={(e) => setLinkStartDate(e.target.value)} /></div>
          <div className="space-y-1"><label className="text-sm font-medium">To date</label><Input type="date" value={linkEndDate} onChange={(e) => setLinkEndDate(e.target.value)} /></div>
          <div className="sm:col-span-2 lg:col-span-3"><Button variant="outline" onClick={applyLinkFilters}>Apply filters</Button><Button className="ml-2" variant="ghost" onClick={() => { setLinkFilterPartner(""); setLinkFilterCourse(""); setLinkFilterCampaign(""); setLinkFilterStatus(""); setLinkFilterId(""); setLinkStartDate(""); setLinkEndDate(""); void load(); }}>Clear filters</Button></div>
        </div>
        <Table><TableHeader><TableRow><TableHead>Partner</TableHead><TableHead>Destination</TableHead><TableHead>Campaign</TableHead><TableHead>Clicks</TableHead><TableHead>Paid enrollments</TableHead><TableHead>Conversion rate</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader><TableBody>{links.map((row) => <TableRow key={row.id}><TableCell>{row.partner_id.slice(0, 8)}</TableCell><TableCell>{row.course_title || row.cohort_name || row.destination_path}</TableCell><TableCell>{row.campaign_label || row.campaign_channel || "—"}</TableCell><TableCell>{row.clicks}</TableCell><TableCell>{row.paid_enrollments}</TableCell><TableCell>{Number(row.conversion_rate).toFixed(2)}%</TableCell><TableCell className="capitalize" title={row.unavailable_reason || undefined}>{row.target_available ? row.status : "Unavailable"}</TableCell><TableCell className="flex flex-wrap gap-2">{row.status === "active" ? <Button size="sm" variant="outline" onClick={() => void updateLink(row, "inactive")}>Pause</Button> : null}{row.status === "inactive" ? <Button size="sm" variant="outline" onClick={() => void updateLink(row, "active")}>Activate</Button> : null}{row.status !== "revoked" ? <Button size="sm" variant="outline" onClick={() => void updateLink(row, "revoked")}>Revoke</Button> : "—"}</TableCell></TableRow>)}</TableBody></Table></div> : null}
    </div>
  );
}
