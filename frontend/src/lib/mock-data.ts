import type { Certificate, Course, Quiz } from "@/types/course";

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
    price: 95000,
    currency: "NGN",
    instructor: {
      name: "Chidi Nwosu",
      title: "ML Engineer & Blockchain Researcher",
      avatar: "CN",
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
    modules: [],
  },
  {
    id: "2",
    slug: "sql-for-blockchain-analytics",
    title: "SQL for Blockchain Analytics",
    description:
      "Master SQL queries for extracting insights from blockchain datasets, Dune, and data warehouses.",
    longDescription:
      "SQL is the language of on-chain analytics. This course teaches you to write efficient queries for transactions, token transfers, DEX trades, and protocol metrics, the skills every blockchain analyst needs daily.",
    thumbnail: "/sql-for-blockchain-analytics.png",
    category: "Blockchain",
    difficulty: "Beginner",
    duration: "6 weeks",
    lessonsCount: 28,
    price: 65000,
    currency: "NGN",
    instructor: {
      name: "Fatima Bello",
      title: "Senior Data Engineer",
      avatar: "FB",
    },
    rating: 4.8,
    studentsCount: 1420,
    skills: ["SQL", "Dune Analytics", "Data modeling", "Joins & aggregations", "DeFi queries"],
    requirements: ["No prior SQL required", "Basic computer literacy"],
    modules: [],
  },
  {
    id: "3",
    slug: "python-for-blockchain-analytics",
    title: "Python for Blockchain Analytics",
    description:
      "Build blockchain analytics pipelines with Python, from RPC calls to wallet tracking and dashboards.",
    longDescription:
      "A hands-on program covering web3.py, API integrations, data cleaning, and visualization for on-chain data. You'll build scripts and tools that form the foundation of a blockchain analyst's toolkit.",
    thumbnail: "/python-for-blockchain-analytics.png",
    category: "Blockchain",
    difficulty: "Beginner",
    duration: "8 weeks",
    lessonsCount: 36,
    price: 79000,
    currency: "NGN",
    instructor: {
      name: "Ada Okonkwo",
      title: "Lead Blockchain Analyst",
      avatar: "AO",
    },
    rating: 4.9,
    studentsCount: 1680,
    skills: ["Python", "web3.py", "APIs", "Pandas", "Wallet tracking"],
    requirements: [
      "Basic Python knowledge",
      "Familiarity with blockchain concepts",
      "A laptop with 8GB+ RAM",
    ],
    enrolled: true,
    progress: 68,
    modules: [
      {
        id: "m1",
        title: "Module 1: Python & On-Chain Data Basics",
        lessons: [
          { id: "l1", title: "Introduction to On-Chain Data", duration: "18 min", completed: true },
          { id: "l2", title: "Setting Up Your Python Environment", duration: "24 min", completed: true },
          { id: "l3", title: "Reading Etherscan with Python", duration: "32 min", completed: false },
        ],
        quiz: { id: "q1", title: "Module 1 Quiz" },
      },
      {
        id: "m2",
        title: "Module 2: Wallet Analysis with Python",
        lessons: [
          { id: "l4", title: "Address Clustering Techniques", duration: "28 min" },
          { id: "l5", title: "Entity Resolution Scripts", duration: "35 min" },
        ],
      },
    ],
  },
  {
    id: "4",
    slug: "blockchain-data-engineering",
    title: "Blockchain Data Engineering",
    description:
      "Design and build production-grade pipelines for indexing, storing, and serving blockchain data.",
    longDescription:
      "Go beyond queries and learn to architect indexers, ETL pipelines, and data infrastructure for multi-chain analytics. Covers PostgreSQL, ClickHouse, Airflow, and real-world scaling patterns used by analytics teams.",
    thumbnail: "/blockchain-data-engineering.png",
    category: "Data Engineering",
    difficulty: "Intermediate",
    duration: "12 weeks",
    lessonsCount: 44,
    price: 99000,
    currency: "NGN",
    instructor: {
      name: "Fatima Bello",
      title: "Senior Data Engineer",
      avatar: "FB",
    },
    rating: 4.8,
    studentsCount: 920,
    skills: ["ETL pipelines", "Indexers", "PostgreSQL", "Airflow", "Multi-chain data"],
    requirements: ["Intermediate SQL", "Basic Python", "Understanding of blockchain basics"],
    modules: [],
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
    price: 109000,
    currency: "NGN",
    instructor: {
      name: "James Adeyemi",
      title: "Quantitative Researcher",
      avatar: "JA",
    },
    rating: 4.9,
    studentsCount: 640,
    skills: ["Backtesting", "Statistics", "Risk models", "Pandas", "Strategy design"],
    requirements: ["Intermediate Python", "Basic statistics", "Linear algebra basics"],
    modules: [],
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

export function formatPrice(amount: number, currency = "NGN"): string {
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
  }).format(amount);
}
