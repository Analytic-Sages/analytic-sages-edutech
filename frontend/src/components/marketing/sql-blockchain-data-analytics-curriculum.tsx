"use client";

import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import { ButtonLink } from "@/components/ui/button-link";

const weeks = [
  {
    week: 1, dates: "2–6 November", title: "SQL for Onchain Data & Research Foundations",
    focus: "Translate blockchain research questions into measurable metrics, then query real onchain datasets.",
    tools: ["Dune", "SQL", "AI assistants"],
    sessions: [
      { date: "Monday, 2 November", title: "Session 1: Research Questions and Blockchain Data", topics: ["Onchain research workflows; blocks, transactions, wallets, smart contracts and events", "Introduction to Dune and blockchain data schemas", "Turning a research question into measurable metrics", "AI lab: formulate research questions and explain blockchain concepts"] },
      { date: "Wednesday, 4 November", title: "Session 2: SQL for Analytical Queries", topics: ["Filtering, aggregation, joins, CTEs and window functions", "Date-based analysis and daily activity metrics", "Calculate transactions, active wallets, fees and growth rates", "AI lab: generate, explain, debug and validate SQL queries"] },
    ],
    office: "Friday, 6 November — SQL troubleshooting, query reviews, research question refinement and project clinic.",
    project: "Analyze a selected blockchain’s activity and produce a documented SQL analysis with an initial set of findings.",
  },
  {
    week: 2, dates: "9–13 November", title: "Excel, APIs & Multi-Platform Data Integration",
    focus: "Clean, combine and analyze market and onchain datasets in a reusable Excel workbook.",
    tools: ["Excel", "Power Query", "CoinGecko API", "Dune"],
    sessions: [
      { date: "Monday, 9 November", title: "Session 3: Excel for Data Analysts", topics: ["Import CSV files and structured datasets", "Clean, format, deduplicate and validate data", "XLOOKUP, SUMIFS, COUNTIFS, IFERROR and date functions", "Percentage change, growth rates and basic financial calculations; AI formula lab"] },
      { date: "Wednesday, 11 November", title: "Session 4: Connecting Data Sources and Building Dashboards", topics: ["CoinGecko market data and API fundamentals", "Refresh data with Power Query where supported", "Combine token prices with Dune onchain metrics", "Pivot tables, charts, slicers and conditional formatting; AI-assisted transformations and dashboard layouts"] },
    ],
    office: "Friday, 13 November — Excel formula clinic, API and data-import troubleshooting, workbook and data-quality review.",
    project: "Build an interactive Excel workbook combining CoinGecko market data with a selected onchain dataset, including cleaned data, calculated metrics, pivot tables and charts.",
  },
  {
    week: 3, dates: "16–20 November", title: "DeFi Protocol Intelligence",
    focus: "Compare protocols using TVL, trading volume, fees, revenue, liquidity and onchain activity.",
    tools: ["SQL", "DefiLlama", "Excel", "Dune"],
    sessions: [
      { date: "Monday, 16 November", title: "Session 5: DeFi Metrics and Protocol Analysis", topics: ["Understand TVL, trading volume, fees, revenue and liquidity", "Introduction to DefiLlama and relevant protocol data sources", "SQL-based protocol activity analysis", "Compare protocols in the same category; AI-assisted metric selection and SQL explanations"] },
      { date: "Wednesday, 18 November", title: "Session 6: DeFi Research Dashboards", topics: ["Combine protocol metrics with onchain and market data", "Growth analysis, market share and concentration", "Excel dashboards for protocol comparisons", "Interpret findings and limitations; AI-assisted chart selection and research outlines"] },
    ],
    office: "Friday, 20 November — DeFi project reviews, dashboard feedback, research methodology and metric validation.",
    project: "Compare three DeFi protocols in the same category. Submit an Excel dashboard and short research brief on growth trends, performance differences and potential risks.",
  },
  {
    week: 4, dates: "23–27 November", title: "RWA & Tokenization Research",
    focus: "Investigate tokenized real-world assets with careful definitions, source checks and comparable metrics.",
    tools: ["RWA data sources", "Excel", "SQL", "AI research tools"],
    sessions: [
      { date: "Monday, 23 November", title: "Session 7: Understanding Tokenized Assets", topics: ["Tokenized Treasuries, funds and other real-world assets", "Identify issuers, asset categories and blockchain networks", "Explore RWA data sources and their definitions", "Analyze supply, market share and historical changes where data is available; AI evidence-mapping lab"] },
      { date: "Wednesday, 25 November", title: "Session 8: RWA Data Modelling and Research", topics: ["Import and clean RWA datasets", "Calculate growth, concentration and issuer comparisons in Excel", "Design an RWA market intelligence dashboard", "Distinguish tokenized supply, market capitalization, trading volume and underlying asset value; AI consistency checks"] },
    ],
    office: "Friday, 27 November — RWA dataset and source reviews, Excel modelling support and feedback on preliminary findings.",
    project: "Produce an RWA market intelligence workbook and research memo examining a selected tokenized asset category, its major issuers and market trends.",
  },
  {
    week: 5, dates: "30 November – 4 December", title: "Perpetual Futures & Market Structure",
    focus: "Use derivatives metrics to understand market activity, positioning and changing conditions.",
    tools: ["SQL", "Excel", "Perpetual futures datasets"],
    sessions: [
      { date: "Monday, 30 November", title: "Session 9: Derivatives Data and Market Metrics", topics: ["Introduction to perpetual futures and funding rates", "Open interest, trading volume and liquidations", "Identify historical data sources and available datasets", "Analyze market activity and changes over time with SQL; AI query-validation lab"] },
      { date: "Wednesday, 2 December", title: "Session 10: Market Research Dashboards", topics: ["Excel-based funding rate and open-interest analysis", "Rolling averages, percentage changes and market comparisons", "Compare price movements with derivatives metrics", "Build a perpetual futures dashboard; use AI to challenge assumptions and structure a report"] },
    ],
    office: "Friday, 4 December — derivatives data troubleshooting, dashboard and calculation reviews, capstone topic selection.",
    project: "Analyze a selected perpetual futures venue or group of markets. Produce a dashboard and short report describing market structure, observed trends and analytical limitations.",
  },
  {
    week: 6, dates: "7–11 December", title: "AI-Assisted Research, Capstone & Publication",
    focus: "Bring SQL, Excel and research narrative together in a reproducible, portfolio-ready deliverable.",
    tools: ["SQL", "Excel", "AI assistants", "Research documentation"],
    sessions: [
      { date: "Monday, 7 December", title: "Session 11: Research Workflows and AI", topics: ["Formulate a research question and measurable hypotheses", "Combine SQL results, Excel analysis and external data sources", "Use AI to review query logic, formulas and research structure", "Verify evidence, document sources and support reproducibility", "Write executive summaries; protect credentials and verify AI-generated outputs"] },
      { date: "Wednesday, 9 December", title: "Session 12: Capstone Presentations", topics: ["Demonstrate final dashboard and workbook", "Present research methodology and findings", "Peer review and instructor feedback", "Discuss limitations, alternative explanations and next steps"] },
    ],
    office: "Friday, 11 December — final corrections, portfolio and documentation review, career pathways and next steps into research or advanced analytics.",
    project: "Final deliverable: a portfolio-ready project containing SQL queries, an Excel workbook, a custom dashboard, a written research report and a presentation.",
  },
];

export function SqlBlockchainDataAnalyticsCurriculum() {
  return (
    <div className="bg-background pb-20 text-foreground">
      <section className="relative overflow-hidden border-b border-[#0B1F3A]/10 bg-gradient-to-br from-[#0B1F3A] via-[#122A4A] to-[#0B1F3A] text-white">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(241,90,36,0.22),transparent_45%)]" />
        <div className="relative mx-auto max-w-5xl px-4 py-14 sm:px-6 sm:py-20 lg:px-8">
          <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-orange">Full curriculum · Instructor-led</p>
          <h1 className="mt-3 font-heading text-4xl font-bold tracking-tight sm:text-5xl">SQL & Excel for Blockchain Data Analytics and Research</h1>
          <p className="mt-4 max-w-2xl text-lg text-white/80">A six-week practical learning journey from blockchain data queries to market intelligence, dashboards and publishable research.</p>
          <p className="mt-6 text-sm font-medium tracking-wide text-brand-orange">6 Modules · 6 Weeks · 12 Live Sessions + Weekly Office Hours · Learn by Building</p>
          <p className="mt-2 text-sm text-white/65">Project-Based Learning · SQL · Excel · Blockchain Data · AI-Assisted Research</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <ButtonLink href="/programs/cohort-9-sql-blockchain-data-analytics" className="h-11 bg-brand-orange text-white hover:bg-brand-orange/90">Programme overview <ArrowRight className="ml-2 size-4" /></ButtonLink>
            <ButtonLink href="/contact" variant="outline" className="h-11 border-white/30 bg-transparent text-white hover:bg-white/10">Enquiry & enrolment updates</ButtonLink>
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
        <h2 className="font-heading text-2xl font-bold sm:text-3xl">Programme outcomes</h2>
        <p className="mt-3 max-w-3xl text-muted-foreground">Learn to query blockchain data, integrate market and protocol data, analyze datasets in Excel, build custom dashboards and use AI to improve analytical workflows. Applied research verticals include DeFi, real-world asset tokenization and perpetual futures.</p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {["SQL queries and documented onchain findings", "Excel workbook integrating market and onchain data", "Comparative DeFi dashboard and research brief", "RWA market intelligence workbook and memo", "Perpetual futures dashboard and market report", "Final portfolio project and presentation"].map((item) => <div key={item} className="flex gap-2 rounded-lg border border-border/70 p-3 text-sm"><Check className="mt-0.5 size-4 shrink-0 text-brand-orange" strokeWidth={2.5} />{item}</div>)}
        </div>
      </section>
      <section className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
        <h2 className="font-heading text-2xl font-bold sm:text-3xl">Six-week curriculum</h2>
        <p className="mt-3 max-w-2xl text-muted-foreground">Each week includes two instructor-led sessions, a Friday office hour and a practical project. Follow the sequence from foundations to capstone without tying the curriculum to calendar dates.</p>
        <div className="mt-8 space-y-12">
          {weeks.map((week) => <article key={week.week} id={`week-${week.week}`} className="scroll-mt-24 border-t border-border/70 pt-8">
            <p className="font-mono text-sm font-semibold text-brand-orange">Week {week.week}</p>
            <h3 className="mt-2 font-heading text-2xl font-bold">{week.title}</h3>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">{week.focus}</p>
            <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Tools and methods: {week.tools.join(" · ")}</p>
            <h4 className="mt-7 text-sm font-semibold uppercase tracking-wide">Live sessions</h4>
            <ol className="mt-3 divide-y divide-border/60 border-y border-border/60">
              {week.sessions.map((session) => <li key={session.title} className="py-5">
                <h5 className="mt-1 text-base font-semibold">{session.title}</h5>
                <ul className="mt-3 space-y-2">{session.topics.map((topic) => <li key={topic} className="flex gap-2 text-sm text-muted-foreground"><Check className="mt-0.5 size-4 shrink-0 text-brand-orange" />{topic}</li>)}</ul>
              </li>)}
            </ol>
            <p className="mt-5 rounded-lg bg-muted/60 p-4 text-sm"><span className="font-semibold text-foreground">Friday office hours: </span><span className="text-muted-foreground">{week.office}</span></p>
            <p className="mt-4 border-l-2 border-brand-orange/50 pl-4 text-sm"><span className="font-semibold">Weekly project: </span><span className="text-muted-foreground">{week.project}</span></p>
          </article>)}
        </div>
      </section>
      <section className="border-t border-border/60 bg-[#0B1F3A] text-white">
        <div className="mx-auto max-w-3xl px-4 py-14 text-center sm:px-6 sm:py-16">
          <h2 className="font-heading text-2xl font-bold sm:text-3xl">Finish with work you can show.</h2>
          <p className="mt-4 text-sm leading-relaxed text-white/75">Your capstone combines SQL queries, an Excel workbook, a custom dashboard, a written research report and a presentation. You’ll also receive feedback on your documentation and portfolio.</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/programs/cohort-9-sql-blockchain-data-analytics" className="h-11 bg-brand-orange text-white hover:bg-brand-orange/90">View programme details <ArrowRight className="ml-2 size-4" /></ButtonLink>
            <Link href="/instructor-led" className="inline-flex h-11 items-center px-4 text-sm text-white/80 underline-offset-4 hover:underline">All instructor-led programmes</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
