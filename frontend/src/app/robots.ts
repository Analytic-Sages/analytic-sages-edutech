import type { MetadataRoute } from "next";
import { PUBLIC_SITE_ORIGIN } from "@/lib/program-pages";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: [
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
        "/explore",
        "/certificates",
        "/verify-email",
        "/reset-password",
        "/staff-invite",
      ],
    },
    sitemap: `${PUBLIC_SITE_ORIGIN}/sitemap.xml`,
    host: PUBLIC_SITE_ORIGIN,
  };
}
