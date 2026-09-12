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

const selectBase =
  "flex h-10 w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50";

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

type PartnershipInquiryFormProps = {
  className?: string;
  /** Visual theme for light page sections vs navy CTA band. */
  variant?: "light" | "dark";
  /** Anchor id for CTAs (use once per page). */
  anchorId?: string;
  /** Prefix field ids when multiple forms exist on one page. */
  idPrefix?: string;
};

export function PartnershipInquiryForm({
  className,
  variant = "dark",
  anchorId,
  idPrefix = "partner",
}: PartnershipInquiryFormProps) {
  const [formError, setFormError] = useState<string | null>(null);
  const [sentTo, setSentTo] = useState<string | null>(null);
  const dark = variant === "dark";
  const fid = (name: string) => `${idPrefix}-${name}`;

  const labelClass = dark ? "text-white" : "text-foreground";
  const inputClass = dark
    ? "border-white/20 bg-white/5 text-white placeholder:text-white/40"
    : undefined;
  const selectClass = dark
    ? cn(selectBase, "border-white/20 bg-white/5 text-white dark:bg-input/30")
    : cn(selectBase, "dark:bg-input/30");
  const errorClass = dark ? "text-sm text-brand-orange" : "text-sm text-destructive";

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
      <div
        id={anchorId}
        className={cn(
          "rounded-2xl border p-6 sm:p-8",
          dark ? "border-white/15 bg-white/5" : "border-border bg-card",
          className
        )}
      >
        <h3
          className={cn(
            "font-heading text-xl font-semibold",
            dark ? "text-white" : "text-foreground"
          )}
        >
          Conversation started
        </h3>
        <p
          className={cn(
            "mt-3 text-sm leading-relaxed sm:text-base",
            dark ? "text-white/75" : "text-muted-foreground"
          )}
        >
          Thanks. We received your partnership inquiry and will reply to{" "}
          <span className={cn("font-medium", dark ? "text-white" : "text-foreground")}>
            {sentTo}
          </span>
          . For urgent matters, email{" "}
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
      id={anchorId}
      className={cn("space-y-5", className)}
      onSubmit={handleSubmit(onSubmit)}
      noValidate
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={fid("fullName")} className={labelClass}>
            Full Name *
          </Label>
          <Input
            id={fid("fullName")}
            autoComplete="name"
            className={inputClass}
            {...register("fullName")}
          />
          {errors.fullName ? <p className={errorClass}>{errors.fullName.message}</p> : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor={fid("workEmail")} className={labelClass}>
            Work Email *
          </Label>
          <Input
            id={fid("workEmail")}
            type="email"
            autoComplete="email"
            className={inputClass}
            {...register("workEmail")}
          />
          {errors.workEmail ? <p className={errorClass}>{errors.workEmail.message}</p> : null}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={fid("organization")} className={labelClass}>
            Company / Organization *
          </Label>
          <Input
            id={fid("organization")}
            autoComplete="organization"
            className={inputClass}
            {...register("organization")}
          />
          {errors.organization ? (
            <p className={errorClass}>{errors.organization.message}</p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor={fid("website")} className={labelClass}>
            Website *
          </Label>
          <Input
            id={fid("website")}
            placeholder="https://"
            className={inputClass}
            {...register("website")}
          />
          {errors.website ? <p className={errorClass}>{errors.website.message}</p> : null}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={fid("organizationType")} className={labelClass}>
            Organization Type *
          </Label>
          <select id={fid("organizationType")} className={selectClass} {...register("organizationType")}>
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
            <p className={errorClass}>{errors.organizationType.message}</p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor={fid("primaryEcosystem")} className={labelClass}>
            Primary Ecosystem / Protocol
          </Label>
          <Input id={fid("primaryEcosystem")} className={inputClass} {...register("primaryEcosystem")} />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor={fid("goal")} className={labelClass}>
          What are you looking to achieve? *
        </Label>
        <select
          id={fid("goal")}
          className={cn(selectClass, "h-auto min-h-10")}
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
        {errors.goal ? <p className={errorClass}>{errors.goal.message}</p> : null}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor={fid("programInterest")} className={labelClass}>
            Program Interest
          </Label>
          <select id={fid("programInterest")} className={selectClass} {...register("programInterest")}>
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
          <Label htmlFor={fid("targetRegion")} className={labelClass}>
            Target Region
          </Label>
          <select id={fid("targetRegion")} className={selectClass} {...register("targetRegion")}>
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
          <Label htmlFor={fid("timeline")} className={labelClass}>
            Timeline
          </Label>
          <select id={fid("timeline")} className={selectClass} {...register("timeline")}>
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
        <Label htmlFor={fid("additionalContext")} className={labelClass}>
          Additional Context
        </Label>
        <Textarea
          id={fid("additionalContext")}
          rows={4}
          className={inputClass}
          placeholder="Share priorities, technical stack, or anything that helps us prepare."
          {...register("additionalContext")}
        />
      </div>

      {formError ? <p className={errorClass}>{formError}</p> : null}

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
