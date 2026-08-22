"""Seed the six existing mock Insights articles so public URLs stay intact."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article, ArticleStatus
from app.services.article_content import paragraphs_to_body, reading_minutes

_SEEDED = [
    {
        "slug": "what-is-on-chain-analysis-beginners-guide",
        "title": "What is On-Chain Analysis? A Beginner’s Guide to Decoding Blockchain Data",
        "excerpt": "Learn how on-chain analysis works, why it matters, and which tools help you turn public blockchain data into useful insights.",
        "category": "Guides",
        "published_at": "2025-09-20",
        "featured": True,
        "cover_image_url": "/6.webp",
        "byline_name": "Analytic Sages",
        "byline_title": "Editorial",
        "paragraphs": [
            "In today’s world, blockchain technology is shaking up industries, from finance to art. You’ve probably heard of Bitcoin, Ethereum, and even NFTs, but have you ever wondered what happens behind the scenes?",
            "How do we track transactions, monitor market trends, and predict the next big shift in the blockchain ecosystem? The answer is on-chain analysis.",
            "Imagine you’re at a busy marketplace. People are exchanging goods. While most transactions happen in the open, you can’t always see who’s buying or selling what. Now picture a smart vendor in the corner with a ledger, noting every sale, every product, and every transaction. That is what blockchain does digitally, transparently, and in a way that is tamper-proof.",
            "That ledger is on-chain data, and on-chain analysis is the method used to track and analyze it.",
            "On-chain analysis is the process of studying the transactions happening on a blockchain. Networks like Bitcoin or Ethereum keep records of every transaction: who sent what, how much was sent, and when. All of this information is stored on the blockchain and is publicly visible to anyone who knows where to look.",
            "The challenge isn’t finding the data. It’s understanding it. On-chain analysis helps you break down and interpret this data so you can make informed decisions.",
            "Think of yourself as a detective with a treasure map (the blockchain). You need to find the hidden treasure: valuable insights. Here’s how on-chain analysis helps:",
            "Tracking transactions: Follow the flow of funds between wallets, whether a large whale or a regular user is moving tokens.",
            "Identifying market sentiment: Activity patterns can reveal how people feel about a token or project. Heavy buying and selling may signal a shift in sentiment or a potential price move.",
            "Measuring network health: Metrics like transaction volume, miner activity, and gas fees help you understand how healthy a blockchain is. Low activity can signal fading interest; high activity often points to growing engagement.",
            "A real-life example is Bitcoin’s price movements. On-chain analysis can help explain sudden spikes by tracking whale wallets. Large sales can precede dips; large buys can suggest a price hike is coming.",
            "Beyond price tracking, on-chain analysis is used to spot trends, analyze project growth, monitor security, and anticipate where blockchain projects may be headed.",
            "Why it matters: it supports better decisions for investors, developers, and curious learners; adds another layer of transparency on top of blockchain itself; and helps with risk management by flagging unusual patterns such as large sales or dormant wallets coming back online.",
            "Common tools for on-chain analysis include Dune Analytics for custom dashboards, Glassnode for crypto metrics, and Nansen for Ethereum address tracking and whale behavior.",
            "On-chain analysis is like a magnifying glass for the hidden stories inside blockchain data. As blockchain grows, this skill becomes more valuable, whether you’re an investor, developer, or aspiring data analyst.",
            "Want to go deeper? Join Analytic Sages and learn how to use on-chain analytics to make informed, data-driven decisions in the blockchain space.",
        ],
    },
    {
        "slug": "how-to-become-a-blockchain-data-engineer",
        "title": "How to Become a Blockchain Data Engineer in 2026",
        "excerpt": "A practical roadmap from SQL and Python basics to building production pipelines that power onchain analytics teams.",
        "category": "Career",
        "published_at": "2026-02-18",
        "featured": True,
        "cover_image_url": None,
        "byline_name": "Fatima Bello",
        "byline_title": "Senior Data Engineer",
        "paragraphs": [
            "Blockchain data engineering sits at the intersection of distributed systems, analytics, and protocol design. Companies need engineers who can ingest raw chain data, model it for analysts, and serve it reliably at scale.",
            "Start with strong SQL fundamentals. Most onchain analytics still begins with querying indexed data, whether through Dune, Flipside, or an internal warehouse. You should be comfortable with joins, window functions, and aggregations over large event tables.",
            "Next, learn Python for automation. RPC calls, batch exports, data cleaning, and orchestration scripts are daily work for data engineers in Web3. Libraries like web3.py, pandas, and requests appear in almost every pipeline.",
            "Then move into infrastructure: PostgreSQL or ClickHouse for storage, Airflow or Dagster for scheduling, and cloud services for deployment. Understanding how indexers work, and what gets lost in the indexing process, separates good engineers from great ones.",
            "Finally, build portfolio projects. Index a niche protocol, publish a dashboard, document your schema decisions, and share your work publicly. At Analytic Sages, we structure courses around exactly this progression so you graduate with proof, not just certificates.",
        ],
    },
    {
        "slug": "5-sql-patterns-every-onchain-analyst-should-know",
        "title": "5 SQL Patterns Every Onchain Analyst Should Know",
        "excerpt": "From wallet cohort analysis to DEX volume breakdowns, these query patterns show up in real analyst workflows every week.",
        "category": "Tutorials",
        "published_at": "2026-02-04",
        "featured": False,
        "cover_image_url": None,
        "byline_name": "Ada Okonkwo",
        "byline_title": "Lead Blockchain Analyst",
        "paragraphs": [
            "Onchain SQL is not just SELECT * FROM transactions. Analysts spend most of their time turning messy event logs into structured insights for researchers, investors, and protocol teams.",
            "Pattern 1: Cohort retention. Track wallets that interacted with a protocol in month one and measure how many return in subsequent months. This requires self-joins or window functions over first-activity timestamps.",
            "Pattern 2: Token flow tracing. Follow transfers between labeled and unlabeled addresses to understand treasury movements, whale activity, or bridge inflows.",
            "Pattern 3: DEX pair analytics. Aggregate swap volumes by pair, version, and chain. Analysts use this to spot liquidity migration and market share shifts across venues.",
            "Pattern 4: New user acquisition funnels. Combine contract deployment dates, first-interaction events, and referral patterns to measure growth quality, not just headline TVL.",
            "Pattern 5: Cross-protocol overlap. Identify wallets active on multiple DeFi apps to map ecosystem stickiness and partnership opportunities.",
            "These patterns form the backbone of our SQL for Blockchain Analytics course. Master them and you can answer 80% of the questions protocol teams actually ask.",
        ],
    },
    {
        "slug": "analytic-sages-students-win-chainlink-hackathon",
        "title": "Analytic Sages Students Win at the Chainlink Data Hackathon",
        "excerpt": "Three learners turned classroom projects into a winning submission: a real-time bridge monitoring dashboard built with Python and SQL.",
        "category": "Education",
        "published_at": "2026-01-22",
        "featured": True,
        "cover_image_url": None,
        "byline_name": "James Adeyemi",
        "byline_title": "Quantitative Researcher",
        "paragraphs": [
            "Hackathons are where learning meets pressure. Last month, a team of Analytic Sages students entered the Chainlink Data Hackathon with a project they initially built during a module capstone.",
            "Their submission tracked cross-chain bridge flows in real time, flagging unusual volume spikes and delayed finality patterns. The stack was deliberately simple: Python for ingestion, PostgreSQL for storage, and a lightweight dashboard for visualization.",
            "What stood out to judges was not flashy ML, but clarity. The team documented data sources, explained assumptions, and showed how their alerts would help analysts respond faster to bridge risk events.",
            "This is the model we encourage across the platform: learn a skill, ship a project, stress-test it in public, and iterate with community feedback. Several team members have since been approached for internship conversations.",
            "If you are learning with us, treat every course project as hackathon-ready. The best submissions start long before registration opens.",
        ],
    },
    {
        "slug": "building-your-first-onchain-dashboard-with-python",
        "title": "Building Your First Onchain Dashboard with Python",
        "excerpt": "Step-by-step guide to pulling Ethereum data, cleaning it, and visualizing wallet activity without over-engineering your stack.",
        "category": "Tutorials",
        "published_at": "2026-01-10",
        "featured": False,
        "cover_image_url": None,
        "byline_name": "Chidi Nwosu",
        "byline_title": "ML Engineer & Blockchain Researcher",
        "paragraphs": [
            "Many beginners assume they need a complex data stack before building anything useful. In practice, your first dashboard can run on a CSV export, a Jupyter notebook, and a few pandas transforms.",
            'Step 1: Define the question. "Which wallets increased stablecoin holdings last week?" is answerable. "Analyze everything on Ethereum" is not.',
            "Step 2: Pull data from a reliable source. Etherscan APIs, Dune exports, or RPC calls via web3.py all work depending on your comfort level and rate limits.",
            "Step 3: Normalize addresses and timestamps. Most bugs in beginner dashboards come from inconsistent casing, timezone errors, or duplicate contract entries.",
            "Step 4: Visualize one metric well. A single time-series of net inflows beats six charts nobody reads.",
            "Step 5: Publish and iterate. Share your notebook, write a short thread on what you found, and invite feedback from other analysts.",
            "This workflow mirrors the project structure in Python for Blockchain Data Analytics. Start small, ship early, and expand your pipeline as the questions get harder.",
        ],
    },
    {
        "slug": "from-analyst-to-quant-developer-career-paths",
        "title": "From Analyst to Quant Developer: Career Paths in Crypto",
        "excerpt": "How onchain analysts evolve into quant developers, and which skills bridge the gap between dashboards and systematic trading.",
        "category": "Career",
        "published_at": "2025-12-15",
        "featured": False,
        "cover_image_url": None,
        "byline_name": "James Adeyemi",
        "byline_title": "Quantitative Researcher",
        "paragraphs": [
            "The line between blockchain analyst and quant developer is blurrier than most job titles suggest. Both roles work with the same datasets. The difference is intent: analysts explain what happened; quants model what might happen next.",
            "Analysts who move into quant work usually deepen their statistics, learn backtesting frameworks, and get disciplined about overfitting. A beautiful chart that fails out-of-sample is not a strategy.",
            "Start by reproducing published research. Pick a simple momentum or mean-reversion hypothesis on a liquid asset, implement it in Python, and document where it breaks. Hiring managers respect intellectual honesty more than perfect Sharpe ratios.",
            "Learn risk metrics early: drawdown, volatility targeting, turnover, and capacity constraints. Crypto markets punish strategies that ignore fees, slippage, and regime changes.",
            "Build in public. Share notebooks, not just results. The quant developers who get hired fastest combine technical depth with clear communication.",
            "At Analytic Sages, our quantitative trading path is designed for analysts ready to make this jump, with projects that mirror real desk workflows rather than toy backtests.",
        ],
    },
]


def seed_insights_articles(db: Session) -> None:
    for item in _SEEDED:
        exists = db.scalar(select(Article.id).where(Article.slug == item["slug"]))
        if exists:
            continue
        body = paragraphs_to_body(item["paragraphs"])
        published_at = datetime.fromisoformat(item["published_at"]).replace(tzinfo=UTC)
        db.add(
            Article(
                slug=item["slug"],
                title=item["title"],
                excerpt=item["excerpt"],
                cover_image_url=item["cover_image_url"],
                category=item["category"],
                tags=[],
                body=body,
                status=ArticleStatus.PUBLISHED,
                byline_name=item["byline_name"],
                byline_title=item["byline_title"],
                featured=item["featured"],
                read_time_minutes=reading_minutes(body),
                published_at=published_at,
                newsletter_sent_at=published_at,
            )
        )
