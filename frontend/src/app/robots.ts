import type { MetadataRoute } from "next";
import { isOpportunitiesPublic, isPartnersPublic } from "@/lib/feature-flags";
import { PUBLIC_SITE_ORIGIN } from "@/lib/program-pages";

export default function robots(): MetadataRoute.Robots {
  const disallow = [
    "/admin",
    "/admin/",
    "/dashboard",
    "/dashboard/",
    "/classroom",
    "/classroom/",
    "/staff",
    "/staff/",
    "/checkout",
    "/checkout/",
    "/learn",
    "/learn/",
    "/my-courses",
    "/my-events",
    "/my-opportunities",
    "/explore",
    "/certificates",
    "/studio",
    "/studio/",
    "/partner",
    "/partner/",
    "/verify-email",
    "/reset-password",
    "/staff-invite",
  ];
  if (!isOpportunitiesPublic()) {
    disallow.push("/opportunities", "/opportunities/");
  }
  if (!isPartnersPublic()) {
    disallow.push("/partners", "/partners/", "/ref", "/ref/");
  }
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow,
    },
    sitemap: `${PUBLIC_SITE_ORIGIN}/sitemap.xml`,
    host: PUBLIC_SITE_ORIGIN,
  };
}
