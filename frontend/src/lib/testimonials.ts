/**
 * Homepage testimonial videos. Cohort 9 program-page videos live in program-pages.ts.
 * To add a homepage video: copy a block, set name/role, and paste a YouTube URL into youtubeUrl.
 */
export type TestimonialVideo = {
  id: string;
  /** Student or alumni name */
  name: string;
  /** Short role / cohort line */
  role: string;
  /** Optional quote shown under the video */
  quote?: string;
  /**
   * YouTube link: any of:
   * - https://www.youtube.com/watch?v=VIDEO_ID
   * - https://youtu.be/VIDEO_ID
   * - https://www.youtube.com/embed/VIDEO_ID
   */
  youtubeUrl: string;
};

export const homeTestimonials: TestimonialVideo[] = [
  {
    id: "t1",
    name: "Victoria Fubara",
    role: "Cohort 7 · Blockchain Data Analyst",
    youtubeUrl: "https://www.youtube-nocookie.com/embed/NV3e8c2llTA",
  },
  {
    id: "t2",
    name: "Dandy Ogbonna",
    role: "Cohort 7 · DeFi Research Analyst",
    youtubeUrl: "https://www.youtube-nocookie.com/embed/HQR7t1M4Yyo",
  },
  {
    id: "t3",
    name: "Rotimi Akinrinde",
    role: "Cohort 5 · Crypto Onchain Analyst",
    youtubeUrl: "https://www.youtube-nocookie.com/embed/IW2IDlQzWHE",
  },
];

export function toYouTubeVideoId(url: string): string | null {
  const trimmed = url.trim();
  if (!trimmed) return null;

  try {
    const parsed = new URL(trimmed);
    const host = parsed.hostname.replace(/^www\./, "");

    if (host === "youtu.be") {
      return parsed.pathname.split("/").filter(Boolean)[0] ?? null;
    }
    if (host === "youtube.com" || host === "m.youtube.com" || host === "youtube-nocookie.com") {
      if (parsed.pathname.startsWith("/embed/") || parsed.pathname.startsWith("/shorts/")) {
        return parsed.pathname.split("/")[2] ?? null;
      }
      return parsed.searchParams.get("v");
    }
  } catch {
    return null;
  }
  return null;
}

export function toYouTubeThumbnail(url: string): string | null {
  const id = toYouTubeVideoId(url);
  return id ? `https://img.youtube.com/vi/${id}/hqdefault.jpg` : null;
}

/** Convert a watch / share / embed URL into a privacy-friendly embed src. */
export function toYouTubeEmbedSrc(url: string): string | null {
  const id = toYouTubeVideoId(url);
  return id ? `https://www.youtube-nocookie.com/embed/${id}` : null;
}
