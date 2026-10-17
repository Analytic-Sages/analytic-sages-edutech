"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ApiError,
  ensureSession,
  getMe,
  getMyPartnerProfile,
  getMyReferralApplication,
  getReferralEligibleCourses,
  getReferralProgramGuide,
  submitReferralPartnerApplication,
  type AuthUser,
  type PartnerPublic,
  type ReferralPartnerApplicationStatus,
  type ReferralProgramGuide,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const PROMOTION_CHANNELS = [
  "LinkedIn", "X", "Telegram", "WhatsApp", "Newsletter", "YouTube",
  "Community", "Events / workshops", "Other",
] as const;

export function PartnersPageContent() {
  const [accountUser, setAccountUser] = useState<AuthUser | null>(null);
  const [profile, setProfile] = useState<PartnerPublic | null>(null);
  const [application, setApplication] = useState<ReferralPartnerApplicationStatus | null>(null);
  const [courses, setCourses] = useState<{ id: string; slug: string; title: string; price: string; currency: string }[]>([]);
  const [guide, setGuide] = useState<ReferralProgramGuide | null>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [country, setCountry] = useState("");
  const [timezone, setTimezone] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [xProfile, setXProfile] = useState("");
  const [githubProfile, setGithubProfile] = useState("");
  const [youtubeProfile, setYoutubeProfile] = useState("");
  const [communities, setCommunities] = useState("");
  const [audienceSize, setAudienceSize] = useState("");
  const [engagement, setEngagement] = useState("");
  const [experience, setExperience] = useState("");
  const [partnershipExperience, setPartnershipExperience] = useState("");
  const [interestedCourses, setInterestedCourses] = useState<string[]>([]);
  const [channels, setChannels] = useState<string[]>([]);
  const [marketingPlan, setMarketingPlan] = useState("");
  const [terms, setTerms] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getReferralProgramGuide().then((row) => { if (!cancelled) setGuide(row); }).catch(() => null);
    getReferralEligibleCourses().then((rows) => {
      if (!cancelled) setCourses(rows);
    }).catch(() => {
      if (!cancelled) setCourses([]);
    });
    ensureSession().then(async (ok) => {
      if (!ok) { if (!cancelled) setLoading(false); return; }
      try {
        const [user, partner, app] = await Promise.all([
          getMe(), getMyPartnerProfile(), getMyReferralApplication(),
        ]);
        if (cancelled) return;
        setAccountUser(user);
        setProfile(partner);
        setApplication(app);
        setFullName(user.full_name?.trim() || "");
        setEmail(user.email || "");
      } catch {
        // Public applicants can apply without signing in; account data is optional.
      } finally {
        if (!cancelled) setLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);

  async function onApply(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!terms) {
      setError("Accept the referral partner terms before submitting.");
      return;
    }
    if (!email.trim()) {
      setError("Enter an email address the team can use to contact you.");
      return;
    }
    if (channels.length === 0) {
      setError("Choose at least one promotion channel.");
      return;
    }
    setSubmitting(true);
    try {
      const socialProfiles = [
        { platform: "X", url: xProfile.trim() },
        { platform: "GitHub", url: githubProfile.trim() },
        { platform: "YouTube", url: youtubeProfile.trim() },
      ].filter((row) => row.url);
      const created = await submitReferralPartnerApplication({
        full_name: fullName.trim(),
        email: email.trim(),
        country: country.trim() || undefined,
        timezone: timezone.trim() || undefined,
        linkedin_url: linkedin.trim() || undefined,
        social_profiles: socialProfiles,
        communities: communities.trim() || undefined,
        audience_size: audienceSize.trim() || undefined,
        audience_engagement: engagement.trim() || undefined,
        relevant_experience: experience.trim() || undefined,
        partnership_experience: partnershipExperience.trim() || undefined,
        interested_courses: interestedCourses,
        promotion_channels: channels,
        marketing_plan: marketingPlan.trim(),
        terms_accepted: terms,
        terms_version: guide?.terms_version || "referral-partner-v1",
      });
      setApplication(created);
      setSuccess("Application received. Our team will review it and contact you using the email provided.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not submit your application. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  function toggle(values: string[], value: string, setter: (next: string[]) => void) {
    setter(values.includes(value) ? values.filter((item) => item !== value) : [...values, value]);
  }

  return (
    <div>
      <section className="relative overflow-hidden border-b border-[#0B1F3A]/10 bg-gradient-to-br from-white via-[#F7F9FC] to-[#EEF3F9]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(241,90,36,0.08),transparent_45%),radial-gradient(ellipse_at_bottom_right,rgba(11,31,58,0.06),transparent_50%)]" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] lg:gap-12 lg:py-20">
          <div className="max-w-xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-orange">Referral Partner Programme</p>
            <h1 className="mt-3 font-[family-name:var(--font-display)] text-4xl font-semibold tracking-tight text-[#0B1F3A] sm:text-5xl">
              Connect People to Opportunities That Matter.
            </h1>
            <p className="mt-4 text-lg text-[#0B1F3A]/80">Help more learners build practical skills and earn commission on eligible paid course and programme payments.</p>
            <p className="mt-5 text-base leading-relaxed text-[#0B1F3A]/90">{guide?.program_overview || "Approved partners receive trackable course and campaign links. Applications are reviewed before activation."}</p>
            <div className="mt-6 space-y-2 text-sm text-[#0B1F3A]/80">
              <p>• One partner account can have multiple course and campaign links.</p>
              <p>• Applications are reviewed by the team; submission does not activate referral privileges.</p>
              <p>• Payouts remain subject to eligibility, minimum thresholds and admin approval.</p>
            </div>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              {profile?.status === "active" ? (
                <Link href="/partner" className={cn(buttonVariants(), "bg-brand-orange text-white hover:bg-brand-orange/90")}>Open partner dashboard →</Link>
              ) : (
                <a href="#partner-apply" className={cn(buttonVariants(), "bg-brand-orange text-white hover:bg-brand-orange/90")}>Apply to become a partner →</a>
              )}
              <Link href="/partners/leaderboard" className={cn(buttonVariants({ variant: "outline" }))}>View leaderboard</Link>
            </div>
          </div>
          <div className="relative mx-auto w-full max-w-xl lg:max-w-none">
            <Image src="/partners/referral-partner-hero.jpg" alt="Professionals connected around a global learning network" width={1200} height={750} priority className="h-auto w-full object-contain" />
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-3xl space-y-8 px-4 py-12 sm:px-6">
        {loading ? <p className="text-sm text-muted-foreground">Loading your application status…</p> : null}
        {guide ? <section className="space-y-3 rounded-lg border p-4 text-sm"><h2 className="font-semibold text-base">Programme terms and guidelines</h2><p>{guide.commission_policy}</p><p>{guide.attribution_policy}</p><p>{guide.payout_policy}</p><p>{guide.marketing_guidelines}</p><p className="text-muted-foreground">Terms version: {guide.terms_version} · Support: {guide.support_contact}</p></section> : null}
        {profile?.status === "active" ? (
          <div className="rounded-lg border p-5">
            <h2 className="font-semibold">You are an active Referral Partner</h2>
            <p className="mt-1 text-sm text-muted-foreground">Manage your referral links, performance and commission history from your dashboard.</p>
            <Link href="/partner" className={cn(buttonVariants(), "mt-4 bg-brand-orange text-white hover:bg-brand-orange/90")}>Open partner dashboard</Link>
          </div>
        ) : application ? (
          <div className="rounded-lg border p-5">
            <h2 className="font-semibold">Application received</h2>
            <p className="mt-2 text-sm text-muted-foreground">Status: <span className="font-medium capitalize text-foreground">{application.status.replaceAll("_", " ")}</span></p>
            <p className="mt-1 text-sm text-muted-foreground">We will contact {application.email} with the next steps. Submitting an application does not grant referral access.</p>
          </div>
        ) : (
          <section id="partner-apply" className="scroll-mt-24 space-y-5">
            <div>
              <h2 className="text-2xl font-semibold text-[#0B1F3A]">Apply to become a Referral Partner</h2>
              <p className="mt-2 text-sm text-muted-foreground">Tell us about your audience, the courses you can promote and how you would reach potential learners. A large audience is not required; relevant and engaged communities matter.</p>
            </div>
            <form onSubmit={onApply} className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2"><Label htmlFor="partner-full-name">Full name *</Label><Input id="partner-full-name" value={fullName} onChange={(e) => setFullName(e.target.value)} required minLength={2} maxLength={160} /></div>
                <div className="space-y-2"><Label htmlFor="partner-email">Email address *</Label><Input id="partner-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required maxLength={320} disabled={!!accountUser?.email} /></div>
                <div className="space-y-2"><Label htmlFor="partner-country">Country</Label><Input id="partner-country" value={country} onChange={(e) => setCountry(e.target.value)} maxLength={100} /></div>
                <div className="space-y-2"><Label htmlFor="partner-timezone">Time zone</Label><Input id="partner-timezone" value={timezone} onChange={(e) => setTimezone(e.target.value)} placeholder="e.g. Africa/Lagos" maxLength={100} /></div>
                <div className="space-y-2 sm:col-span-2"><Label htmlFor="partner-linkedin">LinkedIn profile</Label><Input id="partner-linkedin" type="url" value={linkedin} onChange={(e) => setLinkedin(e.target.value)} placeholder="https://www.linkedin.com/in/…" /></div>
                <div className="space-y-2"><Label htmlFor="partner-x">X profile</Label><Input id="partner-x" value={xProfile} onChange={(e) => setXProfile(e.target.value)} placeholder="Profile URL" /></div>
                <div className="space-y-2"><Label htmlFor="partner-github">GitHub profile</Label><Input id="partner-github" value={githubProfile} onChange={(e) => setGithubProfile(e.target.value)} placeholder="Profile URL" /></div>
                <div className="space-y-2 sm:col-span-2"><Label htmlFor="partner-youtube">YouTube / other profile</Label><Input id="partner-youtube" value={youtubeProfile} onChange={(e) => setYoutubeProfile(e.target.value)} placeholder="Profile URL" /></div>
              </div>

              <div className="space-y-2"><Label htmlFor="partner-communities">Communities, organizations or audiences you can reach</Label><textarea id="partner-communities" value={communities} onChange={(e) => setCommunities(e.target.value)} maxLength={2000} rows={3} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" placeholder="Name relevant communities and explain your access to them." /></div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2"><Label htmlFor="partner-audience">Approximate audience size</Label><Input id="partner-audience" value={audienceSize} onChange={(e) => setAudienceSize(e.target.value)} maxLength={80} placeholder="e.g. 400 community members" /></div>
                <div className="space-y-2"><Label htmlFor="partner-engagement">Audience engagement</Label><Input id="partner-engagement" value={engagement} onChange={(e) => setEngagement(e.target.value)} maxLength={2000} placeholder="How does your audience engage?" /></div>
              </div>
              <div className="space-y-2"><Label htmlFor="partner-experience">Referral, sales, community, or event experience</Label><textarea id="partner-experience" value={experience} onChange={(e) => setExperience(e.target.value)} rows={3} maxLength={3000} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" /></div>
              <div className="space-y-2"><Label htmlFor="partner-partnership-experience">Partnerships, sponsorships or fundraising experience</Label><textarea id="partner-partnership-experience" value={partnershipExperience} onChange={(e) => setPartnershipExperience(e.target.value)} rows={2} maxLength={2000} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" /></div>

              <fieldset className="space-y-3">
                <legend className="text-sm font-medium">Courses you are interested in promoting</legend>
                {courses.length ? <div className="grid gap-2 sm:grid-cols-2">{courses.map((course) => <label key={course.id} className="flex items-start gap-2 text-sm"><input type="checkbox" checked={interestedCourses.includes(course.slug)} onChange={() => toggle(interestedCourses, course.slug, setInterestedCourses)} className="mt-1" /><span>{course.title} — {course.currency} {course.price}</span></label>)}</div> : <p className="text-sm text-muted-foreground">Course choices will be available when the programme is open.</p>}
              </fieldset>

              <fieldset className="space-y-3">
                <legend className="text-sm font-medium">Proposed promotion channels *</legend>
                <div className="grid gap-2 sm:grid-cols-2">{PROMOTION_CHANNELS.map((channel) => <label key={channel} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={channels.includes(channel)} onChange={() => toggle(channels, channel, setChannels)} /><span>{channel}</span></label>)}</div>
              </fieldset>
              <div className="space-y-2"><Label htmlFor="partner-marketing-plan">How would you promote the courses? *</Label><textarea id="partner-marketing-plan" value={marketingPlan} onChange={(e) => setMarketingPlan(e.target.value)} rows={5} required minLength={30} maxLength={3000} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" placeholder="Describe your audience, planned content or outreach, channels, and how you will communicate course value honestly." /></div>

              <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} className="mt-1" required /><span>I agree to the Referral Partner programme terms ({guide?.terms_version || "referral-partner-v1"}) and marketing guidelines. I will not spam, mislead learners, or promise unapproved benefits. I understand that approval and onboarding are separate from activation.</span></label>
              {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
              {success ? <p role="status" className="text-sm text-green-700">{success}</p> : null}
              <Button type="submit" disabled={submitting || !terms || channels.length === 0} className="bg-brand-orange text-white hover:bg-brand-orange/90">{submitting ? "Submitting…" : "Submit application"}</Button>
              <p className="text-xs text-muted-foreground">Your application is reviewed by the Analytic Sages team. Submission does not activate referral links or grant commission privileges.</p>
            </form>
          </section>
        )}
      </div>
    </div>
  );
}
