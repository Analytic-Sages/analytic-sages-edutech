import { FEATURED_COHORT_SLUG } from "@/lib/auth-redirect";
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
  format: string;
  duration: string;
  timeCommitment: string;
  paymentOptions: string;
  audienceFor: string[];
  audienceNotFor: string[];
  learnTopics: { title: string; body: string }[];
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

const cohort9: ProgramPageContent = {
  pageSlug: COHORT_9_PAGE_SLUG,
  cohortSlug: FEATURED_COHORT_SLUG,
  aliases: [FEATURED_COHORT_SLUG],
  eyebrow: "Instructor-Led Training · Cohort 9",
  headline: "SQL Blockchain Data Analytics",
  support:
    "Learn to work with real blockchain data using SQL and build practical analytics projects: live classes, recorded materials, and a learning community.",
  seoTitle: "SQL Blockchain Data Analytics",
  seoDescription:
    "Learn SQL and practical blockchain data analytics through instructor-led training, real on-chain datasets, hands-on projects and expert guidance with Analytic Sages.",
  canonicalPath: `/programs/${COHORT_9_PAGE_SLUG}`,
  postcardImage: "/cohort-9-sql-blockchain-data-analytics.png",
  format: "Live weekly sessions + recorded materials + community",
  duration: "4 weeks",
  timeCommitment: "5-8 hours per week",
  paymentOptions: "Paystack (cards and bank transfer) or crypto via NOWPayments. One-time payment.",
  audienceFor: [
    "You're curious about blockchain but don't know where to start",
    "You want a practical, skill-based path in Web3 data",
    "You have no coding experience (we start from zero)",
    "You're ready to stop watching and start building",
  ],
  audienceNotFor: [
    "You're looking for a get-rich-quick scheme",
    "You can't commit 5-8 hours per week",
  ],
  learnTopics: [
    {
      title: "SQL for Blockchain Data",
      body: "Query wallets, transactions, and protocols like an analyst.",
    },
    {
      title: "Onchain Analytics",
      body: "Track whales, analyze protocol health, spot trends.",
    },
    {
      title: "Research-Driven Reports",
      body: "Write insights that investors and DAOs actually read.",
    },
    {
      title: "Real Dashboard Projects",
      body: "Build a portfolio of work you can show employers.",
    },
    {
      title: "Live Sessions & Support",
      body: "Learn with instructors and a community of peers.",
    },
    {
      title: "Career Pathways",
      body: "Freelance, full-time, or build your own tools.",
    },
  ],
  outcomesIntro: "By the end of this program…",
  outcomes: [
    "Build 2-3 complete dashboards (portfolio ready)",
    "Write a research report from scratch",
    "Query real blockchain data independently",
    "Present your findings with confidence",
    "Join a network of analysts and alumni",
  ],
  outcomeBonus: "Bonus: Access to our alumni community.",
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
        "No. We start from the basics: blockchain data, explorers, then SQL and Dune. No prior coding or SQL is required.",
    },
    {
      question: "What if I miss a live session?",
      answer:
        "Recordings are provided so you can catch up. You are still expected to complete the practice and projects.",
    },
    {
      question: "Is the certificate recognised?",
      answer:
        "Platform certificates are not issued yet. Completing Cohort 9 still gives you the dashboards, report, and classroom work you can show.",
    },
    {
      question: "Can I pay in installments?",
      answer:
        "No. Registration is a one-time payment at checkout via Paystack or NOWPayments.",
    },
    {
      question: "What do I need to start?",
      answer:
        "A laptop, a browser, and time for live class plus practice. Dune setup is covered in the early sessions.",
    },
    {
      question: "Will this help me get a job?",
      answer:
        "The program is built around practical SQL, Dune dashboards, and a research report you can put in a portfolio. It does not guarantee a job or income.",
    },
  ],
};

const programPages: ProgramPageContent[] = [cohort9];

export function getProgramPage(slug: string): ProgramPageContent | undefined {
  return programPages.find(
    (page) => page.pageSlug === slug || page.aliases.includes(slug) || page.cohortSlug === slug,
  );
}

export function listProgramPageSlugs(): string[] {
  return programPages.flatMap((page) => [page.pageSlug, ...page.aliases]);
}

export function listPublicProgramPaths(): string[] {
  return [...new Set(programPages.map((page) => page.canonicalPath))];
}

export function getProgramPageHref(cohortApiSlug: string): string | null {
  const page = programPages.find((item) => item.cohortSlug === cohortApiSlug);
  return page ? `/programs/${page.pageSlug}` : null;
}

export function getProgramPostcard(cohortApiSlug: string): string | null {
  return programPages.find((item) => item.cohortSlug === cohortApiSlug)?.postcardImage ?? null;
}

export const PUBLIC_SITE_ORIGIN = "https://analyticsages.io";
