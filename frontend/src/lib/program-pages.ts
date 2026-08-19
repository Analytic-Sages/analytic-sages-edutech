import { FEATURED_COHORT_SLUG } from "@/lib/auth-redirect";
import { homeTestimonials, type TestimonialVideo } from "@/lib/testimonials";
import { siteConfig } from "@/config/site";

export type ProgramModule = {
  id: string;
  number: string;
  title: string;
  summary: string;
  learn: string[];
  tools: string[];
  outcome: string;
};

export type ProgramProject = {
  id: string;
  title: string;
  analyzes: string;
  tools: string[];
  demonstrates: string;
};

export type ProgramStudentWork = {
  id: string;
  title: string;
  caption: string;
  image: string;
  alt: string;
};

export type ProgramFaq = {
  question: string;
  answer: string;
};

export type ProgramTool = {
  id: string;
  name: string;
  detail: string;
};

export type ProgramPageContent = {
  /** Public marketing URL slug */
  pageSlug: string;
  /** Backend / checkout cohort slug */
  cohortSlug: string;
  aliases: string[];
  eyebrow: string;
  headline: string;
  support: string;
  seoTitle: string;
  seoDescription: string;
  canonicalPath: string;
  format: string;
  community: string;
  paymentOptions: string;
  certificate: string;
  timeCommitment: string;
  timeCommitmentShort: string;
  audienceFor: string[];
  audienceNotFor: string[];
  modules: ProgramModule[];
  projects: ProgramProject[];
  studentWork: ProgramStudentWork[];
  testimonials: TestimonialVideo[];
  outcomes: string[];
  tools: ProgramTool[];
  experience: { title: string; body: string }[];
  faqs: ProgramFaq[];
};

const COHORT_9_PAGE_SLUG = "cohort-9-sql-blockchain-data-analytics";

const cohort9: ProgramPageContent = {
  pageSlug: COHORT_9_PAGE_SLUG,
  cohortSlug: FEATURED_COHORT_SLUG,
  aliases: [FEATURED_COHORT_SLUG],
  eyebrow: "Instructor-Led Training",
  headline: "SQL Blockchain Data Analytics",
  support:
    "Learn to query real blockchain data with SQL, work on live on-chain datasets, and finish with practical analytics projects you can show in a portfolio.",
  seoTitle: "SQL Blockchain Data Analytics",
  seoDescription:
    "Learn SQL and practical blockchain data analytics through instructor-led training, real on-chain datasets, hands-on projects and expert guidance with Analytic Sages.",
  canonicalPath: `/programs/${COHORT_9_PAGE_SLUG}`,
  format: "Live online, instructor-led",
  community: "Analytic Sages Discord and Telegram",
  paymentOptions: "Paystack (cards and bank transfer) or crypto via NOWPayments",
  certificate:
    "Certificates are not issued on the platform yet. Completing the cohort still gives you the projects, recordings, and classroom access.",
  timeCommitment:
    "Live sessions plus independent SQL practice and project work. Weekly load depends on the assignment.",
  timeCommitmentShort: "Live sessions plus project work",
  audienceFor: [
    "You want practical blockchain data skills, not just theory",
    "You want to learn SQL through real on-chain data",
    "You want to build portfolio-ready analytics projects",
    "You are interested in blockchain, DeFi, and data",
    "You want structured instructor-led learning",
    "You are ready to work with real datasets",
  ],
  audienceNotFor: [
    "You are looking for a get-rich-quick scheme",
    "You expect passive learning without doing the work",
    "You are unwilling to commit time to projects and practice",
  ],
  modules: [
    {
      id: "m1",
      number: "01",
      title: "Introduction to Web3 Data Analytics",
      summary:
        "Understand what blockchain data is, why on-chain activity matters, and how explorers fit into an analyst’s workflow.",
      learn: [
        "What blockchain data is and why it matters to decentralized systems",
        "How on-chain data is used for DeFi monitoring, wallet tracking, and investigation",
        "The roles of Etherscan, Dune Analytics, and related tools",
        "How to navigate explorers for transactions, token flows, and contracts",
      ],
      tools: ["Etherscan", "Blockchain explorers"],
      outcome:
        "Write an Etherscan guide that analyses wallet transactions, smart contracts, and token transfers.",
    },
    {
      id: "m2",
      number: "02",
      title: "SQL for Web3 Data Analytics",
      summary:
        "Build SQL foundations on blockchain examples: filters, joins, aggregations, subqueries, and CTEs.",
      learn: [
        "SELECT, WHERE, and ORDER BY with on-chain examples",
        "Joins and aggregations across wallet, transaction, and token data",
        "Subqueries and CTEs for protocol usage and more complex questions",
        "Practice queries on balances, active users, and swap volume",
      ],
      tools: ["SQL"],
      outcome:
        "Query wallet history, identify active protocol users, and aggregate token swap volumes over time.",
    },
    {
      id: "m3",
      number: "03",
      title: "Working with Blockchain Data",
      summary:
        "Move from explorers into live datasets: table schemas, smart contracts, and DEX activity on Dune.",
      learn: [
        "Write SQL against live blockchain datasets in Dune Analytics",
        "Read schemas for blocks, logs, events, and traces",
        "Analyse Uniswap liquidity, volume, swaps, and top pairs",
      ],
      tools: ["Dune Analytics", "SQL", "DEX data"],
      outcome:
        "Build a SQL dashboard for Uniswap covering volume, liquidity pools, and unique users.",
    },
    {
      id: "m4",
      number: "04",
      title: "Building Insightful Dashboards",
      summary:
        "Turn queries into clear visuals and a capstone dashboard for a token or protocol.",
      learn: [
        "Token performance views: price, holder distribution, and transaction trends",
        "Chart, layout, and filter choices that make a finding readable",
        "How to present price, wallet interaction, fees, and growth in one place",
      ],
      tools: ["Dune Analytics", "Data visualization"],
      outcome:
        "Design a capstone dashboard covering trends, wallet interaction, fees, and actionable insights.",
    },
  ],
  projects: [
    {
      id: "p1",
      title: "Wallet and contract explorer study",
      analyzes: "Wallet transactions, smart contracts, and token transfers on a public explorer",
      tools: ["Etherscan"],
      demonstrates: "You can read on-chain activity and explain what a wallet or contract is doing.",
    },
    {
      id: "p2",
      title: "Protocol user and volume queries",
      analyzes: "Wallet balances, active users on a DeFi protocol, and token swap volumes over time",
      tools: ["SQL"],
      demonstrates: "You can write SQL that answers a real analytics question, not just a tutorial query.",
    },
    {
      id: "p3",
      title: "Uniswap SQL dashboard",
      analyzes: "Daily, weekly, and monthly volume, liquidity pools, and unique users",
      tools: ["SQL", "Dune Analytics"],
      demonstrates: "You can turn DEX tables into a readable activity dashboard.",
    },
    {
      id: "p4",
      title: "Token or protocol capstone",
      analyzes: "Price trends, wallet interaction, fees, retention/growth, and a short insight write-up",
      tools: ["Dune Analytics", "Data visualization"],
      demonstrates: "You can complete a portfolio-ready analytics piece and explain the findings.",
    },
  ],
  studentWork: [
    {
      id: "sw1",
      title: "Workshop collaboration",
      caption:
        "Analytic Sages learners working through analytics exercises together. These are real workshop photos, not simulated dashboards.",
      image: "/2.png",
      alt: "Analytic Sages learners collaborating with laptops during a workshop",
    },
    {
      id: "sw2",
      title: "In-person training",
      caption:
        "A live Analytic Sages training session. Cohort 9 is online; earlier cohorts also met in workshop settings like this.",
      image: "/4.png",
      alt: "Analytic Sages in-person training session",
    },
    {
      id: "sw3",
      title: "Classroom practice",
      caption: "Hands-on practice is the core of the instructor-led format.",
      image: "/5.webp",
      alt: "Analytic Sages classroom practice session",
    },
    {
      id: "sw4",
      title: "Cohort working session",
      caption: "Learners building together during an Analytic Sages session.",
      image: "/6.webp",
      alt: "Analytic Sages cohort working session",
    },
  ],
  testimonials: homeTestimonials,
  outcomes: [
    "Build portfolio-ready blockchain analytics dashboards",
    "Query real blockchain data independently with SQL",
    "Conduct on-chain research using explorers and Dune",
    "Turn raw blockchain data into useful insights",
    "Present and explain analytical findings",
    "Leave with a set of practical projects, not only class notes",
    "Join the Analytic Sages learning community",
  ],
  tools: [
    { id: "sql", name: "SQL", detail: "Query wallets, protocols, and swap activity" },
    { id: "dune", name: "Dune Analytics", detail: "Live blockchain datasets and dashboards" },
    { id: "etherscan", name: "Etherscan", detail: "Transactions, contracts, and token flows" },
    { id: "defi", name: "DeFi / DEX data", detail: "Uniswap volume, liquidity, and users" },
    { id: "viz", name: "Data visualization", detail: "Charts and dashboards that tell a story" },
    { id: "onchain", name: "Blockchain data", detail: "Blocks, logs, events, and traces" },
  ],
  experience: [
    {
      title: "Live instructor sessions",
      body: "Learn directly from instructors in scheduled live classes — the core of Instructor-Led Training, not a library of videos you watch alone.",
    },
    {
      title: "Practical projects",
      body: "Apply each module to real blockchain data: explorer studies, SQL practice, a Uniswap dashboard, and a capstone.",
    },
    {
      title: "Recorded materials",
      body: "Revisit live sessions after class. Missing a session does not mean you lose the material.",
    },
    {
      title: "Community",
      body: `Learn alongside other analysts and builders in ${siteConfig.name} Discord and Telegram.`,
    },
    {
      title: "Feedback",
      body: "Get guidance on projects and assignments from instructors during the cohort, unlike self-paced catalog browsing.",
    },
  ],
  faqs: [
    {
      question: "Do I need prior blockchain experience?",
      answer:
        "No. The linked curriculum starts with blockchain data fundamentals and explorers before SQL and Dune. Curiosity about blockchain, DeFi, and data is enough to begin.",
    },
    {
      question: "Do I need to know SQL?",
      answer:
        "No prior SQL is required. The program teaches SELECT, filters, joins, aggregations, and CTEs using on-chain examples.",
    },
    {
      question: "What happens if I miss a live session?",
      answer:
        "Live sessions are the main format, and recordings are provided so you can catch up. You are still expected to complete the practice and projects.",
    },
    {
      question: "How much time should I commit each week?",
      answer:
        "Plan time for the live session plus independent SQL practice and project work. Exact hours vary by week; the work is not designed as passive watching.",
    },
    {
      question: "What tools will I need?",
      answer:
        "A laptop, a browser, and accounts for the analytics tools used in class (including Dune). Setup is covered in the early sessions.",
    },
    {
      question: "Will I receive recordings?",
      answer:
        "Yes. Recorded session materials are part of the instructor-led experience so you can revisit class.",
    },
    {
      question: "Will I receive a certificate?",
      answer:
        "Platform certificates are not live yet. Do not expect an issued Analytic Sages certificate at the end of this cohort. You will still have the projects and classroom work you complete.",
    },
    {
      question: "Can I pay in installments?",
      answer:
        "No installment plan is offered. Registration is paid in full at checkout via Paystack or NOWPayments.",
    },
    {
      question: "How does registration work?",
      answer:
        "Open Register for Cohort 9. If you are not signed in, you will create an account or log in, then complete payment on the existing checkout page. Confirmed payment unlocks the Classroom.",
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

export function getProgramPageHref(cohortApiSlug: string): string | null {
  const page = programPages.find((item) => item.cohortSlug === cohortApiSlug);
  return page ? `/programs/${page.pageSlug}` : null;
}

export const PUBLIC_SITE_ORIGIN = "https://analyticsages.io";
