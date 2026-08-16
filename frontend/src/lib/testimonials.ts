/**
 * Homepage testimonial videos.
 * Paste a YouTube watch, youtu.be, or embed URL into `youtubeUrl`.
 * Leave empty until the video is ready: the UI shows a placeholder.
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

/** Convert a watch / share / embed URL into a privacy-friendly embed src. */
export function toYouTubeEmbedSrc(url: string): string | null {
  const trimmed = url.trim();
  if (!trimmed) return null;

  try {
    const parsed = new URL(trimmed);
    const host = parsed.hostname.replace(/^www\./, "");

    let videoId: string | null = null;

    if (host === "youtu.be") {
      videoId = parsed.pathname.split("/").filter(Boolean)[0] ?? null;
    } else if (host === "youtube.com" || host === "m.youtube.com" || host === "youtube-nocookie.com") {
      if (parsed.pathname.startsWith("/embed/")) {
        videoId = parsed.pathname.split("/")[2] ?? null;
      } else if (parsed.pathname.startsWith("/shorts/")) {
        videoId = parsed.pathname.split("/")[2] ?? null;
      } else {
        videoId = parsed.searchParams.get("v");
      }
    }

    if (!videoId) return null;
    return `https://www.youtube-nocookie.com/embed/${videoId}`;
  } catch {
    return null;
  }
}
