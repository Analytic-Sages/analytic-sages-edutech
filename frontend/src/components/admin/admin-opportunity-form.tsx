"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import {
  announceAdminOpportunity,
  requestAdminReviewAssist,
  archiveAdminOpportunity,
  createAdminOpportunity,
  getAdminOpportunity,
  getAdminOpportunityTaxonomy,
  publishAdminOpportunity,
  rejectAdminOpportunity,
  unpublishAdminOpportunity,
  updateAdminOpportunity,
  TYPE_LABELS,
  REGION_LABELS,
  type AdminTaxonomy,
  type ExperienceLevel,
  type LocationRegion,
  type OpportunityAdmin,
  type OpportunityStatus,
  type OpportunityType,
  type OpportunityWritePayload,
  type PublicBadge,
  type WorkplaceType,
} from "@/lib/opportunities";

type FormState = {
  slug: string;
  title: string;
  organization_name: string;
  description: string;
  requirements: string;
  responsibilities: string;
  benefits: string;
  opportunity_type: OpportunityType;
  employment_type: string;
  experience_level: ExperienceLevel;
  location: string;
  country: string;
  region: string;
  workplace_type: WorkplaceType;
  application_url: string;
  source_url: string;
  deadline: string;
  source_id: string;
  public_badge: PublicBadge;
  featured: boolean;
  admin_notes: string;
  career_path_ids: string[];
  skill_ids: string[];
};

const EMPTY: FormState = {
  slug: "",
  title: "",
  organization_name: "",
  description: "",
  requirements: "",
  responsibilities: "",
  benefits: "",
  opportunity_type: "job",
  employment_type: "",
  experience_level: "not_specified",
  location: "",
  country: "",
  region: "",
  workplace_type: "remote",
  application_url: "",
  source_url: "",
  deadline: "",
  source_id: "",
  public_badge: "none",
  featured: false,
  admin_notes: "",
  career_path_ids: [],
  skill_ids: [],
};

function toLocalInput(iso: string | null) {
  if (!iso) return "";
  const date = new Date(iso);
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function fromOpportunity(row: OpportunityAdmin): FormState {
  return {
    slug: row.slug,
    title: row.title,
    organization_name: row.organization_name,
    description: row.description,
    requirements: row.requirements,
    responsibilities: row.responsibilities ?? "",
    benefits: row.benefits ?? "",
    opportunity_type: row.opportunity_type,
    employment_type: row.employment_type ?? "",
    experience_level: row.experience_level,
    location: row.location,
    country: row.country ?? "",
    region: row.region ?? "",
    workplace_type: row.workplace_type,
    application_url: row.application_url,
    source_url: row.source_url ?? "",
    deadline: toLocalInput(row.deadline),
    source_id: row.source_id ?? "",
    public_badge: row.public_badge,
    featured: row.featured,
    admin_notes: row.admin_notes,
    career_path_ids: row.career_paths.map((item) => item.id),
    skill_ids: row.skills.map((item) => item.id),
  };
}

function withSeconds(value: string) {
  if (!value) return null;
  return value.length === 16 ? `${value}:00` : value;
}

function toPayload(form: FormState): OpportunityWritePayload {
  return {
    slug: form.slug.trim() || null,
    title: form.title.trim(),
    organization_name: form.organization_name.trim(),
    description: form.description.trim(),
    requirements: form.requirements.trim(),
    responsibilities: form.responsibilities.trim() || null,
    benefits: form.benefits.trim() || null,
    opportunity_type: form.opportunity_type,
    employment_type: form.employment_type || null,
    experience_level: form.experience_level,
    location: form.location.trim(),
    country: form.country.trim() || null,
    region: (form.region as LocationRegion) || null,
    workplace_type: form.workplace_type,
    application_url: form.application_url.trim(),
    source_url: form.source_url.trim() || null,
    deadline: withSeconds(form.deadline),
    source_id: form.source_id || null,
    public_badge: form.public_badge,
    featured: form.featured,
    admin_notes: form.admin_notes.trim(),
    career_path_ids: form.career_path_ids,
    skill_ids: form.skill_ids,
  };
}

function toggleId(ids: string[], id: string) {
  return ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id];
}

export function AdminOpportunityForm({ opportunityId }: { opportunityId?: string }) {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [taxonomy, setTaxonomy] = useState<AdminTaxonomy | null>(null);
  const [status, setStatus] = useState<OpportunityStatus>("draft");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [acting, setActing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [assist, setAssist] = useState<{
    notes?: string | null;
    suggested_type?: string | null;
    suggested_career_paths?: string[];
    risk_notes?: string[];
    provider?: string | null;
  } | null>(null);

  useEffect(() => {
    let ignore = false;
    Promise.all([
      getAdminOpportunityTaxonomy(),
      opportunityId ? getAdminOpportunity(opportunityId) : Promise.resolve(null),
    ])
      .then(([tax, row]) => {
        if (ignore) return;
        setTaxonomy(tax);
        if (row) {
          setForm(fromOpportunity(row));
          setStatus(row.status);
          setAssist(row.review_assist || null);
        }
      })
      .catch((err) => {
        if (!ignore) setError(err instanceof ApiError ? err.detail : "Could not load opportunity.");
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [opportunityId]);

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = toPayload(form);
      if (opportunityId) {
        const updated = await updateAdminOpportunity(opportunityId, payload);
        setForm(fromOpportunity(updated));
        setStatus(updated.status);
        router.push("/admin/opportunities");
      } else {
        const created = await createAdminOpportunity(payload);
        router.replace(`/admin/opportunities/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save opportunity.");
    } finally {
      setSaving(false);
    }
  }

  async function runAction(kind: "publish" | "unpublish" | "reject" | "archive") {
    if (!opportunityId) return;
    setActing(kind);
    setError(null);
    try {
      const payload = toPayload(form);
      await updateAdminOpportunity(opportunityId, payload);
      const fn = {
        publish: publishAdminOpportunity,
        unpublish: unpublishAdminOpportunity,
        reject: rejectAdminOpportunity,
        archive: archiveAdminOpportunity,
      }[kind];
      const updated = await fn(opportunityId);
      setForm(fromOpportunity(updated));
      setStatus(updated.status);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update status.");
    } finally {
      setActing(null);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading opportunity…
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        breadcrumbs={[
          { label: "Admin", href: "/admin" },
          { label: "Opportunities", href: "/admin/opportunities" },
          { label: opportunityId ? "Edit opportunity" : "New opportunity" },
        ]}
        title={opportunityId ? "Edit opportunity" : "New opportunity"}
        description="Manual listings still go through validation. Publish only after the application URL and source look trustworthy."
      />
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      <form onSubmit={onSubmit} className="space-y-8">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Label htmlFor="title">Title</Label>
            <Input id="title" value={form.title} onChange={(e) => set("title", e.target.value)} required />
          </div>
          <div>
            <Label htmlFor="organization_name">Organization</Label>
            <Input
              id="organization_name"
              value={form.organization_name}
              onChange={(e) => set("organization_name", e.target.value)}
              required
            />
          </div>
          <div>
            <Label htmlFor="slug">Slug</Label>
            <Input id="slug" value={form.slug} onChange={(e) => set("slug", e.target.value)} placeholder="generated-from-title" />
          </div>
          <div>
            <Label htmlFor="opportunity_type">Type</Label>
            <select
              id="opportunity_type"
              className="mt-1 h-9 w-full rounded-lg border bg-background px-2.5 text-sm"
              value={form.opportunity_type}
              onChange={(e) => set("opportunity_type", e.target.value as OpportunityType)}
            >
              {Object.entries(TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="workplace_type">Workplace</Label>
            <select
              id="workplace_type"
              className="mt-1 h-9 w-full rounded-lg border bg-background px-2.5 text-sm"
              value={form.workplace_type}
              onChange={(e) => set("workplace_type", e.target.value as WorkplaceType)}
            >
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">Onsite</option>
            </select>
          </div>
          <div>
            <Label htmlFor="experience_level">Experience</Label>
            <select
              id="experience_level"
              className="mt-1 h-9 w-full rounded-lg border bg-background px-2.5 text-sm"
              value={form.experience_level}
              onChange={(e) => set("experience_level", e.target.value as ExperienceLevel)}
            >
              <option value="not_specified">Not specified</option>
              <option value="intern">Intern</option>
              <option value="junior">Junior</option>
              <option value="mid">Mid-level</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead</option>
            </select>
          </div>
          <div>
            <Label htmlFor="employment_type">Employment type</Label>
            <select
              id="employment_type"
              className="mt-1 h-9 w-full rounded-lg border bg-background px-2.5 text-sm"
              value={form.employment_type}
              onChange={(e) => set("employment_type", e.target.value)}
            >
              <option value="">Not specified</option>
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
              <option value="volunteer">Volunteer</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <Label htmlFor="location">Location</Label>
            <Input id="location" value={form.location} onChange={(e) => set("location", e.target.value)} />
          </div>
          <div>
            <Label htmlFor="region">Region</Label>
            <select
              id="region"
              className="mt-1 h-9 w-full rounded-lg border bg-background px-2.5 text-sm"
              value={form.region}
              onChange={(e) => set("region", e.target.value)}
            >
              <option value="">Not specified</option>
              {(Object.keys(REGION_LABELS) as LocationRegion[]).map((value) => (
                <option key={value} value={value}>
                  {REGION_LABELS[value]}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="deadline">Deadline</Label>
            <Input
              id="deadline"
              type="datetime-local"
              value={form.deadline}
              onChange={(e) => set("deadline", e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="application_url">Application URL</Label>
            <Input
              id="application_url"
              type="url"
              value={form.application_url}
              onChange={(e) => set("application_url", e.target.value)}
              required
            />
          </div>
          <div>
            <Label htmlFor="source_url">Source URL</Label>
            <Input id="source_url" type="url" value={form.source_url} onChange={(e) => set("source_url", e.target.value)} />
          </div>
          <div>
            <Label htmlFor="public_badge">Public badge</Label>
            <select
              id="public_badge"
              className="mt-1 h-9 w-full rounded-lg border bg-background px-2.5 text-sm"
              value={form.public_badge}
              onChange={(e) => set("public_badge", e.target.value as PublicBadge)}
            >
              <option value="none">None (do not show a public badge)</option>
              <option value="official_source">Verified Source</option>
              <option value="partner">Partner</option>
              <option value="source_checked">Trusted Platform</option>
              <option value="community_submission">Community</option>
            </select>
          </div>
          <div>
            <Label htmlFor="source_id">Source</Label>
            <select
              id="source_id"
              className="mt-1 h-9 w-full rounded-lg border bg-background px-2.5 text-sm"
              value={form.source_id}
              onChange={(e) => set("source_id", e.target.value)}
            >
              <option value="">Default (Manual)</option>
              {(taxonomy?.sources || []).map((source) =>
                source ? (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ) : null
              )}
            </select>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <Label htmlFor="description">Description</Label>
            <p className="mb-2 text-xs text-muted-foreground">
              Blank lines start paragraphs. Use ## headings and - or 1. for lists. Imported jobs keep this structure after review.
            </p>
            <Textarea
              id="description"
              rows={14}
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="responsibilities">Responsibilities</Label>
            <Textarea
              id="responsibilities"
              rows={4}
              value={form.responsibilities}
              onChange={(e) => set("responsibilities", e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="requirements">Requirements</Label>
            <Textarea id="requirements" rows={4} value={form.requirements} onChange={(e) => set("requirements", e.target.value)} />
          </div>
          <div>
            <Label htmlFor="benefits">Benefits</Label>
            <Textarea id="benefits" rows={3} value={form.benefits} onChange={(e) => set("benefits", e.target.value)} />
          </div>
        </div>

        <div>
          <Label>Career paths</Label>
          <p className="mb-2 text-xs text-muted-foreground">The first selected path is treated as primary.</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {(taxonomy?.career_paths || []).map((path) => (
              <label key={path.id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.career_path_ids.includes(path.id)}
                  onChange={() => set("career_path_ids", toggleId(form.career_path_ids, path.id))}
                />
                {path.name}
              </label>
            ))}
          </div>
        </div>

        <div>
          <Label>Skills</Label>
          <div className="mt-2 grid gap-2 sm:grid-cols-3">
            {(taxonomy?.skills || []).map((skill) => (
              <label key={skill.id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.skill_ids.includes(skill.id)}
                  onChange={() => set("skill_ids", toggleId(form.skill_ids, skill.id))}
                />
                {skill.name}
              </label>
            ))}
          </div>
        </div>

        <div>
          <Label htmlFor="admin_notes">Internal notes</Label>
          <Textarea id="admin_notes" rows={3} value={form.admin_notes} onChange={(e) => set("admin_notes", e.target.value)} />
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.featured} onChange={(e) => set("featured", e.target.checked)} />
          Feature on the hub
        </label>

        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={saving} className="bg-brand-orange text-white hover:bg-brand-orange/90">
            {saving ? "Saving…" : opportunityId ? "Save" : "Save draft"}
          </Button>
          {opportunityId && status !== "published" ? (
            <Button type="button" variant="outline" disabled={Boolean(acting)} onClick={() => runAction("publish")}>
              {acting === "publish" ? "Publishing…" : "Publish"}
            </Button>
          ) : null}
          {opportunityId && status === "published" ? (
            <Button type="button" variant="outline" disabled={Boolean(acting)} onClick={() => runAction("unpublish")}>
              Unpublish
            </Button>
          ) : null}
          {opportunityId && status === "published" ? (
            <Button
              type="button"
              variant="outline"
              disabled={Boolean(acting)}
              onClick={async () => {
                setActing("announce");
                setError(null);
                try {
                  const result = await announceAdminOpportunity(opportunityId, true);
                  if (result.status === "skipped" || result.status === "failed") {
                    setError(result.detail || "Telegram announcement was skipped.");
                  }
                } catch (err) {
                  setError(err instanceof ApiError ? err.detail : "Could not announce on Telegram.");
                } finally {
                  setActing(null);
                }
              }}
            >
              {acting === "announce" ? "Announcing…" : "Announce on Telegram"}
            </Button>
          ) : null}
          {opportunityId ? (
            <Button
              type="button"
              variant="outline"
              disabled={Boolean(acting)}
              onClick={async () => {
                setActing("assist");
                setError(null);
                try {
                  const result = await requestAdminReviewAssist(opportunityId);
                  setAssist(result);
                } catch (err) {
                  setError(err instanceof ApiError ? err.detail : "Review assist is not available.");
                } finally {
                  setActing(null);
                }
              }}
            >
              {acting === "assist" ? "Asking…" : "Ask AI for review notes"}
            </Button>
          ) : null}
          {opportunityId && status !== "rejected" ? (
            <Button type="button" variant="outline" disabled={Boolean(acting)} onClick={() => runAction("reject")}>
              Reject
            </Button>
          ) : null}
          {opportunityId && status !== "archived" ? (
            <Button type="button" variant="ghost" disabled={Boolean(acting)} onClick={() => runAction("archive")}>
              Archive
            </Button>
          ) : null}
        </div>
        {assist?.notes || assist?.risk_notes?.length ? (
          <div className="rounded-xl border bg-brand-surface/60 p-4 text-sm">
            <p className="font-medium">Review assist (does not publish)</p>
            {assist.provider ? (
              <p className="mt-1 text-xs text-muted-foreground">
                Notes from {assist.provider === "gemini" ? "Gemini" : "OpenAI"}
              </p>
            ) : null}
            {assist.notes ? <p className="mt-2 text-muted-foreground">{assist.notes}</p> : null}
            {assist.suggested_type ? <p className="mt-2">Suggested type: {assist.suggested_type}</p> : null}
            {assist.suggested_career_paths?.length ? (
              <p className="mt-1">Suggested paths: {assist.suggested_career_paths.join(", ")}</p>
            ) : null}
            {assist.risk_notes?.length ? (
              <ul className="mt-2 list-disc pl-5 text-muted-foreground">
                {assist.risk_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
        {opportunityId ? (
          <p className="text-xs text-muted-foreground">Current status: {status}. Internal trust status stays unverified until later review tooling.</p>
        ) : null}
      </form>
    </div>
  );
}
