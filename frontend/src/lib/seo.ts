import type { Metadata } from "next";
import { PUBLIC_SITE_ORIGIN } from "@/lib/program-pages";
import { siteConfig } from "@/config/site";

export const DEFAULT_OG_IMAGE = "/4.png";
export const ORGANIZATION_LOGO = "/logo-colored.png";

export function absoluteUrl(path = "/"): string {
  if (!path || path === "/") return PUBLIC_SITE_ORIGIN;
  return `${PUBLIC_SITE_ORIGIN}${path.startsWith("/") ? path : `/${path}`}`;
}

export function absoluteAssetUrl(src: string): string {
  if (src.startsWith("http://") || src.startsWith("https://")) return src;
  return `${PUBLIC_SITE_ORIGIN}${src.startsWith("/") ? src : `/${src}`}`;
}

export function brandedTitle(title: string): string {
  if (title === siteConfig.seoTitle || title === "Analytic Sages" || title.endsWith(" | Analytic Sages")) {
    return title;
  }
  return `${title} | Analytic Sages`;
}

type PageMetadataInput = {
  title: string;
  description: string;
  path: string;
  image?: string | null;
  /** Homepage should not become "Analytic Sages | Analytic Sages". */
  absoluteTitle?: boolean;
  type?: "website" | "article";
};

export function pageMetadata({
  title,
  description,
  path,
  image,
  absoluteTitle = false,
  type = "website",
}: PageMetadataInput): Metadata {
  const url = absoluteUrl(path);
  const ogTitle = brandedTitle(title);
  const ogImage = absoluteAssetUrl(image || DEFAULT_OG_IMAGE);
  const metadata: Metadata = {
    title: absoluteTitle ? { absolute: title } : title,
    description,
    alternates: { canonical: url },
    openGraph: {
      title: ogTitle,
      description,
      url,
      siteName: siteConfig.name,
      type,
      images: [{ url: ogImage, alt: ogTitle }],
    },
    twitter: {
      card: "summary_large_image",
      title: ogTitle,
      description,
      images: [ogImage],
    },
  };

  return metadata;
}

export function organizationJsonLd() {
  const orgId = `${PUBLIC_SITE_ORIGIN}/#organization`;
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "EducationalOrganization",
        "@id": orgId,
        name: siteConfig.name,
        url: PUBLIC_SITE_ORIGIN,
        logo: {
          "@type": "ImageObject",
          url: absoluteAssetUrl(ORGANIZATION_LOGO),
        },
        image: absoluteAssetUrl(DEFAULT_OG_IMAGE),
        description: siteConfig.description,
        email: siteConfig.emails.support,
        sameAs: [siteConfig.links.youtube, siteConfig.links.telegram, siteConfig.links.discord],
      },
      {
        "@type": "WebSite",
        "@id": `${PUBLIC_SITE_ORIGIN}/#website`,
        url: PUBLIC_SITE_ORIGIN,
        name: siteConfig.name,
        description: siteConfig.description,
        publisher: { "@id": orgId },
        inLanguage: "en",
      },
    ],
  };
}

export function blogPostingJsonLd(post: {
  title: string;
  excerpt: string;
  slug: string;
  publishedAt: string;
  coverImage?: string;
  author: { name: string };
}) {
  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.excerpt,
    datePublished: post.publishedAt,
    mainEntityOfPage: absoluteUrl(`/insights/${post.slug}`),
    image: absoluteAssetUrl(post.coverImage || DEFAULT_OG_IMAGE),
    author: {
      "@type": "Person",
      name: post.author.name,
    },
    publisher: {
      "@type": "EducationalOrganization",
      name: siteConfig.name,
      logo: {
        "@type": "ImageObject",
        url: absoluteAssetUrl(ORGANIZATION_LOGO),
      },
    },
  };
}
