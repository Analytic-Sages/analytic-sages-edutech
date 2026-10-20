import {
  BDE_COHORT_SLUG,
  blockchainDataEngineeringProgram,
  getEngineeringProgramPage,
  listEngineeringProgramSlugs,
} from "@/lib/blockchain-data-engineering-program";
import type { TestimonialVideo } from "@/lib/testimonials";
import { siteConfig } from "@/config/site";

export type ProgramFaq = {
  question: string;
  answer: string;
};

export type ProgramDuneDashboard = {
  id: string;
  title: string;
  description?: string;
  author: string;
  /** Dune chart embed, e.g. https://dune.com/embeds/QUERY/VIZ */
  embedSrc: string;
};

export type ProgramPageContent = {
  pageSlug: string;
  cohortSlug: string;
  aliases: string[];
  eyebrow: string;
  headline: string;
  support: string;
  seoTitle: string;
  seoDescription: string;
  canonicalPath: string;
  curriculumPath: string;
  format: string;
  duration: string;
  timeCommitment: string;
  paymentOptions: string;
  registrationDeadline: string;
  startDate: string;
  registrationClosed?: boolean;
  /** When true, show Coming soon - do not sell checkout as open. */
  comingSoon?: boolean;
  audienceFor: string[];
  audienceNotFor: string[];
  learnTopics: { title: string; body: string }[];
  pathways?: { title: string; kicker: string; body: string; output: string }[];
  outcomesIntro: string;
  outcomes: string[];
  outcomeBonus: string;
  duneDashboards: ProgramDuneDashboard[];
  /** Paste YouTube watch / youtu.be / embed URLs into `youtubeUrl`. */
  testimonials: TestimonialVideo[];
  moreTestimonialsUrl: string;
  faqs: ProgramFaq[];
  postcardImage: string;
};

const COHORT_9_PAGE_SLUG = "cohort-9-sql-blockchain-data-analytics";
/** API slug for Cohort 9 (kept even when FEATURED points at BDE). */
export const COHORT_9_COHORT_SLUG = "cohort-9-blockchain-data";

const cohort9: ProgramPageContent = {
  pageSlug: COHORT_9_PAGE_SLUG,
  cohortSlug: COHORT_9_COHORT_SLUG,
  aliases: [COHORT_9_COHORT_SLUG],
  eyebrow: "Cohort 1 Launch · Instructor-Led",
  headline: "SQL & Excel for Blockchain Data Analytics and Research",
  support:
    "Master SQL, Excel and AI for Web3 research in a six-week instructor-led bootcamp. Move from raw blockchain data to practical market intelligence, dashboards and research across DeFi, tokenized real-world assets and perpetual futures.",
  seoTitle: "SQL & Excel for Onchain Data and Research Analysis | Analytic Sages",
  seoDescription:
    "Learn SQL, Excel, APIs and AI-assisted research with Analytic Sages. Build onchain analytics dashboards and research projects across DeFi, tokenized real-world assets and perpetual futures in six weeks.",
  canonicalPath: `/programs/${COHORT_9_PAGE_SLUG}`,
  curriculumPath: `/programs/${COHORT_9_PAGE_SLUG}/curriculum`,
  postcardImage: "/SQL and Excel for Blockchain Analytics.png",
  format: "Instructor-led training, practical labs, weekly projects and office hours",
  duration: "6 weeks",
  timeCommitment: "5–8 hours per week · Mondays and Wednesdays training, Fridays office hours",
  paymentOptions: "Registration closed on 7 October 2026. Classes start on 9 November 2026. Join the waitlist for the next intake. Tuition for this six-week programme is $50 / ₦70,000.",
  registrationDeadline: "2026-10-07T22:59:59Z",
  startDate: "2026-11-09T00:00:00Z",
  registrationClosed: true,
  comingSoon: false,
  audienceFor: [
    "You want practical SQL, Excel and AI skills for Web3 research",
    "You want to analyze DeFi, RWA tokenization or perpetual futures",
    "You want to build dashboards and portfolio-ready research",
    "You can attend live sessions and complete weekly projects",
  ],
  audienceNotFor: [
    "You expect guaranteed jobs or investment returns",
    "You cannot commit time to weekly practice and projects",
  ],
  learnTopics: [
    {
      title: "SQL for Onchain Research",
      body: "Query blockchain tables with filters, joins, CTEs and window functions.",
    },
    {
      title: "Excel, APIs & Data Integration",
      body: "Clean datasets, combine CoinGecko market data and onchain metrics, and build interactive workbooks.",
    },
    {
      title: "DeFi, RWA & Derivatives Research",
      body: "Analyze protocol performance, tokenized assets and perpetual futures market structure.",
    },
    {
      title: "AI-Assisted Analysis",
      body: "Use AI to draft and debug queries, review formulas and structure research responsibly.",
    },
    {
      title: "Live Labs & Office Hours",
      body: "Get guided practice, troubleshooting and weekly project feedback.",
    },
    {
      title: "Portfolio-Ready Capstone",
      body: "Package SQL, an Excel workbook, a dashboard, research report and presentation.",
    },
  ],
  pathways: [
    {
      title: "SQL Analytics Training",
      kicker: "CORE CURRICULUM",
      body: "Build the core workflow: extract data, validate metrics, analyze with SQL and Excel, and present findings clearly.",
      output: "Output: SQL queries · Excel workbook · dashboard · research brief",
    },
    {
      title: "Study Group",
      kicker: "ONGOING PRACTICE",
      body: "Keep your analytical skills sharp through short CoinGecko, Excel, protocol-metrics and SQL exercises.",
      output: "Output: Weekly exercises · peer reviews · reusable templates",
    },
    {
      title: "Research Lab",
      kicker: "DEEPER INVESTIGATION",
      body: "Turn analytical skills into deeper research across DeFi, RWA and tokenization, stablecoins, perpetual futures and ecosystem growth.",
      output: "Output: Research reports · dashboards · datasets · analytical threads",
    },
    {
      title: "Fellowship",
      kicker: "TALENT DEVELOPMENT",
      body: "Committed learners can progress into larger research briefs, mentorship, methodology documentation and community or industry presentations.",
      output: "Output: Research ownership · portfolio evidence · mentorship · opportunities",
    },
  ],
  outcomesIntro: "By the end of this program…",
  outcomes: [
    "Query and document real blockchain datasets with SQL",
    "Integrate market and onchain data in Excel",
    "Build dashboards for DeFi, RWA and perpetual futures research",
    "Validate AI-assisted analysis and communicate limitations",
    "Present a portfolio-ready capstone project",
  ],
  outcomeBonus: "Final portfolio: SQL queries, Excel workbook, custom dashboard, written research report and presentation.",
  duneDashboards: [
    {
      id: "d1",
      title: "Aave V3 365 TVL",
      author: "cryptopanda01",
      embedSrc: "https://dune.com/embeds/6927509/10834449",
    },
    {
      id: "d2",
      title: "Aave Deposit and Withdraw Value",
      author: "cryptopanda01",
      embedSrc: "https://dune.com/embeds/6927509/10834492",
    },
    {
      id: "d3",
      title: "Volatility (blue) vs Range Width (green) Over Time",
      description:
        "This query analyzes the risk of liquidity provider (LP) positions in the Uniswap V3 WETH/USDC pool.",
      author: "apostleoffinance123",
      embedSrc: "https://dune.com/embeds/5911295/9547652",
    },
    {
      id: "d4",
      title: "Netflow",
      author: "cryptopanda01",
      embedSrc: "https://dune.com/embeds/6927509/10834479",
    },
  ],
  testimonials: [
    {
      id: "c9-t1",
      name: "Kelvin",
      role: "Cohort 5",
      youtubeUrl: "https://www.youtube.com/embed/rJyOypSDBig",
    },
    {
      id: "c9-t2",
      name: "Dandy Ogbonna",
      role: "Cohort 7 · DeFi Research Analyst",
      youtubeUrl: "https://www.youtube.com/embed/38c6s1JJ0QA",
    },
    {
      id: "c9-t3",
      name: "Litoshi",
      role: "Cohort 1 · Onchain Analyst",
      youtubeUrl: "https://www.youtube.com/embed/e6Od4Jeh9nM",
    },
    {
      id: "c9-t4",
      name: "Victoria Fubara",
      role: "Cohort 7 · Blockchain Data Analyst",
      youtubeUrl: "https://www.youtube.com/embed/NV3e8c2llTA",
    },
    {
      id: "c9-t5",
      name: "Favour Igbise",
      role: "Blockchain Analyst",
      youtubeUrl: "https://www.youtube.com/embed/w3Lvh8vWz58",
    },
  ],
  moreTestimonialsUrl: siteConfig.links.youtube,
  faqs: [
    {
      question: "Do I need any experience?",
      answer:
        "The programme introduces onchain research and SQL foundations with guided labs and AI-assisted practice. Prior blockchain research experience is not required.",
    },
    {
      question: "What if I miss a live session?",
      answer:
        "Recordings are provided so you can catch up. You are still expected to complete the practice and projects.",
    },
    {
      question: "Will I receive a certificate?",
      answer:
        "Yes. Learners who successfully complete the programme and its required projects will receive a certificate of completion from Analytic Sages.",
    },
    {
      question: "When does the programme start and what does it cost?",
      answer:
        "The six-week programme runs from 9 November to 18 December 2026. Tuition is $50 / ₦70,000. Registration closed on 7 October 2026.",
    },
    {
      question: "What do I need to start?",
      answer:
        "Bring a laptop, a browser, and time for live sessions and weekly practice. The programme introduces Dune, Excel workflows, market-data APIs and responsible AI use.",
    },
    {
      question: "Will this help me get a job?",
      answer:
        "We don’t guarantee jobs, but we teach you the skills and how to showcase them. Many past students have landed freelance gigs, full-time roles, and protocol recognition.",
    },
  ],
};

const programPages: ProgramPageContent[] = [cohort9];

export {
  blockchainDataEngineeringProgram,
  getEngineeringProgramPage,
  listEngineeringProgramSlugs,
  BDE_COHORT_SLUG,
};

export function getProgramPage(slug: string): ProgramPageContent | undefined {
  return programPages.find(
    (page) => page.pageSlug === slug || page.aliases.includes(slug) || page.cohortSlug === slug,
  );
}

export function listProgramPageSlugs(): string[] {
  return [
    ...programPages.flatMap((page) => [page.pageSlug, ...page.aliases]),
    ...listEngineeringProgramSlugs(),
  ];
}

export function listPublicProgramPaths(): string[] {
  return [
    ...new Set([
      ...programPages.flatMap((page) => [page.canonicalPath, page.curriculumPath]),
      blockchainDataEngineeringProgram.canonicalPath,
      blockchainDataEngineeringProgram.curriculumPath,
    ]),
  ];
}

export function listComingSoonPrograms(): ProgramPageContent[] {
  return programPages.filter((page) => page.comingSoon);
}

/** API cohort slugs that should never appear as open - marketing marks them Coming soon. */
export function comingSoonCohortSlugs(): Set<string> {
  return new Set(listComingSoonPrograms().map((page) => page.cohortSlug));
}

export function getProgramPageHref(cohortApiSlug: string): string | null {
  const engineering = getEngineeringProgramPage(cohortApiSlug);
  if (engineering) return `/programs/${engineering.pageSlug}`;
  const page = programPages.find((item) => item.cohortSlug === cohortApiSlug);
  return page ? `/programs/${page.pageSlug}` : null;
}

/** Waitlist page for a cohort whose registration has closed (next-intake intake form). */
export function getProgramWaitlistHref(cohortApiSlug: string): string | null {
  const engineering = getEngineeringProgramPage(cohortApiSlug);
  if (engineering) return `/waitlist/${engineering.pageSlug}`;
  const page = programPages.find((item) => item.cohortSlug === cohortApiSlug);
  return page ? `/waitlist/${page.pageSlug}` : null;
}

export function getProgramPostcard(cohortApiSlug: string): string | null {
  const engineering = getEngineeringProgramPage(cohortApiSlug);
  if (engineering) return engineering.postcardImage;
  return programPages.find((item) => item.cohortSlug === cohortApiSlug)?.postcardImage ?? null;
}

export const PUBLIC_SITE_ORIGIN = "https://www.analyticsages.io";
