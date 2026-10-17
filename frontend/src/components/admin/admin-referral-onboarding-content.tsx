"use client";

import { useEffect, useState } from "react";
import { ApiError, getAdminReferralApplications, getAdminReferralCohorts, getAdminReferralLinks, patchAdminReferralApplication, patchAdminReferralCohort, createAdminReferralCohort, patchAdminReferralLink, type ReferralPartnerApplication, type ReferralCohort, type ReferralLink } from "@/lib/api";
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

  useEffect(() => {
    setStatus(application.status);
    setCohortId(application.cohort_id || "");
    setScores(application.scores || {});
    setReviewNotes(application.review_notes || "");
    setRejectionReason(application.rejection_reason || "");
  }, [application]);

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
  const [tab, setTab] = useState<"applications" | "cohorts" | "links">("applications");
  const [applications, setApplications] = useState<ReferralPartnerApplication[]>([]);
  const [cohorts, setCohorts] = useState<ReferralCohort[]>([]);
  const [links, setLinks] = useState<ReferralLink[]>([]);
  const [newCohortName, setNewCohortName] = useState("");
  const [newCohortCapacity, setNewCohortCapacity] = useState("10");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setError(null);
    const [apps, nextCohorts, nextLinks] = await Promise.all([
      getAdminReferralApplications(), getAdminReferralCohorts(), getAdminReferralLinks(),
    ]);
    setApplications(apps);
    setCohorts(nextCohorts);
    setLinks(nextLinks);
  }

  useEffect(() => { load().catch((err) => setError(err instanceof ApiError ? err.detail : "Could not load onboarding data.")); }, []);

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

  async function updateLink(link: ReferralLink, status: "inactive" | "active" | "revoked") {
    setError(null);
    try { await patchAdminReferralLink(link.id, status, status === "revoked" ? "Revoked by admin" : undefined); await load(); }
    catch (err) { setError(err instanceof ApiError ? err.detail : "Could not update link."); }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">{(["applications", "cohorts", "links"] as const).map((key) => <Button key={key} size="sm" variant={tab === key ? "default" : "outline"} onClick={() => setTab(key)} className={tab === key ? "bg-brand-orange text-white hover:bg-brand-orange/90" : ""}>{key === "applications" ? "Applications" : key === "cohorts" ? "Cohorts" : "Referral links"}</Button>)}</div>
      {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
      {tab === "applications" ? <div className="space-y-3"><p className="text-sm text-muted-foreground">Score applicants consistently; approval requires an interview decision and an available cohort. Activation remains a separate partner onboarding step.</p>{applications.length ? applications.map((app) => <ApplicationReviewRow key={app.id} application={app} cohorts={cohorts} onSaved={() => load().catch((err) => setError(err instanceof ApiError ? err.detail : "Could not refresh applications."))} />) : <p className="text-sm text-muted-foreground">No applications submitted yet.</p>}</div> : null}
      {tab === "cohorts" ? <div className="space-y-4"><form onSubmit={createCohort} className="grid gap-3 rounded-lg border p-4 sm:grid-cols-[1fr_140px_auto]"><div className="space-y-1"><label className="text-sm font-medium">Cohort name</label><Input value={newCohortName} onChange={(e) => setNewCohortName(e.target.value)} minLength={2} required placeholder="e.g. Cohort 2" /></div><div className="space-y-1"><label className="text-sm font-medium">Capacity</label><Input type="number" min={1} max={1000} value={newCohortCapacity} onChange={(e) => setNewCohortCapacity(e.target.value)} required /></div><div className="flex items-end"><Button type="submit" disabled={busy || !newCohortName.trim()}>{busy ? "Creating…" : "Create cohort"}</Button></div></form><Table><TableHeader><TableRow><TableHead>Cohort</TableHead><TableHead>Approved / capacity</TableHead><TableHead>Remaining</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader><TableBody>{cohorts.map((row) => <TableRow key={row.id}><TableCell>{row.name}</TableCell><TableCell>{row.approved_count} / {row.capacity}</TableCell><TableCell>{row.remaining_slots}</TableCell><TableCell>{row.is_active ? "Active" : "Inactive"}</TableCell><TableCell className="flex flex-wrap gap-2"><Button size="sm" variant="outline" onClick={() => { const value = window.prompt("New cohort capacity", String(row.capacity)); if (value && Number.isInteger(Number(value))) void updateCohort(row, { capacity: Number(value) }); }}>Change capacity</Button><Button size="sm" variant="outline" onClick={() => void updateCohort(row, { is_active: !row.is_active })}>{row.is_active ? "Deactivate" : "Activate"}</Button></TableCell></TableRow>)}</TableBody></Table></div> : null}
      {tab === "links" ? <Table><TableHeader><TableRow><TableHead>Partner</TableHead><TableHead>Destination</TableHead><TableHead>Campaign</TableHead><TableHead>Clicks</TableHead><TableHead>Paid enrollments</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader><TableBody>{links.map((row) => <TableRow key={row.id}><TableCell>{row.partner_id.slice(0, 8)}</TableCell><TableCell>{row.course_title || row.cohort_name || row.destination_path}</TableCell><TableCell>{row.campaign_label || row.campaign_channel || "—"}</TableCell><TableCell>{row.clicks}</TableCell><TableCell>{row.paid_enrollments}</TableCell><TableCell className="capitalize">{row.status}</TableCell><TableCell className="flex flex-wrap gap-2">{row.status === "active" ? <Button size="sm" variant="outline" onClick={() => void updateLink(row, "inactive")}>Pause</Button> : null}{row.status === "inactive" ? <Button size="sm" variant="outline" onClick={() => void updateLink(row, "active")}>Activate</Button> : null}{row.status !== "revoked" ? <Button size="sm" variant="outline" onClick={() => void updateLink(row, "revoked")}>Revoke</Button> : "—"}</TableCell></TableRow>)}</TableBody></Table> : null}
    </div>
  );
}
