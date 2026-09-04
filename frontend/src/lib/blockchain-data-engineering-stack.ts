/** Interactive stack explorer data for Blockchain Data Engineering (landing). */

export type StackCategoryId =
  | "programming"
  | "extraction"
  | "storage"
  | "transform"
  | "infra"
  | "orchestration"
  | "realtime"
  | "products"
  | "cloud";

export type StackCategory = {
  id: StackCategoryId | "all";
  label: string;
};

export type StackTool = {
  id: string;
  name: string;
  categoryId: StackCategoryId;
  categoryLabel: string;
  /** Simple Icons slug for CDN logo; null = monogram fallback */
  iconSlug: string | null;
  brandColor: string;
  summary: string;
  uses: string[];
  /** Highlighted node in the mini stack path */
  pathHighlight: string;
};

export const STACK_CATEGORIES: StackCategory[] = [
  { id: "all", label: "All Tools" },
  { id: "programming", label: "Programming & Data" },
  { id: "extraction", label: "Blockchain Data Extraction" },
  { id: "storage", label: "Data Storage" },
  { id: "transform", label: "Data Transformation" },
  { id: "infra", label: "Infrastructure" },
  { id: "orchestration", label: "Workflow Orchestration" },
  { id: "realtime", label: "Real-Time Data" },
  { id: "products", label: "Data Products" },
  { id: "cloud", label: "Cloud & Deployment" },
];

export const STACK_FLOW_LAYERS: { label: string; tools: string[] }[] = [
  { label: "Blockchain networks", tools: ["Protocol APIs", "RPC"] },
  { label: "Data extraction", tools: ["Python", "Web3.py", "HTTP APIs"] },
  { label: "Data storage", tools: ["PostgreSQL"] },
  { label: "Data transformation", tools: ["dbt"] },
  { label: "Workflow & real-time", tools: ["Prefect", "Airflow", "Kafka"] },
  { label: "Data products", tools: ["FastAPI"] },
  { label: "Cloud deployment", tools: ["AWS", "Google Cloud", "Railway", "Render"] },
];

/** Mini path shown in the detail panel - selected tool name is highlighted. */
export const STACK_PATH = [
  "Blockchain",
  "Extraction",
  "Python",
  "PostgreSQL",
  "dbt",
  "Data product",
] as const;

export const STACK_TOOLS: StackTool[] = [
  {
    id: "python",
    name: "Python",
    categoryId: "programming",
    categoryLabel: "Programming & Data",
    iconSlug: "python",
    brandColor: "#3776AB",
    summary:
      "A core language for working with data, building pipelines and developing blockchain data applications.",
    uses: ["Data extraction", "Data transformation", "Automation", "Building data pipelines"],
    pathHighlight: "Python",
  },
  {
    id: "sql",
    name: "SQL",
    categoryId: "programming",
    categoryLabel: "Programming & Data",
    iconSlug: null,
    brandColor: "#336791",
    summary:
      "The language of structured data - query warehouses, shape analytics models and validate pipeline outputs.",
    uses: ["Querying warehouses", "Analytics engineering", "Data quality checks", "Reporting"],
    pathHighlight: "PostgreSQL",
  },
  {
    id: "web3py",
    name: "Web3.py",
    categoryId: "extraction",
    categoryLabel: "Blockchain Data Extraction",
    iconSlug: "ethereum",
    brandColor: "#627EEA",
    summary:
      "Python library for talking to Ethereum-compatible nodes - fetch blocks, logs, contracts and receipts.",
    uses: ["RPC calls", "Event / log extraction", "Contract reads", "Onchain ingestion"],
    pathHighlight: "Extraction",
  },
  {
    id: "rpc",
    name: "RPC Providers",
    categoryId: "extraction",
    categoryLabel: "Blockchain Data Extraction",
    iconSlug: "ethereum",
    brandColor: "#0B1F3A",
    summary:
      "Managed node endpoints that serve chain state reliably so your pipelines can extract without running full nodes.",
    uses: ["Stable RPC access", "Historical queries", "Multi-chain reads", "Rate-limit handling"],
    pathHighlight: "Extraction",
  },
  {
    id: "http-apis",
    name: "HTTP APIs",
    categoryId: "extraction",
    categoryLabel: "Blockchain Data Extraction",
    iconSlug: null,
    brandColor: "#F15A24",
    summary:
      "REST and HTTP interfaces for indexing services, explorers and protocol APIs alongside raw RPC extraction.",
    uses: ["Enrichment feeds", "Explorer data", "Third-party indexes", "Hybrid ingestion"],
    pathHighlight: "Extraction",
  },
  {
    id: "asyncio",
    name: "Asyncio",
    categoryId: "extraction",
    categoryLabel: "Blockchain Data Extraction",
    iconSlug: "python",
    brandColor: "#3776AB",
    summary:
      "Python’s async toolkit for concurrent network I/O - critical when pulling many blocks, logs or endpoints.",
    uses: ["Concurrent RPC calls", "Backfill jobs", "Throughput", "Non-blocking pipelines"],
    pathHighlight: "Extraction",
  },
  {
    id: "postgresql",
    name: "PostgreSQL",
    categoryId: "storage",
    categoryLabel: "Data Storage",
    iconSlug: "postgresql",
    brandColor: "#4169E1",
    summary:
      "A production-grade relational database for structured onchain datasets, warehouses and analytics tables.",
    uses: ["Onchain warehouses", "Normalized schemas", "Analytics tables", "Reliable storage"],
    pathHighlight: "PostgreSQL",
  },
  {
    id: "dbt",
    name: "dbt",
    categoryId: "transform",
    categoryLabel: "Data Transformation",
    iconSlug: "dbt",
    brandColor: "#FF694B",
    summary:
      "Analytics engineering framework that turns raw loads into tested, documented, versioned SQL models.",
    uses: ["SQL transforms", "Model testing", "Documentation", "Analytics-ready datasets"],
    pathHighlight: "dbt",
  },
  {
    id: "docker",
    name: "Docker",
    categoryId: "infra",
    categoryLabel: "Infrastructure",
    iconSlug: "docker",
    brandColor: "#2496ED",
    summary:
      "Package services and dependencies so extraction, databases and APIs run the same locally and in the cloud.",
    uses: ["Reproducible envs", "Service isolation", "Local stacks", "Deployable images"],
    pathHighlight: "Extraction",
  },
  {
    id: "docker-compose",
    name: "Docker Compose",
    categoryId: "infra",
    categoryLabel: "Infrastructure",
    iconSlug: "docker",
    brandColor: "#2496ED",
    summary:
      "Define multi-container stacks - database, workers and APIs - with one config for development and demos.",
    uses: ["Multi-service local runs", "DB + app wiring", "Dev parity", "Quick demos"],
    pathHighlight: "Extraction",
  },
  {
    id: "prefect",
    name: "Prefect",
    categoryId: "orchestration",
    categoryLabel: "Workflow Orchestration",
    iconSlug: "prefect",
    brandColor: "#070E10",
    summary:
      "Modern workflow orchestration for scheduling, observing and retrying extract → load → transform jobs.",
    uses: ["Pipeline schedules", "Retries & alerts", "Flow observability", "Production runs"],
    pathHighlight: "Data product",
  },
  {
    id: "airflow",
    name: "Apache Airflow",
    categoryId: "orchestration",
    categoryLabel: "Workflow Orchestration",
    iconSlug: "apacheairflow",
    brandColor: "#017CEE",
    summary:
      "Industry-standard DAG orchestration used widely in data teams for batch blockchain and analytics pipelines.",
    uses: ["DAG scheduling", "Dependencies", "Ops monitoring", "Batch ELT"],
    pathHighlight: "Data product",
  },
  {
    id: "kafka",
    name: "Apache Kafka",
    categoryId: "realtime",
    categoryLabel: "Real-Time Data",
    iconSlug: "apachekafka",
    brandColor: "#231F20",
    summary:
      "Streaming backbone for high-throughput event data - useful when onchain activity must move in near real time.",
    uses: ["Event streams", "Decoupled producers", "Near-real-time feeds", "Scale-out ingest"],
    pathHighlight: "Data product",
  },
  {
    id: "fastapi",
    name: "FastAPI",
    categoryId: "products",
    categoryLabel: "Data Products",
    iconSlug: "fastapi",
    brandColor: "#009688",
    summary:
      "High-performance Python APIs that expose cleaned onchain datasets as products others can consume.",
    uses: ["Data APIs", "Auth & docs", "Serving models", "Product interfaces"],
    pathHighlight: "Data product",
  },
  {
    id: "aws",
    name: "AWS",
    categoryId: "cloud",
    categoryLabel: "Cloud & Deployment",
    iconSlug: "amazonaws",
    brandColor: "#FF9900",
    summary:
      "Cloud platform for hosting databases, workers and APIs when your blockchain data systems leave the laptop.",
    uses: ["Cloud compute", "Managed data stores", "Networking", "Production deploys"],
    pathHighlight: "Data product",
  },
  {
    id: "gcp",
    name: "Google Cloud",
    categoryId: "cloud",
    categoryLabel: "Cloud & Deployment",
    iconSlug: "googlecloud",
    brandColor: "#4285F4",
    summary:
      "Alternative cloud for containers, storage and services - choose what fits your team and budget.",
    uses: ["Cloud run / VMs", "Storage", "Managed services", "Deployment practice"],
    pathHighlight: "Data product",
  },
  {
    id: "railway",
    name: "Railway",
    categoryId: "cloud",
    categoryLabel: "Cloud & Deployment",
    iconSlug: "railway",
    brandColor: "#0B0D0E",
    summary:
      "Developer-friendly hosting to ship APIs and workers quickly without heavy cloud ops overhead.",
    uses: ["Fast deploys", "Env management", "Student / MVP hosting", "API shipping"],
    pathHighlight: "Data product",
  },
  {
    id: "render",
    name: "Render",
    categoryId: "cloud",
    categoryLabel: "Cloud & Deployment",
    iconSlug: "render",
    brandColor: "#46E3B7",
    summary:
      "Simple PaaS for web services and background jobs - a practical path from local Docker to the internet.",
    uses: ["Web services", "Background workers", "Managed TLS", "Straightforward deploys"],
    pathHighlight: "Data product",
  },
];

export const DEFAULT_STACK_TOOL_ID = "python";
