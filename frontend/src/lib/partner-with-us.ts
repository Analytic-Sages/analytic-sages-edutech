/** Typed content for /partner-with-us. Keep metrics and partnerships verified only. */

export type PartnerCapability = {
  number: string;
  title: string;
  summary: string;
  items: string[];
  outcome: string;
};

export type PartnershipStep = {
  number: string;
  title: string;
  body: string;
};

export type PartnershipMode = {
  number: string;
  title: string;
  body: string;
};

export type PartnerOutcome = {
  title: string;
  body: string;
};

export type PartnerContribution = {
  title: string;
  items: string[];
};

export type ImpactMetric = {
  value: string;
  label: string;
};

export type PartnerFAQ = {
  question: string;
  answer: string;
};

export type PartnerCaseStudy = {
  id: string;
  partnerName: string;
  challenge: string;
  whatWeDid: string;
  whatParticipantsBuilt: string;
  outcome: string;
};

/** Verified stats, aligned with TrustStats / About. */
export const partnerImpactMetrics: ImpactMetric[] = [
  { value: "2,000+", label: "Community members" },
  { value: "450+", label: "Blockchain analysts trained" },
  { value: "18+", label: "Countries represented" },
  { value: "8", label: "Successful cohorts" },
  { value: "92%", label: "Course completion rate" },
];

export const partnerHeroProofMetrics: ImpactMetric[] = [
  { value: "2,000+", label: "community members" },
  { value: "450+", label: "blockchain analysts trained" },
  { value: "18+", label: "countries" },
  { value: "8", label: "successful cohorts" },
];

export const partnerCapabilities: PartnerCapability[] = [
  {
    number: "01",
    title: "Ecosystem Data & Analytics",
    summary: "Help your ecosystem understand what is happening onchain.",
    items: [
      "Blockchain analytics",
      "Onchain research",
      "Protocol intelligence",
      "Data visualization",
      "Ecosystem analytics",
      "Financial data analysis",
    ],
    outcome: "Turn blockchain activity into actionable intelligence.",
  },
  {
    number: "02",
    title: "Technical Talent Development",
    summary: "Build a pipeline of people who understand your technology.",
    items: [
      "Blockchain data engineers",
      "Onchain analysts",
      "Researchers",
      "AI engineers",
      "Quantitative researchers",
      "Technical builders",
    ],
    outcome: "Develop talent capable of contributing to your ecosystem.",
  },
  {
    number: "03",
    title: "Ecosystem-Specific Learning",
    summary: "Turn your technology into a structured learning experience.",
    items: [
      "Protocol learning tracks",
      "Technical workshops",
      "Instructor-led cohorts",
      "Data programs",
      "Research programs",
      "Practical challenges",
    ],
    outcome: "Move people from documentation to applied knowledge.",
  },
  {
    number: "04",
    title: "Projects & Ecosystem Contribution",
    summary: "Learning becomes more valuable when people build.",
    items: [
      "Dashboards",
      "Data pipelines",
      "Analytics tools",
      "Research products",
      "AI applications",
      "Protocol-focused projects",
    ],
    outcome: "Create a pathway from learning to real ecosystem contribution.",
  },
  {
    number: "05",
    title: "Talent Discovery",
    summary: "Identify high-performing participants and connect them to the ecosystem.",
    items: [
      "Grants",
      "Bounties",
      "Hackathons",
      "Contributor programs",
      "Internships",
      "Jobs",
      "Ecosystem opportunities",
    ],
    outcome: "Turn education into an ecosystem talent pipeline.",
  },
  {
    number: "06",
    title: "Ecosystem Intelligence",
    summary: "Go beyond education.",
    items: [
      "Data products",
      "Research reports",
      "Ecosystem dashboards",
      "Market intelligence",
      "Protocol analysis",
      "Emerging trend research",
    ],
    outcome: "Give ecosystem teams deeper visibility into their own growth.",
  },
];

export const contributionPipeline = [
  "Blockchain",
  "Data",
  "Analytics",
  "Intelligence",
  "Talent",
  "Projects",
  "Ecosystem Contribution",
] as const;

export const talentPipelineSteps: PartnershipStep[] = [
  {
    number: "01",
    title: "Define",
    body: "We identify your ecosystem's technical, data and talent priorities.",
  },
  {
    number: "02",
    title: "Design",
    body: "We build the curriculum, learning experience and project structure around those priorities.",
  },
  {
    number: "03",
    title: "Develop",
    body: "We train analysts, engineers, researchers and builders through structured learning.",
  },
  {
    number: "04",
    title: "Build",
    body: "Participants apply their skills through practical, ecosystem-focused projects.",
  },
  {
    number: "05",
    title: "Discover",
    body: "Identify high-performing learners, promising projects and emerging contributors.",
  },
  {
    number: "06",
    title: "Connect",
    body: "Create pathways into grants, bounties, jobs, contributor programs and other ecosystem opportunities.",
  },
  {
    number: "07",
    title: "Measure",
    body: "Track participation, learning, project delivery and ecosystem engagement.",
  },
];

export const partnershipModes: PartnershipMode[] = [
  {
    number: "01",
    title: "Ecosystem Learning Programs",
    body: "Build a dedicated learning pathway around your protocol, infrastructure or ecosystem.",
  },
  {
    number: "02",
    title: "Technical Cohorts",
    body: "Develop a focused cohort of analysts, engineers, researchers or builders.",
  },
  {
    number: "03",
    title: "Ecosystem Data Programs",
    body: "Train talent to understand and analyze your ecosystem through data.",
  },
  {
    number: "04",
    title: "Research & Intelligence",
    body: "Develop ecosystem research, dashboards and data products.",
  },
  {
    number: "05",
    title: "Challenges & Build Programs",
    body: "Give learners real ecosystem problems to solve through projects, challenges and competitions.",
  },
  {
    number: "06",
    title: "Strategic Ecosystem Partnerships",
    body: "Work with Analytic Sages across multiple programs, talent initiatives and ecosystem priorities.",
  },
];

export const partnerOutcomes: PartnerOutcome[] = [
  {
    title: "Talent Pipeline",
    body: "Access to people who understand your ecosystem and its technology.",
  },
  {
    title: "Ecosystem Education",
    body: "Structured learning experiences built around your actual technical stack and priorities.",
  },
  {
    title: "Real Projects",
    body: "Participants don't just consume content. They build.",
  },
  {
    title: "Ecosystem Intelligence",
    body: "Data analysis, dashboards and research that provide additional visibility.",
  },
  {
    title: "Community Access",
    body: "Engage directly with a growing global technical learning community.",
  },
  {
    title: "Measurable Outcomes",
    body: "Clear reporting across participation, learning, projects and ecosystem engagement.",
  },
];

export const partnerContributions: PartnerContribution[] = [
  {
    title: "Technical Resources",
    items: ["RPC access", "APIs", "Datasets", "Developer tooling", "Infrastructure"],
  },
  {
    title: "Expertise",
    items: ["Mentors", "Engineers", "Researchers", "Guest speakers", "Judges"],
  },
  {
    title: "Ecosystem Opportunities",
    items: ["Grants", "Bounties", "Hackathons", "Contributor programs", "Jobs"],
  },
  {
    title: "Program Support",
    items: ["Curriculum input", "Technical guidance", "Project challenges", "Ecosystem priorities"],
  },
];

export const whyAnalyticSages = [
  {
    title: "Blockchain-Native",
    body: "We focus on the data, technologies and infrastructure powering blockchain ecosystems.",
  },
  {
    title: "Technical First",
    body: "Our programs go beyond awareness into analytics, engineering, research and building.",
  },
  {
    title: "Community Driven",
    body: "A growing global community of learners, analysts, engineers and builders.",
  },
  {
    title: "Outcome Oriented",
    body: "We measure what participants learn, build and contribute, not simply how many register.",
  },
];

/**
 * Confirmed institutional partnership case studies only.
 * Leave empty until a relationship is verified in-repo / by product.
 */
export const partnerCaseStudies: PartnerCaseStudy[] = [];

export const partnerFaqs: PartnerFAQ[] = [
  {
    question: "What kinds of organizations can partner with Analytic Sages?",
    answer:
      "We work with protocols, foundations, L1/L2 ecosystems, DeFi teams, Web3 infrastructure companies, developer platforms, research organizations and ecosystem teams looking to develop technical talent and deepen ecosystem intelligence.",
  },
  {
    question: "What can Analytic Sages build with an ecosystem?",
    answer:
      "Ecosystem learning tracks, technical cohorts, blockchain data programs, research and dashboards, practical challenges, and longer-term strategic talent initiatives, designed around your stack and goals.",
  },
  {
    question: "Can a program be customized around our protocol?",
    answer:
      "Yes. Curriculum, projects, technical content, workshops and ecosystem activities can be adapted to your protocol, tooling and priorities.",
  },
  {
    question: "What types of talent can you develop?",
    answer:
      "Blockchain analysts, data engineers, researchers, AI engineers, quantitative researchers and technical builders: people prepared to understand and contribute to your ecosystem.",
  },
  {
    question: "How does a partnership begin?",
    answer:
      "A discovery conversation to clarify goals, then program design, execution and measurement. We start from outcomes, not packages.",
  },
  {
    question: "How do you measure outcomes?",
    answer:
      "Participation, completion, learning outcomes, project delivery, ecosystem engagement and other KPIs agreed with your team.",
  },
  {
    question: "Can our technical team participate?",
    answer:
      "Yes. Mentorship, technical sessions, workshops, project reviews and judging can be built into the program.",
  },
  {
    question: "Can programs be global or region-specific?",
    answer:
      "Yes. Programs can run globally or focus on specific regions and communities, depending on your ecosystem priorities.",
  },
  {
    question: "Can Analytic Sages work with multiple ecosystem partners?",
    answer:
      "Yes, where the partnership structure makes strategic and operational sense for everyone involved.",
  },
];

export const organizationTypes = [
  "Protocol",
  "Foundation",
  "Infrastructure Company",
  "Web3 Company",
  "Ecosystem Team",
  "Research Organization",
  "Other",
] as const;

export const partnershipGoals = [
  "Develop technical talent",
  "Launch an ecosystem learning program",
  "Build a protocol-specific learning track",
  "Develop blockchain data talent",
  "Produce ecosystem research",
  "Build ecosystem intelligence",
  "Run a technical challenge",
  "Explore a strategic partnership",
  "Other",
] as const;

export const programInterests = [
  "Ecosystem Data & Analytics",
  "Technical Talent Development",
  "Ecosystem Learning",
  "Research & Intelligence",
  "Projects & Challenges",
  "Strategic Partnership",
] as const;

export const targetRegions = [
  "Global",
  "Africa",
  "Asia",
  "Europe",
  "Latin America",
  "Middle East",
  "North America",
  "Other",
] as const;

export const timelines = [
  "Exploring",
  "Next 1–3 months",
  "Next 3–6 months",
  "6+ months",
  "Flexible",
] as const;
