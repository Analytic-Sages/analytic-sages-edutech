import { apiFetch } from "@/lib/api";

export type OpportunityType =
  | "job"
  | "internship"
  | "fellowship"
  | "hackathon"
  | "grant"
  | "bounty"
  | "challenge"
  | "research"
  | "other";

export type HackathonEventFormat = "online" | "in_person" | "hybrid" | "unknown";
export type HackathonPhase = "open" | "upcoming" | "ongoing" | "ended" | "unknown";

export type HackathonDetails = {
  short_description?: string | null;
  registration_url?: string | null;
  website_url?: string | null;
  registration_open_at?: string | null;
  registration_deadline?: string | null;
  start_at?: string | null;
  end_at?: string | null;
  submission_deadline?: string | null;
  event_format: HackathonEventFormat;
  prize_pool_amount?: number | null;
  prize_currency?: string | null;
  prize_pool_raw?: string | null;
  team_size_min?: number | null;
  team_size_max?: number | null;
  tags?: string[];
  tracks?: string[];
  derived_phase?: HackathonPhase | null;
  registration_closes_in_days?: number | null;
};

export type BountyCategory =
  | "bug"
  | "security"
  | "development"
  | "content"
  | "design"
  | "research"
  | "quest"
  | "other"
  | "unknown";

export type BountyPhase = "open" | "closing_soon" | "ended" | "unknown";

export type BountyDetails = {
  short_description?: string | null;
  listing_url?: string | null;
  reward_amount?: number | null;
  reward_token?: string | null;
  reward_currency?: string | null;
  reward_raw?: string | null;
  category: BountyCategory;
  opens_at?: string | null;
  deadline?: string | null;
  winners_announced?: boolean;
  skills?: string[];
  tags?: string[];
  chain_focus?: string | null;
  derived_phase?: BountyPhase | null;
  closes_in_days?: number | null;
};

export type WorkplaceType = "remote" | "hybrid" | "onsite";
export type LocationRegion =
  | "global"
  | "africa"
  | "nigeria"
  | "europe"
  | "north_america"
  | "asia"
  | "remote";
export type ExperienceLevel = "intern" | "junior" | "mid" | "senior" | "lead" | "not_specified";
export type OpportunityStatus = "draft" | "published" | "rejected" | "expired" | "archived";
export type PublicBadge = "none" | "official_source" | "partner" | "source_checked" | "community_submission";

export type CareerPathPublic = {
  id: string;
  name: string;
  slug: string;
  description: string;
  is_primary?: boolean;
  relevance_score?: number | null;
};

export type SkillPublic = {
  id: string;
  name: string;
  slug: string;
  category: string;
  importance?: string;
};

export type OpportunityCard = {
  id: string;
  slug: string;
  title: string;
  organization_name: string;
  organization_logo_url?: string | null;
  compensation_text?: string | null;
  opportunity_type: OpportunityType;
  employment_type: string | null;
  experience_level: ExperienceLevel;
  location: string;
  location_raw?: string | null;
  location_scope?: string | null;
  country: string | null;
  region: LocationRegion | null;
  workplace_type: WorkplaceType;
  deadline: string | null;
  published_at: string | null;
  featured: boolean;
  closing_soon: boolean;
  public_badge: PublicBadge;
  application_domain: string | null;
  primary_career_path: CareerPathPublic | null;
  skills: SkillPublic[];
  source?: { id: string | null; name: string; source_type: string } | null;
  saved?: boolean;
  applied?: boolean;
  match_score?: number | null;
  hackathon?: HackathonDetails | null;
  bounty?: BountyDetails | null;
};

export type OpportunityDetail = OpportunityCard & {
  description: string;
  requirements: string;
  responsibilities: string | null;
  benefits: string | null;
  application_url: string;
  source_url: string | null;
  career_paths: CareerPathPublic[];
  source: { id: string | null; name: string; source_type: string } | null;
  updated_at: string;
  similar: OpportunityCard[];
};

export type FilterOption = { value: string; label: string; count: number };
export type TaxonomyOption = { id: string; slug: string; name: string; count: number };

export type OpportunityFilters = {
  types: FilterOption[];
  career_paths: TaxonomyOption[];
  skills: TaxonomyOption[];
  workplace_types: FilterOption[];
  experience_levels: FilterOption[];
  regions: FilterOption[];
};

export type OpportunityList = {
  items: OpportunityCard[];
  total: number;
  limit: number;
  offset: number;
};

export type OpportunityAdmin = {
  id: string;
  slug: string;
  title: string;
  organization_name: string;
  organization_logo_url?: string | null;
  compensation_text?: string | null;
  description: string;
  requirements: string;
  responsibilities: string | null;
  benefits: string | null;
  opportunity_type: OpportunityType;
  employment_type: string | null;
  experience_level: ExperienceLevel;
  location: string;
  country: string | null;
  region: LocationRegion | null;
  workplace_type: WorkplaceType;
  application_url: string;
  source_url: string | null;
  deadline: string | null;
  published_at: string | null;
  status: OpportunityStatus;
  source_id: string | null;
  source: {
    id: string;
    name: string;
    website_url: string | null;
    source_type: string;
    trust_level: string;
    automation_enabled: boolean;
    auto_publish_allowed: boolean;
    is_active: boolean;
  } | null;
  trust_score: number | null;
  trust_status: string;
  public_badge: PublicBadge;
  featured: boolean;
  admin_notes: string;
  is_manual?: boolean;
  external_id?: string | null;
  relevance_score?: number | null;
  match_reasons?: string[];
  matched_career_tracks?: string[];
  duplicate_of_id?: string | null;
  duplicate_confidence?: string | null;
  location_raw?: string | null;
  location_scope?: string | null;
  career_paths: CareerPathPublic[];
  skills: SkillPublic[];
  risk_flags?: OpportunityRiskFlag[];
  telegram_announced_at?: string | null;
  review_assist?: {
    notes?: string | null;
    suggested_type?: string | null;
    suggested_career_paths?: string[];
    risk_notes?: string[];
    generated_at?: string;
    provider?: string;
  };
  created_at: string;
  updated_at: string;
};

export type OpportunityRiskFlag = {
  flag_type: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  is_resolved: boolean;
};

export type OpportunityAdminOverview = {
  published: number;
  draft: number;
  review: number;
  rejected: number;
  expired: number;
  ingested_today: number;
};

export type OpportunitySyncRun = {
  id: string;
  source_id: string;
  started_at: string;
  completed_at: string | null;
  status: "running" | "completed" | "failed";
  found: number;
  created: number;
  updated: number;
  duplicates: number;
  rejected: number;
  error_message: string | null;
  triggered_by: string | null;
};

export type OpportunitySyncAllResult = {
  runs: OpportunitySyncRun[];
  sources: number;
  found: number;
  created: number;
  updated: number;
  duplicates: number;
  rejected: number;
  failed: number;
  published: false;
};

export type OpportunitySourceAdmin = {
  id: string;
  name: string;
  website_url: string | null;
  source_type: string;
  trust_level: string;
  automation_enabled: boolean;
  auto_publish_allowed: boolean;
  connector_type: string;
  config: Record<string, string>;
  last_checked_at: string | null;
  last_error: string | null;
  health_status: string;
  is_active: boolean;
  latest_sync: OpportunitySyncRun | null;
  published_count?: number;
  rejected_count?: number;
  review_count?: number;
  created_at: string;
  updated_at: string;
};

export type AdminTaxonomy = {
  career_paths: CareerPathPublic[];
  skills: SkillPublic[];
  sources: OpportunityAdmin["source"][];
};

export const TYPE_ROUTES: { href: string; type: OpportunityType; label: string }[] = [
  { href: "/opportunities/jobs", type: "job", label: "Jobs" },
  { href: "/opportunities/internships", type: "internship", label: "Internships" },
  { href: "/opportunities/fellowships", type: "fellowship", label: "Fellowships" },
  { href: "/opportunities/hackathons", type: "hackathon", label: "Hackathons" },
  { href: "/opportunities/grants", type: "grant", label: "Grants" },
  { href: "/opportunities/bounties", type: "bounty", label: "Bounties" },
  { href: "/opportunities/research", type: "research", label: "Research" },
];

export const TYPE_LABELS: Record<OpportunityType, string> = {
  job: "Job",
  internship: "Internship",
  fellowship: "Fellowship",
  hackathon: "Hackathon",
  grant: "Grant",
  bounty: "Bounty",
  challenge: "Challenge",
  research: "Research",
  other: "Other",
};

export const HACKATHON_FORMAT_LABELS: Record<HackathonEventFormat, string> = {
  online: "Online",
  in_person: "In person",
  hybrid: "Hybrid",
  unknown: "Format TBA",
};


export const WORKPLACE_LABELS: Record<WorkplaceType, string> = {
  remote: "Remote",
  hybrid: "Hybrid",
  onsite: "Onsite",
};

export const REGION_LABELS: Record<LocationRegion, string> = {
  global: "Global",
  africa: "Africa",
  nigeria: "Nigeria",
  europe: "Europe",
  north_america: "North America",
  asia: "Asia",
  remote: "Remote",
};

export const BADGE_COPY: Record<
  Exclude<PublicBadge, "none">,
  { label: string; meaning: string }
> = {
  official_source: {
    label: "Verified Source",
    meaning: "Sourced from the organization official website, careers page, or official program channel.",
  },
  partner: {
    label: "Partner",
    meaning: "Provided directly by an approved Analytic Sages partner. Always verify the destination yourself.",
  },
  source_checked: {
    label: "Trusted Platform",
    meaning: "Listed on an established third-party platform. Analytic Sages has not independently verified the employer.",
  },
  community_submission: {
    label: "Community",
    meaning: "Submitted through a community channel and reviewed before publication. Extra caution is warranted.",
  },
};

export const SAFETY_NOTICE =
  "Analytic Sages aggregates opportunities from external sources and does not guarantee the accuracy, availability, or legitimacy of third-party listings. Always conduct your own due diligence.";

export const APPLY_SAFETY_POINTS = [
  "Never pay money to secure a job or internship.",
  "Be cautious of requests to install unknown software.",
  "Verify the domain belongs to the organization.",
  "Never share wallet seed phrases, private keys, or unnecessary financial information.",
];

export function applyCtaLabel(type: OpportunityType) {
  if (type === "hackathon") return "Join hackathon";
  if (type === "fellowship") return "Apply for fellowship";
  if (type === "grant") return "View grant";
  if (type === "bounty") return "Complete bounty";
  return "Apply now";
}

export function formatPosted(value: string | null) {
  if (!value) return null;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

/** Relative time for listing cards, e.g. "2 days ago". */
export function formatPostedRelative(value: string | null) {
  if (!value) return null;
  const then = new Date(value).getTime();
  if (Number.isNaN(then)) return null;
  const diffMs = Date.now() - then;
  if (diffMs < 0) return "just now";
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 60) return minutes <= 1 ? "just now" : `${minutes} minutes ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return hours === 1 ? "1 hour ago" : `${hours} hours ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "1 day ago";
  if (days < 14) return `${days} days ago`;
  if (days < 45) {
    const weeks = Math.floor(days / 7);
    return weeks === 1 ? "1 week ago" : `${weeks} weeks ago`;
  }
  return formatPosted(value);
}

export function compensationLabel(opportunity: OpportunityCard): string | null {
  if (opportunity.compensation_text?.trim()) return opportunity.compensation_text.trim();
  const prize = opportunity.hackathon?.prize_pool_raw || opportunity.bounty?.reward_raw;
  if (prize?.trim()) return prize.trim();
  if (opportunity.opportunity_type === "hackathon") return "Prize pool";
  if (opportunity.opportunity_type === "grant") return "Funding";
  if (opportunity.opportunity_type === "bounty") return "Reward";
  if (opportunity.opportunity_type === "fellowship") return "Stipend TBA";
  return null;
}

export function viewCtaLabel(type: OpportunityType) {
  if (type === "hackathon") return "Explore";
  if (type === "grant") return "View grant";
  if (type === "bounty") return "View bounty";
  if (type === "fellowship") return "View";
  return "View";
}

export type LearningPathCta = {
  title: string;
  body: string;
  href: string;
};

/** Map career paths to Analytic Sages programmes learners can explore. */
export function learningPathForOpportunity(opportunity: {
  primary_career_path: CareerPathPublic | null;
  career_paths?: CareerPathPublic[];
  skills: SkillPublic[];
}): LearningPathCta | null {
  const paths = [
    opportunity.primary_career_path,
    ...(opportunity.career_paths || []),
  ].filter(Boolean) as CareerPathPublic[];
  const slugs = new Set(paths.map((p) => p.slug));
  if (slugs.has("blockchain-data-engineering")) {
    return {
      title: "Blockchain Data Engineering",
      body: "Learn Python, SQL, Web3.py, dbt, orchestration and onchain data pipelines.",
      href: "/programs/blockchain-data-engineering",
    };
  }
  if (slugs.has("onchain-data-analytics")) {
    return {
      title: "SQL Blockchain Data Analytics",
      body: "Practice SQL on real blockchain data and build practical analytics projects.",
      href: "/programs/cohort-9-sql-blockchain-data-analytics",
    };
  }
  if (
    slugs.has("applied-ai") ||
    slugs.has("agentic-systems") ||
    slugs.has("ai-automation")
  ) {
    return {
      title: "Instructor-led AI programmes",
      body: "Build applied AI, agent, and automation skills through live Analytic Sages cohorts.",
      href: "/instructor-led",
    };
  }
  if (
    opportunity.skills.some((s) =>
      ["python", "sql", "dbt", "web3", "kafka", "airflow"].includes(s.slug),
    )
  ) {
    return {
      title: "Blockchain Data Engineering",
      body: "Missing pipeline skills? Learn the stack this opportunity asks for.",
      href: "/programs/blockchain-data-engineering",
    };
  }
  return null;
}

export function organizationInitials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase();
}

export type OpportunityQuery = {
  q?: string;
  opportunity_type?: OpportunityType;
  career_path?: string;
  skill?: string;
  workplace_type?: WorkplaceType;
  employment_type?: string;
  region?: LocationRegion;
  event_format?: HackathonEventFormat;
  hackathon_phase?: HackathonPhase;
  bounty_category?: BountyCategory;
  bounty_phase?: BountyPhase;
  sort?: "newest" | "deadline" | "featured" | "closing_soon" | "matched" | "hackathon" | "bounty";
  limit?: number;
  offset?: number;
};

function queryString(params: OpportunityQuery) {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.opportunity_type) search.set("opportunity_type", params.opportunity_type);
  if (params.career_path) search.set("career_path", params.career_path);
  if (params.skill) search.set("skill", params.skill);
  if (params.workplace_type) search.set("workplace_type", params.workplace_type);
  if (params.employment_type) search.set("employment_type", params.employment_type);
  if (params.region) search.set("region", params.region);
  if (params.event_format) search.set("event_format", params.event_format);
  if (params.hackathon_phase) search.set("hackathon_phase", params.hackathon_phase);
  if (params.bounty_category) search.set("bounty_category", params.bounty_category);
  if (params.bounty_phase) search.set("bounty_phase", params.bounty_phase);
  if (params.sort) search.set("sort", params.sort);
  if (params.limit) search.set("limit", String(params.limit));
  if (params.offset) search.set("offset", String(params.offset));
  const value = search.toString();
  return value ? `?${value}` : "";
}

export function listOpportunities(params: OpportunityQuery = {}) {
  return apiFetch<OpportunityList>(`/api/v1/opportunities${queryString(params)}`);
}

export function getOpportunityFilters() {
  return apiFetch<OpportunityFilters>("/api/v1/opportunities/filters", { auth: false });
}

export function getOpportunity(slug: string) {
  return apiFetch<OpportunityDetail>(`/api/v1/opportunities/${encodeURIComponent(slug)}`, {
    auth: false,
  });
}

export function getAdminOpportunities(
  params: { q?: string; status?: OpportunityStatus; review?: boolean } = {},
) {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.status) search.set("status", params.status);
  if (params.review) search.set("review", "true");
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return apiFetch<{ items: OpportunityAdmin[]; total: number }>(`/api/v1/admin/opportunities${suffix}`);
}

export function getAdminOpportunityOverview() {
  return apiFetch<OpportunityAdminOverview>("/api/v1/admin/opportunities/overview");
}

export function getAdminOpportunity(id: string) {
  return apiFetch<OpportunityAdmin>(`/api/v1/admin/opportunities/${encodeURIComponent(id)}`);
}

export function getAdminOpportunityTaxonomy() {
  return apiFetch<AdminTaxonomy>("/api/v1/admin/opportunities/taxonomy");
}

export type OpportunityWritePayload = {
  slug?: string | null;
  title: string;
  organization_name: string;
  organization_logo_url?: string | null;
  compensation_text?: string | null;
  description: string;
  requirements: string;
  responsibilities?: string | null;
  benefits?: string | null;
  opportunity_type: OpportunityType;
  employment_type?: string | null;
  experience_level: ExperienceLevel;
  location: string;
  country?: string | null;
  region?: LocationRegion | null;
  workplace_type: WorkplaceType;
  application_url: string;
  source_url?: string | null;
  deadline?: string | null;
  source_id?: string | null;
  public_badge: PublicBadge;
  featured: boolean;
  admin_notes?: string;
  career_path_ids: string[];
  skill_ids: string[];
};

export function createAdminOpportunity(payload: OpportunityWritePayload) {
  return apiFetch<OpportunityAdmin>("/api/v1/admin/opportunities", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAdminOpportunity(id: string, payload: Partial<OpportunityWritePayload>) {
  return apiFetch<OpportunityAdmin>(`/api/v1/admin/opportunities/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function publishAdminOpportunity(id: string, notes?: string) {
  return apiFetch<OpportunityAdmin>(`/api/v1/admin/opportunities/${encodeURIComponent(id)}/publish`, {
    method: "POST",
    body: JSON.stringify({ notes: notes || null }),
  });
}

export type OpportunityBulkPublishResult = {
  published: number;
  skipped: number;
  published_ids: string[];
  skipped_items: { id: string; title: string; reason: string }[];
};

export function bulkPublishAdminOpportunities(
  opportunityIds: string[],
  opts?: { notes?: string; includeHighRisk?: boolean },
) {
  return apiFetch<OpportunityBulkPublishResult>("/api/v1/admin/opportunities/bulk-publish", {
    method: "POST",
    body: JSON.stringify({
      opportunity_ids: opportunityIds,
      notes: opts?.notes ?? null,
      include_high_risk: opts?.includeHighRisk ?? false,
    }),
  });
}

export function unpublishAdminOpportunity(id: string, notes?: string) {
  return apiFetch<OpportunityAdmin>(`/api/v1/admin/opportunities/${encodeURIComponent(id)}/unpublish`, {
    method: "POST",
    body: JSON.stringify({ notes: notes || null }),
  });
}

export function rejectAdminOpportunity(id: string, notes?: string) {
  return apiFetch<OpportunityAdmin>(`/api/v1/admin/opportunities/${encodeURIComponent(id)}/reject`, {
    method: "POST",
    body: JSON.stringify({ notes: notes || null }),
  });
}

export function archiveAdminOpportunity(id: string, notes?: string) {
  return apiFetch<OpportunityAdmin>(`/api/v1/admin/opportunities/${encodeURIComponent(id)}/archive`, {
    method: "POST",
    body: JSON.stringify({ notes: notes || null }),
  });
}

export function listAdminOpportunitySources() {
  return apiFetch<{ items: OpportunitySourceAdmin[]; total: number }>("/api/v1/admin/opportunity-sources");
}

export function createAdminOpportunitySource(payload: {
  name: string;
  website_url?: string | null;
  trust_level: "high" | "medium" | "low";
  automation_enabled: boolean;
  auto_publish_allowed: boolean;
  connector_type:
    | "rss"
    | "greenhouse"
    | "ashby"
    | "lever"
    | "ethglobal"
    | "colosseum"
    | "devpost"
    | "devfolio"
    | "dorahacks"
    | "encode"
    | "superteam";
  config: Record<string, string>;
  is_active?: boolean;
}) {
  return apiFetch<OpportunitySourceAdmin>("/api/v1/admin/opportunity-sources", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAdminOpportunitySource(
  id: string,
  payload: Partial<{
    name: string;
    website_url: string | null;
    trust_level: "high" | "medium" | "low";
    automation_enabled: boolean;
    auto_publish_allowed: boolean;
    is_active: boolean;
    config: Record<string, string>;
  }>,
) {
  return apiFetch<OpportunitySourceAdmin>(`/api/v1/admin/opportunity-sources/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function syncAdminOpportunitySource(id: string) {
  return apiFetch<OpportunitySyncRun>(`/api/v1/admin/opportunity-sources/${encodeURIComponent(id)}/sync`, {
    method: "POST",
  });
}

export function syncAdminOpportunitySources() {
  return apiFetch<OpportunitySyncAllResult>("/api/v1/admin/opportunities/sync-sources", {
    method: "POST",
  });
}

export function listAdminOpportunitySyncRuns(id: string) {
  return apiFetch<{ items: OpportunitySyncRun[]; total: number }>(
    `/api/v1/admin/opportunity-sources/${encodeURIComponent(id)}/sync-runs`,
  );
}

export type OpportunitySaveItem = {
  id: string;
  opportunity_id: string;
  state: "saved" | "applied";
  closed: boolean;
  created_at: string;
  opportunity: OpportunityCard;
};

export function listMyOpportunities(bucket: "saved" | "applied" | "closed" = "saved") {
  return apiFetch<{ items: OpportunitySaveItem[]; total: number }>(
    `/api/v1/me/opportunities?bucket=${encodeURIComponent(bucket)}`,
  );
}

export function saveOpportunity(id: string) {
  return apiFetch<OpportunitySaveItem>(`/api/v1/me/opportunities/${encodeURIComponent(id)}/save`, {
    method: "POST",
  });
}

export function unsaveOpportunity(id: string) {
  return apiFetch<void>(`/api/v1/me/opportunities/${encodeURIComponent(id)}/save`, { method: "DELETE" });
}

export function markOpportunityApplied(id: string) {
  return apiFetch<OpportunitySaveItem>(`/api/v1/me/opportunities/${encodeURIComponent(id)}/applied`, {
    method: "POST",
  });
}

export function getMyOpportunityInterests() {
  return apiFetch<{ career_paths: CareerPathPublic[] }>("/api/v1/me/opportunity-interests");
}

export function updateMyOpportunityInterests(career_path_ids: string[]) {
  return apiFetch<{ career_paths: CareerPathPublic[] }>("/api/v1/me/opportunity-interests", {
    method: "PUT",
    body: JSON.stringify({ career_path_ids }),
  });
}

export function announceAdminOpportunity(id: string, force = false) {
  const suffix = force ? "?force=true" : "";
  return apiFetch<{ status: string; detail?: string; announced_at?: string }>(
    `/api/v1/admin/opportunities/${encodeURIComponent(id)}/announce${suffix}`,
    { method: "POST" },
  );
}

export function requestAdminReviewAssist(id: string) {
  return apiFetch<{
    configured: boolean;
    notes: string | null;
    suggested_type: string | null;
    suggested_career_paths: string[];
    risk_notes: string[];
    generated_at: string | null;
    provider: string | null;
  }>(`/api/v1/admin/opportunities/${encodeURIComponent(id)}/review-assist`, { method: "POST" });
}

export const DISCOVERY_TYPES: OpportunityType[] = [
  "internship",
  "fellowship",
  "hackathon",
  "challenge",
  "grant",
  "bounty",
  "research",
];

export type OpportunityDiscoverCandidate = {
  title: string;
  organization_name: string;
  opportunity_type: OpportunityType;
  application_url: string;
  source_url: string | null;
  description: string;
  why_relevant: string;
  location: string;
  deadline: string | null;
  career_path_slugs: string[];
  already_imported: boolean;
  source_host: string | null;
};

export type OpportunityDiscoverResponse = {
  configured: boolean;
  grounded: boolean;
  never_publishes: boolean;
  types_updated: number;
  dropped: number;
  candidates: OpportunityDiscoverCandidate[];
  provider: string | null;
  notes: string | null;
};

export function discoverAdminOpportunities(types: OpportunityType[], query?: string) {
  return apiFetch<OpportunityDiscoverResponse>("/api/v1/admin/opportunities/discover", {
    method: "POST",
    body: JSON.stringify({ types, query: query || null }),
  });
}

export function importAdminDiscoveredOpportunities(candidates: OpportunityDiscoverCandidate[]) {
  return apiFetch<{ imported: number; skipped: number; opportunity_ids: string[]; published: boolean }>(
    "/api/v1/admin/opportunities/discover/import",
    {
      method: "POST",
      body: JSON.stringify({ candidates }),
    },
  );
}

export function reclassifyAdminOpportunityTypes() {
  return apiFetch<{ updated: number }>("/api/v1/admin/opportunities/reclassify-types", { method: "POST" });
}

export function sendAdminOpportunityDigest(force = false) {
  const suffix = force ? "?force=true" : "";
  return apiFetch<{ status: string; listing_count: number; detail?: string }>(
    `/api/v1/admin/opportunities/digest${suffix}`,
    { method: "POST" },
  );
}

export function formatDeadline(value: string | null) {
  if (!value) return "Open";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function typeFromPath(segment: string): OpportunityType | null {
  const match = TYPE_ROUTES.find((item) => item.href === `/opportunities/${segment}`);
  return match?.type ?? null;
}
