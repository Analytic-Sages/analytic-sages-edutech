import type { MetadataRoute } from "next";
import { isOpportunitiesPublic } from "@/lib/feature-flags";
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
    "/verify-email",
    "/reset-password",
    "/staff-invite",
  ];
  if (!isOpportunitiesPublic()) {
    disallow.push("/opportunities", "/opportunities/");
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
