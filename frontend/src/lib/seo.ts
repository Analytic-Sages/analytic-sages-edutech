import type { Metadata } from "next";
import { PUBLIC_SITE_ORIGIN } from "@/lib/program-pages";

export function absoluteUrl(path = "/"): string {
  if (!path || path === "/") return PUBLIC_SITE_ORIGIN;
  return `${PUBLIC_SITE_ORIGIN}${path.startsWith("/") ? path : `/${path}`}`;
}

export function absoluteAssetUrl(src: string): string {
  if (src.startsWith("http://") || src.startsWith("https://")) return src;
  return `${PUBLIC_SITE_ORIGIN}${src.startsWith("/") ? src : `/${src}`}`;
}

export function brandedTitle(title: string): string {
  if (title === "Analytic Sages" || title.endsWith(" | Analytic Sages")) return title;
  return `${title} | Analytic Sages`;
}

type PageMetadataInput = {
  title: string;
  description: string;
  path: string;
  image?: string | null;
  /** Homepage should not become "Analytic Sages | Analytic Sages". */
  absoluteTitle?: boolean;
};

export function pageMetadata({
  title,
  description,
  path,
  image,
  absoluteTitle = false,
}: PageMetadataInput): Metadata {
  const url = absoluteUrl(path);
  const ogTitle = brandedTitle(title);
  const metadata: Metadata = {
    title: absoluteTitle ? { absolute: title } : title,
    description,
    alternates: { canonical: url },
    openGraph: {
      title: ogTitle,
      description,
      url,
      siteName: "Analytic Sages",
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: ogTitle,
      description,
    },
  };

  if (image) {
    const ogImage = absoluteAssetUrl(image);
    metadata.openGraph = { ...metadata.openGraph, images: [{ url: ogImage, alt: ogTitle }] };
    metadata.twitter = { ...metadata.twitter, images: [ogImage] };
  }

  return metadata;
}
