import type { Certificate, Course, Module, Quiz } from "@/types/course";

/** Placeholder curriculum until LMS modules ship from the API. */
function starterModules(
  moduleOneTitle: string,
  lessons: Array<{ id: string; title: string; duration: string; completed?: boolean }>
): Module[] {
  return [
    {
      id: "m1",
      title: moduleOneTitle,
      lessons,
      quiz: { id: "q1", title: "Module 1 Quiz" },
    },
    {
      id: "m2",
      title: "Module 2: Applied Practice",
      lessons: [
        { id: "l4", title: "Hands-on Lab Walkthrough", duration: "28 min" },
        { id: "l5", title: "Capstone Project Brief", duration: "22 min" },
      ],
    },
  ];
}

export const courses: Course[] = [
  {
    id: "1",
    slug: "applied-ai-for-blockchain",
    title: "Applied AI for Blockchain",
    description:
      "Apply machine learning and AI techniques to on-chain data, smart contracts, and DeFi protocol analysis.",
    longDescription:
      "Learn how to build practical AI systems for blockchain, from anomaly detection and wallet classification to LLM-powered transaction analysis. You'll work with real on-chain datasets and deploy models that analysts use in production.",
    thumbnail: "/applied-ai-for-blockchain.png",
    category: "AI",
    difficulty: "Intermediate",
    duration: "10 weeks",
    lessonsCount: 40,
    price: 0,
    currency: "USD",
    comingSoon: true,
    instructor: {
      name: "Analytic Sages",
      title: "Instructor",
      avatar: "AS",
    },
    rating: 4.9,
    studentsCount: 780,
    skills: [
      "Machine learning",
      "On-chain AI",
      "Anomaly detection",
      "LLM applications",
      "Python",
    ],
    requirements: [
      "Intermediate Python",
      "Basic blockchain concepts",
      "Familiarity with pandas",
    ],
    modules: starterModules("Module 1: AI for On-Chain Data", [
      { id: "l1", title: "Introduction to On-Chain AI", duration: "18 min" },
      { id: "l2", title: "Feature Engineering for Wallet Data", duration: "26 min" },
      { id: "l3", title: "Anomaly Detection Baselines", duration: "32 min" },
    ]),
  },
  {
    id: "2",
    slug: "sql-for-blockchain-analytics",
    title: "Beginner Blockchain Analytics (SQL)",
    description:
      "Master Dune, Flipside, and advanced SQL to query blockchain data like professional analysts.",
    longDescription:
      "A beginner-friendly path into Web3 data analytics. Start with blockchain explorers and on-chain fundamentals, build SQL skills on live datasets, analyze DeFi and DEX activity, and finish with dashboards that turn queries into clear insights.",
    thumbnail: "/sql-for-blockchain-analytics.png",
    category: "Blockchain",
    difficulty: "Beginner",
    duration: "4 weeks",
    lessonsCount: 18,
    price: 35,
    currency: "USD",
    comingSoon: true,
    instructor: {
      name: "Analytic Sages",
      title: "Instructor",
      avatar: "AS",
    },
    rating: 4.8,
    studentsCount: 1420,
    skills: [
      "Blockchain explorers (Etherscan)",
      "SQL for on-chain data",
      "Dune Analytics",
      "Joins, aggregations & CTEs",
      "DEX & Uniswap analysis",
      "Dashboard storytelling",
    ],
    requirements: ["No prior SQL required", "Basic computer literacy"],
    roleDescription:
      "Master Dune, Flipside, and advanced SQL to query blockchain data like professional analysts.",
    careerOutcomes: ["Onchain Analyst", "Research Analyst", "Data Analyst"],
    modules: [
      {
        id: "m1",
        title: "Introduction to Web3 Data Analytics",
        lessons: [
          {
            id: "m1-l1",
            title: "Understanding Blockchain Data: what it is and why it matters to decentralized systems",
            duration: "Session",
          },
          {
            id: "m1-l2",
            title: "Why On-chain Data Matters: DeFi monitoring, wallet tracking, fraud detection",
            duration: "Session",
          },
          {
            id: "m1-l3",
            title: "Overview of Blockchain Data Tools: Etherscan, Dune Analytics, and their roles",
            duration: "Session",
          },
          {
            id: "m1-l4",
            title:
              "Exploring Blockchain Explorers: navigate Etherscan and Blockchain.com for transactions, token flows, and contracts",
            duration: "Session",
          },
          {
            id: "m1-p1",
            title:
              "Project: Write a comprehensive Etherscan guide to analyse wallet transactions, explore smart contracts, and track token transfers",
            duration: "Project",
          },
        ],
      },
      {
        id: "m2",
        title: "SQL for Web3 Data Analytics",
        lessons: [
          {
            id: "m2-l1",
            title: "SQL Foundations in Web3: SELECT, WHERE, ORDER BY with blockchain examples",
            duration: "Session",
          },
          {
            id: "m2-l2",
            title:
              "Joins and Aggregations: combine wallet, transaction, and token data; COUNT, SUM, AVG",
            duration: "Session",
          },
          {
            id: "m2-l3",
            title:
              "Subqueries and CTEs: nested queries for top traders, protocol usage, and complex analytics",
            duration: "Session",
          },
          {
            id: "m2-p1",
            title: "Practice: Query wallet balances and transaction history",
            duration: "Practice",
          },
          {
            id: "m2-p2",
            title: "Practice: Identify active users on a DeFi protocol",
            duration: "Practice",
          },
          {
            id: "m2-p3",
            title: "Practice: Aggregate token swap volumes over time",
            duration: "Practice",
          },
        ],
      },
      {
        id: "m3",
        title: "Working with Blockchain Data",
        lessons: [
          {
            id: "m3-l1",
            title:
              "Advanced On-chain Tools: write SQL on live blockchain datasets with Dune Analytics",
            duration: "Session",
          },
          {
            id: "m3-l2",
            title:
              "Understanding Blockchain Data Tables: schema of blocks, logs, events, and traces",
            duration: "Session",
          },
          {
            id: "m3-l3",
            title:
              "Analyzing Smart Contracts & DEXs: Uniswap liquidity, volume, swaps, and top pairs",
            duration: "Session",
          },
          {
            id: "m3-p1",
            title:
              "Project: Build a SQL dashboard for Uniswap covering daily/weekly/monthly volume, liquidity pools, and unique users",
            duration: "Project",
          },
        ],
      },
      {
        id: "m4",
        title: "Building Insightful Dashboards",
        lessons: [
          {
            id: "m4-l1",
            title:
              "Token Performance Dashboard: price, holder distribution, and transaction trends (Dune or Tableau)",
            duration: "Session",
          },
          {
            id: "m4-l2",
            title:
              "Data Visualization Best Practices: charts, layout, and filters that tell a clear story",
            duration: "Session",
          },
          {
            id: "m4-p1",
            title:
              "Capstone: Design a full dashboard for a token or protocol covering price trends, wallet interaction, gas fees, retention/growth, and actionable insights",
            duration: "Capstone",
          },
        ],
      },
    ],
  },
  {
    id: "2b",
    slug: "tableau-for-web3-business-intelligence",
    title: "Tableau for Web3 Business Intelligence",
    description:
      "Turn on-chain data into clear dashboards and business insights with Tableau, built for Web3 teams and analysts.",
    longDescription:
      "A cohort program that teaches you to connect blockchain datasets, model metrics, and ship interactive Tableau dashboards for DeFi, NFT, and protocol reporting. Designed for beginners who want visual analytics skills that employers recognize.",
    thumbnail: "/1.png",
    category: "Blockchain",
    difficulty: "Beginner",
    duration: "2 months",
    lessonsCount: 20,
    price: 0,
    currency: "USD",
    comingSoon: true,
    instructor: {
      name: "Analytic Sages",
      title: "Instructor",
      avatar: "AS",
    },
    rating: 4.8,
    studentsCount: 420,
    skills: ["Tableau", "Dashboards", "KPI design", "Web3 metrics", "Storytelling"],
    requirements: ["No prior Tableau required", "Basic spreadsheet literacy"],
    roleDescription:
      "Build Web3 business intelligence dashboards with Tableau using real blockchain datasets.",
    careerOutcomes: ["BI Analyst", "Onchain Analyst", "Research Analyst"],
    modules: starterModules("Module 1: Tableau Foundations for Web3", [
      { id: "l1", title: "Connecting On-Chain Data Sources", duration: "20 min" },
      { id: "l2", title: "Building Your First Protocol Dashboard", duration: "28 min" },
      { id: "l3", title: "Storytelling with Web3 Metrics", duration: "24 min" },
    ]),
  },
  {
    id: "3",
    slug: "python-for-blockchain-analytics",
    title: "Python for Blockchain Data Analytics",
    description:
      "Build blockchain data pipelines, automate workflows, and analyze onchain activity with Python.",
    longDescription:
      "An intensive 2-month (8-week) training that builds foundational and applied Python skills for data analysis and blockchain analytics. Through a hands-on approach, participants explore how Python can analyze on-chain data, build dashboards, and extract insights from real-world blockchain transactions, ending with a capstone dashboard or report.",
    thumbnail: "/python-for-blockchain-analytics.png",
    category: "Blockchain",
    difficulty: "Beginner",
    duration: "2 months",
    lessonsCount: 20,
    price: 150,
    currency: "USD",
    comingSoon: true,
    instructor: {
      name: "Analytic Sages",
      title: "Instructor",
      avatar: "AS",
    },
    rating: 4.9,
    studentsCount: 1680,
    skills: [
      "Python fundamentals",
      "Pandas & NumPy",
      "Matplotlib & Seaborn",
      "APIs (Etherscan, CoinPaprika)",
      "web3.py",
      "Streamlit / Dash dashboards",
      "On-chain analysis",
    ],
    requirements: [
      "Basic computer literacy",
      "No prior blockchain experience required",
      "A laptop with 8GB+ RAM",
    ],
    roleDescription:
      "Build blockchain data pipelines, automate workflows, and analyze onchain activity with Python.",
    careerOutcomes: ["Blockchain Analyst", "Data Engineer", "Research Analyst"],
    enrolled: true,
    progress: 68,
    modules: [
      {
        id: "m1",
        title: "Python Fundamentals",
        lessons: [
          {
            id: "py-m1-l1",
            title: "Python syntax, variables, and data types (strings, lists, dictionaries, and more)",
            duration: "Session",
          },
          {
            id: "py-m1-l2",
            title: "Control structures: loops (for, while) and conditional statements (if-else)",
            duration: "Session",
          },
          {
            id: "py-m1-l3",
            title: "Writing and using functions; importing standard and custom modules",
            duration: "Session",
          },
          {
            id: "py-m1-l4",
            title: "Working with files (CSV, JSON) for data input/output",
            duration: "Session",
          },
          {
            id: "py-m1-l5",
            title: "Basic error handling (try-except) and debugging techniques",
            duration: "Session",
          },
          {
            id: "py-m1-l6",
            title: "Introduction to APIs: making RESTful API calls with the requests module",
            duration: "Session",
          },
          {
            id: "py-m1-h1",
            title: "Hands-on: Write Python scripts to pull data from APIs and process local data files",
            duration: "Hands-on",
          },
        ],
      },
      {
        id: "m2",
        title: "Python for Data Analysis",
        lessons: [
          {
            id: "py-m2-l1",
            title: "Data wrangling and analysis with Pandas and NumPy",
            duration: "Session",
          },
          {
            id: "py-m2-l2",
            title: "Data visualization with Matplotlib and Seaborn",
            duration: "Session",
          },
          {
            id: "py-m2-l3",
            title: "Web scraping fundamentals using BeautifulSoup and Selenium",
            duration: "Session",
          },
          {
            id: "py-m2-l4",
            title: "API data extraction: working with Etherscan and CoinPaprika APIs",
            duration: "Session",
          },
          {
            id: "py-m2-l5",
            title: "Running SQL queries with sqlite3 and integrating with Pandas (read_sql)",
            duration: "Session",
          },
          {
            id: "py-m2-p1",
            title:
              "Project: Extract token market data from an API and visualize price, volume, and trend metrics",
            duration: "Project",
          },
        ],
      },
      {
        id: "m3",
        title: "Python for Blockchain Analytics",
        lessons: [
          {
            id: "py-m3-l1",
            title: "Blockchain architecture and on-chain data structures (blocks, transactions, logs)",
            duration: "Session",
          },
          {
            id: "py-m3-l2",
            title: "Fetching on-chain data using Flipside, Dune, and Etherscan APIs",
            duration: "Session",
          },
          {
            id: "py-m3-l3",
            title: "Writing and executing blockchain queries with SQL",
            duration: "Session",
          },
          {
            id: "py-m3-l4",
            title:
              "Using web3.py to interact with Ethereum: transactions, balances, and contract data",
            duration: "Session",
          },
          {
            id: "py-m3-l5",
            title: "Building simple data dashboards using Streamlit or Dash",
            duration: "Session",
          },
          {
            id: "py-m3-p1",
            title: "Project: Build a mini-dashboard to track Uniswap token swaps or wallet activity",
            duration: "Project",
          },
        ],
      },
      {
        id: "m4",
        title: "Real-World On-chain Analysis",
        lessons: [
          {
            id: "py-m4-l1",
            title: "Analysing DEX swaps, NFT sales, and DeFi transactions",
            duration: "Session",
          },
          {
            id: "py-m4-l2",
            title: "Wallet profiling and activity tracking",
            duration: "Session",
          },
          {
            id: "py-m4-l3",
            title: "Transaction flow analysis and trend identification",
            duration: "Session",
          },
          {
            id: "py-m4-l4",
            title: "Structuring and presenting analytical reports for investors or protocol teams",
            duration: "Session",
          },
          {
            id: "py-m4-p1",
            title:
              "Capstone: Design and present a full blockchain analytics dashboard/report covering token performance, whale wallet behavior, or comparative DeFi metrics",
            duration: "Capstone",
          },
        ],
      },
    ],
  },
  {
    id: "4",
    slug: "blockchain-data-engineering",
    title: "Blockchain Data Engineering",
    description:
      "Learn how modern blockchain datasets are collected, transformed, and served at scale using Python, dbt, PostgreSQL, and cloud infrastructure.",
    longDescription:
      "Go beyond queries and learn to architect indexers, ETL pipelines, and data infrastructure for multi-chain analytics. Covers PostgreSQL, ClickHouse, Airflow, and real-world scaling patterns used by analytics teams.",
    thumbnail: "/blockchain-data-engineering.png",
    category: "Data Engineering",
    difficulty: "Intermediate",
    duration: "12 weeks",
    lessonsCount: 44,
    price: 0,
    currency: "USD",
    comingSoon: true,
    instructor: {
      name: "Analytic Sages",
      title: "Instructor",
      avatar: "AS",
    },
    rating: 4.8,
    studentsCount: 920,
    skills: ["ETL pipelines", "Indexers", "PostgreSQL", "Airflow", "Multi-chain data"],
    requirements: ["Intermediate SQL", "Basic Python", "Understanding of blockchain basics"],
    roleDescription:
      "Learn how modern blockchain datasets are collected, transformed, and served at scale using Python, dbt, PostgreSQL, and cloud infrastructure.",
    careerOutcomes: ["Blockchain Data Engineer", "Backend Engineer", "Protocol Analyst"],
    modules: starterModules("Module 1: Blockchain Data Pipelines", [
      { id: "l1", title: "Indexer Architecture Overview", duration: "20 min" },
      { id: "l2", title: "ETL Patterns for Chain Data", duration: "28 min" },
      { id: "l3", title: "Serving Analytics Tables", duration: "26 min" },
    ]),
  },
  {
    id: "5",
    slug: "quantitative-trading-with-python",
    title: "Quantitative Trading with Python",
    description:
      "Build, backtest, and evaluate crypto trading strategies using Python and quantitative methods.",
    longDescription:
      "From statistical arbitrage to momentum strategies, learn the quant workflow used by professional traders. Covers pandas, backtesting frameworks, risk metrics, and portfolio optimization applied to digital asset markets.",
    thumbnail: "/quantitative-trading-with-python.png",
    category: "Quantitative Finance",
    difficulty: "Advanced",
    duration: "10 weeks",
    lessonsCount: 38,
    price: 0,
    currency: "USD",
    comingSoon: true,
    instructor: {
      name: "Analytic Sages",
      title: "Instructor",
      avatar: "AS",
    },
    rating: 4.9,
    studentsCount: 640,
    skills: ["Backtesting", "Statistics", "Risk models", "Pandas", "Strategy design"],
    requirements: ["Intermediate Python", "Basic statistics", "Linear algebra basics"],
    modules: starterModules("Module 1: Quant Trading Foundations", [
      { id: "l1", title: "Market Data and Returns", duration: "18 min" },
      { id: "l2", title: "Building Your First Backtest", duration: "30 min" },
      { id: "l3", title: "Risk Metrics That Matter", duration: "24 min" },
    ]),
  },
];

export const certificates: Certificate[] = [
  {
    id: "cert-1",
    courseTitle: "SQL for Blockchain Analytics",
    issuedAt: "2025-11-15",
    certificateId: "AS-2025-00142",
  },
];

export const moduleQuiz: Quiz = {
  id: "q1",
  title: "Module 1 Quiz: Python & On-Chain Data Basics",
  passScore: 70,
  questions: [
    {
      id: "q1-1",
      question: "What does a blockchain transaction primarily contain?",
      options: [
        "Only the sender's email address",
        "Input references, outputs, and cryptographic signatures",
        "A SQL query result",
        "The current stock price",
      ],
      correctIndex: 1,
    },
    {
      id: "q1-2",
      question: "Which tool is commonly used to explore Ethereum transactions?",
      options: ["Etherscan", "Photoshop", "Excel only", "GitHub Actions"],
      correctIndex: 0,
    },
    {
      id: "q1-3",
      question: "What is a block hash used for?",
      options: [
        "Storing user passwords",
        "Linking blocks and verifying integrity",
        "Sending emails",
        "Rendering video",
      ],
      correctIndex: 1,
    },
  ],
};

export function getCourseBySlug(slug: string): Course | undefined {
  return courses.find((c) => c.slug === slug);
}

export function getEnrolledCourses(): Course[] {
  return courses.filter((c) => c.enrolled);
}

const featuredCourseSlugs = [
  "sql-for-blockchain-analytics",
  "python-for-blockchain-analytics",
] as const;

export function getFeaturedCourses(): Course[] {
  return featuredCourseSlugs
    .map((slug) => courses.find((c) => c.slug === slug))
    .filter((c): c is Course => c !== undefined);
}

export function getSelfPacedCourses(): Course[] {
  return courses.map((c) => ({ ...c, comingSoon: true }));
}

export function formatPrice(amount: number, currency = "USD"): string {
  if (currency === "NGN") {
    return new Intl.NumberFormat("en-NG", {
      style: "currency",
      currency: "NGN",
      maximumFractionDigits: 0,
    }).format(amount);
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: amount % 1 === 0 ? 0 : 2,
  }).format(amount);
}

/** Self-paced enrollment is gated until Bunny player is ready. Live product is Instructor-Led. */
export const LIVE_COURSE_SLUGS = new Set<string>([]);

export function isCourseLive(slug: string): boolean {
  return LIVE_COURSE_SLUGS.has(slug);
}
