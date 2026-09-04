export type EngineeringFaq = {
  question: string;
  answer: string;
};

export type StackTier = {
  label: string;
  tools: string[];
};

export type CurriculumWeek = {
  week: number;
  title: string;
  focus: string;
  tools: string[];
  objectives: string[];
  exercises: string[];
  project?: string;
  sessions: { number: number; title: string; summary: string }[];
};

export type EngineeringProgramPageContent = {
  pageSlug: string;
  cohortSlug: string;
  aliases: string[];
  eyebrow: string;
  /** SEO primary H1 */
  h1: string;
  /** Sales headline under H1 */
  salesHeadline: string;
  heroBody: string;
  support: string;
  positioning: string;
  positioningPhrase: string;
  seoTitle: string;
  seoDescription: string;
  canonicalPath: string;
  curriculumPath: string;
  postcardImage: string;
  format: string;
  duration: string;
  timeCommitment: string;
  paymentOptions: string;
  applyLabel: string;
  programSignal: string;
  learningMode: string;
  problemTitle: string;
  problemSupport: string;
  processChain: string[];
  definitionTitle: string;
  definitionBody: string;
  definitionItems: string[];
  systemsTitle: string;
  systemsIntro: string;
  systemsFlow: string[];
  journey: string[];
  buildsTitle: string;
  builds: { title: string; body: string }[];
  stackTitle: string;
  stackIntro: string;
  stackTiers: StackTier[];
  personasTitle: string;
  personas: string[];
  careersTitle: string;
  careersIntro: string;
  careers: string[];
  careersNote: string;
  outcomesTitle: string;
  outcomes: string[];
  curriculumPreviewTitle: string;
  curriculumPreviewClose: string;
  curriculumPreview: { range: string; title: string }[];
  faqs: EngineeringFaq[];
  curriculum: {
    seoTitle: string;
    seoDescription: string;
    intro: string;
    modules: {
      number: string;
      title: string;
      body: string;
      topics: string[];
    }[];
    weeks: CurriculumWeek[];
    facilitatorNote: string;
  };
};

export const BDE_PAGE_SLUG = "blockchain-data-engineering";
export const BDE_COHORT_SLUG = "blockchain-data-engineering";

export const blockchainDataEngineeringProgram: EngineeringProgramPageContent = {
  pageSlug: BDE_PAGE_SLUG,
  cohortSlug: BDE_COHORT_SLUG,
  aliases: [BDE_COHORT_SLUG],
  eyebrow: "Blockchain & Web3 Engineering Programme",
  h1: "Blockchain Data Engineering Programme",
  salesHeadline: "Build the Infrastructure Behind Blockchain Data.",
  heroBody:
    "Learn how to extract, transform, store and deploy real onchain data pipelines using Python, SQL, Web3.py, PostgreSQL, dbt and modern data engineering tools.",
  support:
    "Learn Blockchain Data Engineering by building real onchain data systems — pipelines, warehouses, transformations, APIs and cloud deployment.",
  positioning:
    "Don't just learn tools. Learn how the system connects — from blockchain RPCs to production data products.",
  positioningPhrase:
    "Learn Blockchain Data Engineering by Building Real Onchain Data Systems.",
  seoTitle: "Blockchain Data Engineering Programme | Learn Python, Web3.py & Onchain Data",
  seoDescription:
    "Learn Blockchain Data Engineering through hands-on projects. Build real onchain data pipelines using Python, SQL, Web3.py, PostgreSQL, dbt, Docker and modern data engineering tools.",
  canonicalPath: `/programs/${BDE_PAGE_SLUG}`,
  curriculumPath: `/programs/${BDE_PAGE_SLUG}/curriculum`,
  postcardImage: "/blockchain-data-engineering.png",
  format: "Project-Based Learning · Live sessions · Builds · Reviews · Community",
  duration: "10 weeks",
  timeCommitment: "8–12 hours per week",
  paymentOptions: "Paystack (cards and bank transfer) or crypto via NOWPayments. One-time payment.",
  applyLabel: "Join the Next Cohort",
  programSignal: "5 Modules · 10 Weeks · 30 Sessions · Learn by Building",
  learningMode: "Project-Based Learning",
  problemTitle: "Blockchain Data Is Growing. So Is the Need for Infrastructure.",
  problemSupport:
    "Blockchains generate massive volumes of transactions, smart contract events and protocol activity. Raw blockchain data isn't immediately useful.",
  processChain: ["Extracted", "Processed", "Stored", "Transformed", "Automated", "Served"],
  definitionTitle: "What Is Blockchain Data Engineering?",
  definitionBody:
    "Blockchain Data Engineering is the process of building systems that collect, process, transform and serve blockchain data. A Blockchain Data Engineer may work with:",
  definitionItems: [
    "Blockchain RPCs",
    "Smart contract events",
    "Transaction data",
    "Event logs",
    "APIs",
    "Databases",
    "Data warehouses",
    "ETL and ELT pipelines",
    "Streaming systems",
    "Cloud infrastructure",
  ],
  systemsTitle: "Don't Just Learn Tools. Learn How the System Connects.",
  systemsIntro:
    "Most beginners learn tools separately. Real engineering happens when Python, SQL, Docker, databases and APIs work together. At Analytic Sages, you'll progressively connect the pieces.",
  systemsFlow: [
    "Blockchain & RPC Data",
    "Python + Web3.py Extraction",
    "Data Ingestion Pipelines",
    "PostgreSQL",
    "dbt Transformation",
    "Workflow Orchestration",
    "Streaming & Real-Time Data",
    "APIs & Data Products",
    "Cloud Deployment",
  ],
  journey: ["Learn", "Build", "Debug", "Improve", "Ship"],
  buildsTitle: "Build Real Onchain Data Systems",
  builds: [
    {
      title: "Blockchain Data Pipelines",
      body: "Extract transactions, logs and smart contract events from blockchain networks.",
    },
    {
      title: "Onchain Data Warehouses",
      body: "Store and structure blockchain data for analysis and applications.",
    },
    {
      title: "Analytics Engineering Pipelines",
      body: "Transform raw blockchain data into reliable datasets using dbt.",
    },
    {
      title: "Automated Data Workflows",
      body: "Schedule and monitor pipelines using orchestration tools like Prefect and Apache Airflow.",
    },
    {
      title: "Real-Time Blockchain Systems",
      body: "Explore streaming architectures and event-driven data processing with Apache Kafka.",
    },
    {
      title: "Blockchain Data APIs",
      body: "Build FastAPI services that make structured onchain data available to applications.",
    },
    {
      title: "Deployable Data Products",
      body: "Take projects from local development to cloud infrastructure on AWS, Google Cloud, Railway or Render.",
    },
  ],
  stackTitle: "Build Your Blockchain Data Engineering Stack",
  stackIntro:
    "Learn the fundamentals so you understand how data systems work — and explore modern tools so you understand where the industry is heading.",
  stackTiers: [
    { label: "Programming & Data", tools: ["Python", "SQL"] },
    {
      label: "Blockchain Data Extraction",
      tools: ["Web3.py", "RPC Providers", "HTTP APIs", "Asyncio"],
    },
    { label: "Data Storage", tools: ["PostgreSQL"] },
    { label: "Data Transformation", tools: ["dbt"] },
    { label: "Infrastructure", tools: ["Docker", "Docker Compose"] },
    { label: "Workflow Orchestration", tools: ["Prefect", "Apache Airflow"] },
    { label: "Real-Time Data", tools: ["Apache Kafka"] },
    { label: "Data Products", tools: ["FastAPI"] },
    { label: "Cloud & Deployment", tools: ["AWS", "Google Cloud", "Railway", "Render"] },
  ],
  personasTitle: "Built for Technical Builders",
  personas: [
    "Aspiring Blockchain Data Engineers",
    "Data Analysts moving into Engineering",
    "Python Developers entering Web3",
    "Software Engineers interested in blockchain infrastructure",
    "Onchain Analysts who want to build their own data pipelines",
    "Technical Researchers",
    "Builders interested in DeFi and financial infrastructure",
  ],
  careersTitle: "Where Can Blockchain Data Engineering Take You?",
  careersIntro: "The skills developed in this programme can support career paths such as:",
  careers: [
    "Blockchain Data Engineer",
    "Web3 Data Engineer",
    "Onchain Data Engineer",
    "Data Engineer",
    "Onchain Analytics Engineer",
    "Analytics Engineer",
    "Data Infrastructure Engineer",
    "Blockchain Research Engineer",
  ],
  careersNote:
    "The exact tools vary by company and role, which is why the programme focuses on both foundational engineering concepts and exposure to modern data infrastructure.",
  outcomesTitle: "What You'll Leave With",
  outcomes: [
    "Extracting real blockchain data via RPCs and Web3.py",
    "Building blockchain data ingestion pipelines",
    "Designing PostgreSQL warehouses for onchain data",
    "Transforming data with dbt and analytics engineering patterns",
    "Containerising applications with Docker",
    "Automating workflows with Prefect and Apache Airflow",
    "Understanding streaming data and Apache Kafka architectures",
    "Building blockchain data APIs with FastAPI",
    "Deploying practical data products to the cloud",
  ],
  curriculumPreviewTitle: "Your 10-Week Learning Journey",
  curriculumPreviewClose: "30 Practical Sessions. One Connected Engineering Journey.",
  curriculumPreview: [
    { range: "Module 1", title: "Blockchain & Data Engineering Foundations" },
    { range: "Module 2", title: "Blockchain Data Extraction & Pipeline Engineering" },
    { range: "Module 3", title: "Data Warehousing & Analytics Engineering" },
    { range: "Module 4", title: "Production Data Systems & Automation" },
    { range: "Module 5", title: "Cloud Deployment & Capstone Project" },
  ],
  faqs: [
    {
      question: "What is Blockchain Data Engineering?",
      answer:
        "Blockchain Data Engineering is the process of building systems that collect, process, transform and serve blockchain data — from RPCs and smart contract events through warehouses, ETL/ELT pipelines, streaming systems and cloud infrastructure.",
    },
    {
      question: "What does a Blockchain Data Engineer do?",
      answer:
        "A Blockchain Data Engineer builds data pipelines and infrastructure that power onchain analytics, DeFi applications, protocol intelligence, research platforms and data APIs. They work with Python, SQL, event logs, RPCs, databases, orchestration and often streaming or cloud systems.",
    },
    {
      question: "Do I need to know blockchain before learning Blockchain Data Engineering?",
      answer:
        "You should be interested in blockchain technology, but you do not need to be a smart contract developer. We introduce the blockchain data shapes — transactions, logs and events — as you build extraction and pipeline skills.",
    },
    {
      question: "Do I need Python or SQL experience?",
      answer:
        "Basic Python knowledge is recommended. Familiarity with data concepts and SQL helps, but you do not need years of professional data engineering experience.",
    },
    {
      question: "What tools will I learn?",
      answer:
        "You'll work with Python, SQL, Web3.py, PostgreSQL, dbt, Docker, Docker Compose, Prefect, Apache Airflow, Apache Kafka, FastAPI, and cloud deployment options including AWS, Google Cloud, Railway and Render.",
    },
    {
      question: "Will I work with real blockchain data?",
      answer:
        "Yes. The programme is built around extracting and processing real onchain data — not toy datasets disconnected from blockchain networks.",
    },
    {
      question: "What projects will I build?",
      answer:
        "You'll work toward blockchain data pipelines, onchain data warehouses, dbt analytics engineering models, automated workflows, data APIs and deployable cloud data products — culminating in a connected capstone system.",
    },
    {
      question: "Is Blockchain Data Engineering the same as Onchain Analytics?",
      answer:
        "No. Onchain analytics focuses on querying and interpreting blockchain data. Blockchain Data Engineering focuses on building the pipelines, warehouses, transformations, orchestration and APIs underneath those analytics.",
    },
    {
      question: "What career opportunities are available after learning Blockchain Data Engineering?",
      answer:
        "Skills from this programme can support paths such as Blockchain Data Engineer, Web3 Data Engineer, Onchain Data Engineer, Data Engineer, Onchain Analytics Engineer, Analytics Engineer and Data Infrastructure Engineer.",
    },
    {
      question: "How is this programme taught?",
      answer:
        "It is Project-Based Learning: live instructor-led sessions, hands-on builds, debugging, reviews and progressive projects across 5 modules, 10 weeks and 30 sessions.",
    },
    {
      question: "How long is the programme?",
      answer:
        "The Blockchain Data Engineering Programme runs for 10 weeks, with approximately 8–12 hours per week including live sessions and project work.",
    },
    {
      question: "Can I pay in installments?",
      answer:
        "Registration is currently a one-time payment at checkout via Paystack or NOWPayments unless a tuition plan is explicitly enabled for the cohort.",
    },
  ],
  curriculum: {
    seoTitle: "Blockchain Data Engineering Curriculum | 5 Modules, 30 Sessions",
    seoDescription:
      "Full Blockchain Data Engineering curriculum: Web3.py extraction, PostgreSQL warehousing, dbt analytics engineering, Prefect, Apache Airflow, Apache Kafka, FastAPI and cloud deployment across 10 weeks.",
    intro:
      "Learn Blockchain Data Engineering by building real onchain data systems. Project-Based Learning across 5 modules, 10 weeks and 30 sessions — from blockchain RPCs to cloud deployment.",
    modules: [
      {
        number: "01",
        title: "Blockchain & Data Engineering Foundations",
        body: "Set up a reproducible engineering environment and understand how blockchain data, Python and SQL fit into modern data infrastructure.",
        topics: [
          "Blockchain data fundamentals",
          "Data engineering fundamentals",
          "Python for data engineering",
          "SQL for blockchain and pipelines",
          "Docker fundamentals",
        ],
      },
      {
        number: "02",
        title: "Blockchain Data Extraction & Pipeline Engineering",
        body: "Extract real onchain data with Web3.py and turn scripts into reliable blockchain data pipelines.",
        topics: [
          "Web3.py and Ethereum RPC access",
          "Smart contract events and event logs",
          "Blockchain data extraction",
          "Data ingestion and ETL patterns",
          "Docker Compose for pipeline services",
        ],
      },
      {
        number: "03",
        title: "Data Warehousing & Analytics Engineering",
        body: "Store structured blockchain data in PostgreSQL and transform it with dbt into analytics-ready datasets.",
        topics: [
          "PostgreSQL for blockchain data",
          "Data warehousing and modelling",
          "dbt for analytics engineering",
          "Transfer and event normalisation",
          "Testing transformation models",
        ],
      },
      {
        number: "04",
        title: "Production Data Systems & Automation",
        body: "Orchestrate pipelines, explore streaming architectures and expose onchain data through APIs.",
        topics: [
          "Prefect workflow orchestration",
          "Apache Airflow DAGs",
          "Apache Kafka and streaming data",
          "Real-time blockchain data concepts",
          "FastAPI blockchain data APIs",
        ],
      },
      {
        number: "05",
        title: "Cloud Deployment & Capstone Project",
        body: "Deploy data products and present an end-to-end Blockchain Data Engineering system.",
        topics: [
          "AWS and Google Cloud for data apps",
          "Railway and Render deployment",
          "Production configuration and runbooks",
          "Capstone architecture",
          "Portfolio packaging and demo",
        ],
      },
    ],
    weeks: [
      {
        week: 1,
        title: "Foundations & Engineering Environment",
        focus: "Orientation, tooling, and reproducible local environments.",
        tools: ["Python", "Docker", "SQL"],
        objectives: [
          "Understand the Blockchain Data Engineering workflow",
          "Set up a reproducible development environment",
          "Write foundational Python and SQL for pipeline work",
        ],
        exercises: [
          "Run a baseline Docker environment",
          "Query sample tabular data with SQL",
          "Structure a project repository for engineering work",
        ],
        sessions: [
          {
            number: 1,
            title: "Programme orientation & systems thinking",
            summary: "Map the full path from chain data to product and set programme expectations.",
          },
          {
            number: 2,
            title: "Python & SQL for data engineers",
            summary: "Practical language foundations used throughout the cohort.",
          },
          {
            number: 3,
            title: "Docker fundamentals for data work",
            summary: "Containerise a simple service and understand why reproducibility matters.",
          },
        ],
      },
      {
        week: 2,
        title: "Blockchain Data Extraction",
        focus: "Pull real onchain data using Web3.py and structure extraction jobs.",
        tools: ["Python", "Web3.py", "Docker"],
        objectives: [
          "Connect to blockchain RPC endpoints",
          "Extract transactions, logs and contract events",
          "Persist raw extraction outputs reliably",
        ],
        exercises: [
          "Fetch blocks and transactions with Web3.py",
          "Decode a basic event log set",
          "Containerise an extraction job",
        ],
        project: "Raw extraction service for a chosen contract or token set.",
        sessions: [
          {
            number: 4,
            title: "Web3.py & RPC access patterns",
            summary: "Connect, request and handle blockchain node responses.",
          },
          {
            number: 5,
            title: "Transactions, receipts and event logs",
            summary: "Understand the data shapes you will extract and store.",
          },
          {
            number: 6,
            title: "Building your first extraction job",
            summary: "Ship a working job that pulls and stores raw onchain data.",
          },
        ],
      },
      {
        week: 3,
        title: "Data Pipelines",
        focus: "Turn extraction into a pipeline with validation and multi-service compose setups.",
        tools: ["Python", "Docker Compose", "PostgreSQL"],
        objectives: [
          "Design extract → validate → load steps",
          "Run multi-service environments with Docker Compose",
          "Handle failures and retries in batch jobs",
        ],
        exercises: [
          "Compose app + database services",
          "Add validation before load",
          "Log pipeline run metadata",
        ],
        sessions: [
          {
            number: 7,
            title: "Pipeline architecture for onchain data",
            summary: "Break work into dependable stages instead of one-off scripts.",
          },
          {
            number: 8,
            title: "Docker Compose for data services",
            summary: "Coordinate application and database containers locally.",
          },
          {
            number: 9,
            title: "Validation, idempotency and load",
            summary: "Make ingestion safer to re-run and easier to debug.",
          },
        ],
      },
      {
        week: 4,
        title: "Data Warehousing with PostgreSQL",
        focus: "Model and store structured blockchain data for analytical workloads.",
        tools: ["PostgreSQL", "SQL", "Docker"],
        objectives: [
          "Apply warehouse concepts to onchain entities",
          "Design schemas for transfers and events",
          "Use indexing to support analytical queries",
        ],
        exercises: [
          "Model ERC-20 transfer tables",
          "Add indexes for common query patterns",
          "Inspect schemas with database tooling",
        ],
        project: "Structured warehouse schema for extracted blockchain activity.",
        sessions: [
          {
            number: 10,
            title: "Warehouse thinking for blockchain data",
            summary: "Move from dumping JSON to designing durable tables.",
          },
          {
            number: 11,
            title: "Schema design for transfers & events",
            summary: "Normalize addresses, tokens and transfer facts.",
          },
          {
            number: 12,
            title: "Indexing and query performance basics",
            summary: "Keep analytical queries usable as volume grows.",
          },
        ],
      },
      {
        week: 5,
        title: "Analytics Engineering with dbt",
        focus: "Transform raw tables into cleaned, tested analytics-ready models.",
        tools: ["dbt", "PostgreSQL", "SQL"],
        objectives: [
          "Structure a dbt project for onchain datasets",
          "Build staging and mart layers",
          "Add tests to transformation models",
        ],
        exercises: [
          "Create staging models from raw tables",
          "Build transfer marts",
          "Add uniqueness and not-null tests",
        ],
        sessions: [
          {
            number: 13,
            title: "dbt project structure",
            summary: "Sources, models and the path from raw to marts.",
          },
          {
            number: 14,
            title: "Staging models for blockchain tables",
            summary: "Clean and standardize fields before business logic.",
          },
          {
            number: 15,
            title: "Testing and documenting models",
            summary: "Make transformations trustworthy and shareable.",
          },
        ],
      },
      {
        week: 6,
        title: "Normalization & Protocol Datasets",
        focus: "Turn messy chain records into protocol-ready analytical datasets.",
        tools: ["dbt", "SQL", "Python"],
        objectives: [
          "Normalize addresses and token metadata",
          "Model protocol-relevant entities",
          "Produce datasets ready for analytics and research",
        ],
        exercises: [
          "Build address dimension logic",
          "Create protocol activity aggregates",
          "Review model lineage",
        ],
        project: "Analytics-ready protocol dataset from your warehouse.",
        sessions: [
          {
            number: 16,
            title: "Normalization patterns for onchain data",
            summary: "Reduce duplication and inconsistency across entities.",
          },
          {
            number: 17,
            title: "Protocol analytics datasets",
            summary: "Shape tables that analysts and apps can actually use.",
          },
          {
            number: 18,
            title: "Review: transformation quality",
            summary: "Critique models, tests and documentation as a cohort.",
          },
        ],
      },
      {
        week: 7,
        title: "Orchestration with Prefect & Airflow",
        focus: "Schedule and coordinate multi-step pipelines reliably.",
        tools: ["Prefect", "Apache Airflow", "Docker"],
        objectives: [
          "Express pipelines as orchestrated workflows",
          "Understand Airflow DAGs and dependencies",
          "Handle retries, schedules and observability basics",
        ],
        exercises: [
          "Build a Prefect flow for extract → load → transform",
          "Author a simple Airflow DAG",
          "Simulate and recover from a failed task",
        ],
        sessions: [
          {
            number: 19,
            title: "Why orchestration matters",
            summary: "From manual scripts to dependable scheduled systems.",
          },
          {
            number: 20,
            title: "Prefect for practical workflows",
            summary: "Compose flows that match your existing pipeline stages.",
          },
          {
            number: 21,
            title: "Apache Airflow DAGs",
            summary: "Model dependencies and schedules with industry-standard tooling.",
          },
        ],
      },
      {
        week: 8,
        title: "Streaming Concepts & Data APIs",
        focus: "Introduce Kafka-style streaming ideas and expose data via FastAPI.",
        tools: ["Apache Kafka", "FastAPI", "PostgreSQL"],
        objectives: [
          "Understand streaming vs batch for blockchain data",
          "Work with Kafka concepts (topics, producers, consumers)",
          "Serve warehouse data through a FastAPI service",
        ],
        exercises: [
          "Sketch a streaming architecture for event ingestion",
          "Produce/consume a sample topic locally",
          "Ship a FastAPI endpoint over warehouse tables",
        ],
        project: "Data API over your analytics-ready tables.",
        sessions: [
          {
            number: 22,
            title: "Batch vs streaming for onchain systems",
            summary: "Choose the right pattern for latency and reliability.",
          },
          {
            number: 23,
            title: "Apache Kafka fundamentals",
            summary: "Topics, producers, consumers and where they fit your stack.",
          },
          {
            number: 24,
            title: "Building blockchain data APIs with FastAPI",
            summary: "Turn infrastructure into a service applications can call.",
          },
        ],
      },
      {
        week: 9,
        title: "Cloud & Deployment",
        focus: "Deploy practical projects beyond your laptop.",
        tools: ["AWS", "Google Cloud", "Railway", "Render", "Docker"],
        objectives: [
          "Package services for cloud deployment",
          "Configure environments and secrets safely",
          "Deploy at least one pipeline or API service",
        ],
        exercises: [
          "Container deploy to Railway or Render",
          "Map equivalent AWS/GCP building blocks",
          "Document runbooks for your deployed service",
        ],
        project: "Deployed service (pipeline worker, API, or both).",
        sessions: [
          {
            number: 25,
            title: "Cloud options for data products",
            summary: "Compare AWS, GCP, Railway and Render for cohort projects.",
          },
          {
            number: 26,
            title: "Deploying containerised services",
            summary: "Ship a working service with environment configuration.",
          },
          {
            number: 27,
            title: "Observability & operational basics",
            summary: "Logs, health checks and what to watch after deploy.",
          },
        ],
      },
      {
        week: 10,
        title: "Capstone Project & Demo",
        focus: "Integrate the stack and present a production-minded system.",
        tools: ["Full stack"],
        objectives: [
          "Assemble extraction → warehouse → transform → orchestration → API/deploy",
          "Document architecture decisions",
          "Demo and package work for portfolio use",
        ],
        exercises: [
          "Capstone build sprint",
          "Architecture write-up",
          "Live demo to the cohort",
        ],
        project: "End-to-end Blockchain Data Engineering capstone.",
        sessions: [
          {
            number: 28,
            title: "Capstone architecture clinic",
            summary: "Pressure-test designs before the final build push.",
          },
          {
            number: 29,
            title: "Build & integration lab",
            summary: "Connect remaining pieces and resolve production issues.",
          },
          {
            number: 30,
            title: "Demo day & portfolio packaging",
            summary: "Present what you built and how the system fits together.",
          },
        ],
      },
    ],
    facilitatorNote:
      "Sessions are live and project-driven. Facilitators guide implementation, debugging and architecture reviews — the emphasis is building working Blockchain Data Engineering systems, not watching slides.",
  },
};


export function getEngineeringProgramPage(
  slug: string,
): EngineeringProgramPageContent | undefined {
  const page = blockchainDataEngineeringProgram;
  if (page.pageSlug === slug || page.aliases.includes(slug) || page.cohortSlug === slug) {
    return page;
  }
  return undefined;
}

export function listEngineeringProgramSlugs(): string[] {
  return [
    blockchainDataEngineeringProgram.pageSlug,
    ...blockchainDataEngineeringProgram.aliases,
  ];
}
