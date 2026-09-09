"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { siteConfig } from "@/config/site";
import { ApiError, sendContactMessage } from "@/lib/api";
import { trackContact } from "@/lib/marketing-pixels";
import {
  organizationTypes,
  partnershipGoals,
  programInterests,
  targetRegions,
  timelines,
} from "@/lib/partner-with-us";
import { cn } from "@/lib/utils";

const schema = z.object({
  fullName: z.string().trim().min(2, "Enter your full name").max(120),
  workEmail: z.string().trim().email("Enter a valid work email"),
  organization: z.string().trim().min(2, "Enter your organization").max(160),
  website: z
    .string()
    .trim()
    .min(3, "Enter a website")
    .max(200)
    .refine((v) => /^(https?:\/\/)?[\w.-]+\.[a-z]{2,}(\/\S*)?$/i.test(v), {
      message: "Enter a valid website URL",
    }),
  organizationType: z.string().min(1, "Select an organization type"),
  primaryEcosystem: z.string().trim().max(160).optional(),
  goal: z.string().min(1, "Select what you want to achieve"),
  programInterest: z.string().optional(),
  targetRegion: z.string().optional(),
  timeline: z.string().optional(),
  additionalContext: z.string().trim().max(3500).optional(),
});

type FormData = z.infer<typeof schema>;

const selectClass =
  "flex h-10 w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30";

function buildSubject(data: FormData) {
  return `Partnership inquiry: ${data.organization} · ${data.goal}`.slice(0, 200);
}

function buildMessage(data: FormData) {
  const lines = [
    "Partnership inquiry from Partner With Us",
    "",
    `Full name: ${data.fullName}`,
    `Work email: ${data.workEmail}`,
    `Organization: ${data.organization}`,
    `Website: ${data.website}`,
    `Organization type: ${data.organizationType}`,
    `Primary ecosystem / protocol: ${data.primaryEcosystem?.trim() || "N/A"}`,
    `Looking to achieve: ${data.goal}`,
    `Program interest: ${data.programInterest || "N/A"}`,
    `Target region: ${data.targetRegion || "N/A"}`,
    `Timeline: ${data.timeline || "N/A"}`,
    "",
    "Additional context:",
    data.additionalContext?.trim() || "N/A",
  ];
  return lines.join("\n").slice(0, 4000);
}

export function PartnershipInquiryForm({ className }: { className?: string }) {
  const [formError, setFormError] = useState<string | null>(null);
  const [sentTo, setSentTo] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      organizationType: "",
      goal: "",
      programInterest: "",
      targetRegion: "",
      timeline: "",
      primaryEcosystem: "",
      additionalContext: "",
    },
  });

  async function onSubmit(data: FormData) {
    setFormError(null);
    try {
      await sendContactMessage({
        name: data.fullName,
        email: data.workEmail,
        subject: buildSubject(data),
        message: buildMessage(data),
      });
      trackContact();
      setSentTo(data.workEmail);
    } catch (err) {
      setFormError(
        err instanceof ApiError
          ? err.detail
          : "We could not send your inquiry. Please try again or email us directly."
      );
    }
  }

  if (sentTo) {
    return (
      <div className={cn("rounded-2xl border border-white/15 bg-white/5 p-6 sm:p-8", className)}>
        <h3 className="font-heading text-xl font-semibold text-white">Conversation started</h3>
        <p className="mt-3 text-sm leading-relaxed text-white/75 sm:text-base">
          Thanks. We received your partnership inquiry and will reply to{" "}
          <span className="font-medium text-white">{sentTo}</span>. For urgent matters, email{" "}
          <a
            href={`mailto:${siteConfig.emails.admin}`}
            className="font-medium text-brand-orange underline-offset-4 hover:underline"
          >
            {siteConfig.emails.admin}
          </a>
          .
        </p>
      </div>
    );
  }

  return (
    <form
      id="partner-inquiry"
      className={cn("space-y-5", className)}
      onSubmit={handleSubmit(onSubmit)}
      noValidate
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="fullName" className="text-white">
            Full Name *
          </Label>
          <Input
            id="fullName"
            autoComplete="name"
            className="border-white/20 bg-white/5 text-white placeholder:text-white/40"
            {...register("fullName")}
          />
          {errors.fullName ? (
            <p className="text-sm text-brand-orange">{errors.fullName.message}</p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="workEmail" className="text-white">
            Work Email *
          </Label>
          <Input
            id="workEmail"
            type="email"
            autoComplete="email"
            className="border-white/20 bg-white/5 text-white placeholder:text-white/40"
            {...register("workEmail")}
          />
          {errors.workEmail ? (
            <p className="text-sm text-brand-orange">{errors.workEmail.message}</p>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="organization" className="text-white">
            Company / Organization *
          </Label>
          <Input
            id="organization"
            autoComplete="organization"
            className="border-white/20 bg-white/5 text-white placeholder:text-white/40"
            {...register("organization")}
          />
          {errors.organization ? (
            <p className="text-sm text-brand-orange">{errors.organization.message}</p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="website" className="text-white">
            Website *
          </Label>
          <Input
            id="website"
            placeholder="https://"
            className="border-white/20 bg-white/5 text-white placeholder:text-white/40"
            {...register("website")}
          />
          {errors.website ? (
            <p className="text-sm text-brand-orange">{errors.website.message}</p>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="organizationType" className="text-white">
            Organization Type *
          </Label>
          <select
            id="organizationType"
            className={cn(selectClass, "border-white/20 bg-white/5 text-white")}
            {...register("organizationType")}
          >
            <option value="" className="text-foreground">
              Select type
            </option>
            {organizationTypes.map((opt) => (
              <option key={opt} value={opt} className="text-foreground">
                {opt}
              </option>
            ))}
          </select>
          {errors.organizationType ? (
            <p className="text-sm text-brand-orange">{errors.organizationType.message}</p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="primaryEcosystem" className="text-white">
            Primary Ecosystem / Protocol
          </Label>
          <Input
            id="primaryEcosystem"
            className="border-white/20 bg-white/5 text-white placeholder:text-white/40"
            {...register("primaryEcosystem")}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="goal" className="text-white">
          What are you looking to achieve? *
        </Label>
        <select
          id="goal"
          className={cn(selectClass, "h-auto min-h-10 border-white/20 bg-white/5 text-white")}
          {...register("goal")}
        >
          <option value="" className="text-foreground">
            Select a goal
          </option>
          {partnershipGoals.map((opt) => (
            <option key={opt} value={opt} className="text-foreground">
              {opt}
            </option>
          ))}
        </select>
        {errors.goal ? <p className="text-sm text-brand-orange">{errors.goal.message}</p> : null}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor="programInterest" className="text-white">
            Program Interest
          </Label>
          <select
            id="programInterest"
            className={cn(selectClass, "border-white/20 bg-white/5 text-white")}
            {...register("programInterest")}
          >
            <option value="" className="text-foreground">
              Optional
            </option>
            {programInterests.map((opt) => (
              <option key={opt} value={opt} className="text-foreground">
                {opt}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="targetRegion" className="text-white">
            Target Region
          </Label>
          <select
            id="targetRegion"
            className={cn(selectClass, "border-white/20 bg-white/5 text-white")}
            {...register("targetRegion")}
          >
            <option value="" className="text-foreground">
              Optional
            </option>
            {targetRegions.map((opt) => (
              <option key={opt} value={opt} className="text-foreground">
                {opt}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="timeline" className="text-white">
            Timeline
          </Label>
          <select
            id="timeline"
            className={cn(selectClass, "border-white/20 bg-white/5 text-white")}
            {...register("timeline")}
          >
            <option value="" className="text-foreground">
              Optional
            </option>
            {timelines.map((opt) => (
              <option key={opt} value={opt} className="text-foreground">
                {opt}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="additionalContext" className="text-white">
          Additional Context
        </Label>
        <Textarea
          id="additionalContext"
          rows={4}
          className="border-white/20 bg-white/5 text-white placeholder:text-white/40"
          placeholder="Share priorities, technical stack, or anything that helps us prepare."
          {...register("additionalContext")}
        />
      </div>

      {formError ? <p className="text-sm text-brand-orange">{formError}</p> : null}

      <Button
        type="submit"
        disabled={isSubmitting}
        className="h-12 w-full bg-brand-orange text-base font-semibold text-white hover:bg-brand-orange/90 sm:w-auto sm:px-10"
      >
        {isSubmitting ? "Sending…" : "Start the Conversation →"}
      </Button>
    </form>
  );
}
