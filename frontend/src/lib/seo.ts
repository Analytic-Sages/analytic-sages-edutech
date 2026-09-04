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

export function organizationId(): string {
  return `${PUBLIC_SITE_ORIGIN}/#organization`;
}

export function websiteId(): string {
  return `${PUBLIC_SITE_ORIGIN}/#website`;
}

export function socialSameAs(): string[] {
  return [
    siteConfig.links.x,
    siteConfig.links.youtube,
    siteConfig.links.telegram,
    siteConfig.links.discord,
  ];
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
      site: siteConfig.twitterHandle,
      creator: siteConfig.twitterHandle,
      title: ogTitle,
      description,
      images: [ogImage],
    },
  };

  return metadata;
}

export function organizationJsonLd() {
  const orgId = organizationId();
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
        sameAs: socialSameAs(),
      },
      {
        "@type": "WebSite",
        "@id": websiteId(),
        url: PUBLIC_SITE_ORIGIN,
        name: siteConfig.name,
        description: siteConfig.description,
        publisher: { "@id": orgId },
        inLanguage: "en",
      },
    ],
  };
}

export type BreadcrumbItem = { name: string; path: string };

export function breadcrumbJsonLd(items: BreadcrumbItem[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: absoluteUrl(item.path),
    })),
  };
}

export function faqPageJsonLd(faqs: { question: string; answer: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer,
      },
    })),
  };
}

export function courseJsonLd(input: {
  name: string;
  description: string;
  path: string;
  image?: string | null;
  providerName?: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "Course",
    name: input.name,
    description: input.description,
    url: absoluteUrl(input.path),
    image: absoluteAssetUrl(input.image || DEFAULT_OG_IMAGE),
    provider: {
      "@id": organizationId(),
    },
    inLanguage: "en",
  };
}

/** Live / cohort-style programmes (e.g. Blockchain Data Engineering). */
export function educationalProgramJsonLd(input: {
  name: string;
  description: string;
  path: string;
  image?: string | null;
  timeToComplete?: string;
  educationalProgramMode?: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "EducationalOccupationalProgram",
    name: input.name,
    description: input.description,
    url: absoluteUrl(input.path),
    image: absoluteAssetUrl(input.image || DEFAULT_OG_IMAGE),
    provider: {
      "@id": organizationId(),
    },
    ...(input.timeToComplete ? { timeToComplete: input.timeToComplete } : {}),
    ...(input.educationalProgramMode
      ? { educationalProgramMode: input.educationalProgramMode }
      : {}),
    inLanguage: "en",
  };
}

export function eventJsonLd(input: {
  name: string;
  description: string;
  path: string;
  image?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  isFree?: boolean;
  price?: number;
  currency?: string;
  eventStatus?: "EventScheduled" | "EventCancelled" | "EventPostponed";
}) {
  const offer =
    input.isFree || input.price === 0
      ? {
          "@type": "Offer",
          price: 0,
          priceCurrency: input.currency || "USD",
          availability: "https://schema.org/InStock",
          url: absoluteUrl(input.path),
        }
      : input.price != null
        ? {
            "@type": "Offer",
            price: input.price,
            priceCurrency: input.currency || "USD",
            availability: "https://schema.org/InStock",
            url: absoluteUrl(input.path),
          }
        : undefined;

  return {
    "@context": "https://schema.org",
    "@type": "Event",
    name: input.name,
    description: input.description,
    url: absoluteUrl(input.path),
    image: absoluteAssetUrl(input.image || DEFAULT_OG_IMAGE),
    ...(input.startDate ? { startDate: input.startDate } : {}),
    ...(input.endDate ? { endDate: input.endDate } : {}),
    eventAttendanceMode: "https://schema.org/OnlineEventAttendanceMode",
    eventStatus: `https://schema.org/${input.eventStatus || "EventScheduled"}`,
    organizer: { "@id": organizationId() },
    ...(offer ? { offers: offer } : {}),
    location: {
      "@type": "VirtualLocation",
      url: absoluteUrl(input.path),
    },
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
      "@id": organizationId(),
    },
    isPartOf: {
      "@id": websiteId(),
    },
  };
}
