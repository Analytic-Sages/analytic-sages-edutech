"use client";

import { useState } from "react";
import { CheckCircle2, Play, RefreshCw, Terminal, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

type QueryResult = {
  columns: string[];
  rows: (string | number)[][];
  executionTimeMs: number;
};

const sampleSqlSnippet = `-- Dune SQL Blockchain Query: Top DEX Pools by 24h Volume
SELECT 
    project,
    version,
    sum(amount_usd) AS volume_24h_usd,
    count(distinct tx_hash) AS total_swaps
FROM DEX.trades
WHERE block_time >= now() - INTERVAL '24 hours'
GROUP BY 1, 2
ORDER BY volume_24h_usd DESC
LIMIT 5;`;

const samplePythonSnippet = `# Python Onchain Data Pipeline
import pandas as pd

tx_data = [
    {"block": 1948201, "from": "0x7a25...3B", "to": "0x11b8...9E", "eth": 12.5, "gas_gwei": 24},
    {"block": 1948202, "from": "0x3fC9...D1", "to": "0x7a25...3B", "eth": 45.0, "gas_gwei": 31},
    {"block": 1948205, "from": "0xD8dA...60", "to": "0x0000...00", "eth": 100.0, "gas_gwei": 18},
]

df = pd.DataFrame(tx_data)
print(f"Total ETH Volume: {df['eth'].sum()} ETH")
print(f"Average Gas Price: {df['gas_gwei'].mean():.1f} Gwei")`;

const mockSqlResults: QueryResult = {
  columns: ["project", "version", "volume_24h_usd", "total_swaps"],
  rows: [
    ["Uniswap", "v3", "$842,109,240", "142,890"],
    ["Curve", "v2", "$312,450,110", "48,210"],
    ["PancakeSwap", "v3", "$198,620,000", "89,450"],
    ["Balancer", "v2", "$84,150,000", "12,300"],
    ["Aerodrome", "v1", "$62,800,000", "34,120"],
  ],
  executionTimeMs: 142,
};

export function CodeSandbox() {
  const [mode, setMode] = useState<"sql" | "python">("sql");
  const [code, setCode] = useState(sampleSqlSnippet);
  const [isRunning, setIsRunning] = useState(false);
  const [hasRun, setHasRun] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleModeSwitch = (newMode: "sql" | "python") => {
    setMode(newMode);
    setCode(newMode === "sql" ? sampleSqlSnippet : samplePythonSnippet);
    setHasRun(false);
  };

  const handleRun = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      setHasRun(true);
    }, 400);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    setCode(mode === "sql" ? sampleSqlSnippet : samplePythonSnippet);
    setHasRun(false);
  };

  return (
    <div className="overflow-hidden rounded-2xl border bg-slate-950 text-slate-100 shadow-elevated">
      {/* Sandbox Bar */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 rounded-lg bg-slate-800 p-1">
            <button
              onClick={() => handleModeSwitch("sql")}
              className={`rounded-md px-3 py-1 text-xs font-semibold transition-all ${
                mode === "sql"
                  ? "bg-brand-orange text-white shadow-xs"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Dune SQL
            </button>
            <button
              onClick={() => handleModeSwitch("python")}
              className={`rounded-md px-3 py-1 text-xs font-semibold transition-all ${
                mode === "python"
                  ? "bg-brand-navy text-white shadow-xs"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Python Web3
            </button>
          </div>
          <span className="hidden text-xs text-slate-500 sm:inline">
            Interactive Onchain Lab
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-300 hover:bg-slate-700"
          >
            {copied ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
            {copied ? "Copied" : "Copy Code"}
          </button>
          <button
            onClick={handleReset}
            className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-300 hover:bg-slate-700"
          >
            <RefreshCw className="size-3" />
            Reset
          </button>
          <Button
            size="sm"
            onClick={handleRun}
            disabled={isRunning}
            className="bg-emerald-600 text-white hover:bg-emerald-500 h-8 gap-1.5 px-3 text-xs font-bold shadow-sm"
          >
            <Play className={`size-3.5 fill-current ${isRunning ? "animate-spin" : ""}`} />
            {isRunning ? "Running..." : "Run Query"}
          </Button>
        </div>
      </div>

      {/* Editor & Output Container */}
      <div className="grid gap-px bg-slate-800 lg:grid-cols-2">
        {/* Editor Area */}
        <div className="flex flex-col bg-slate-950 p-4">
          <div className="mb-2 flex items-center justify-between text-[0.7rem] text-slate-400 font-mono">
            <span>EDITABLE QUERY EDITOR</span>
            <span>{code.split("\n").length} Lines</span>
          </div>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            spellCheck={false}
            className="min-h-[220px] w-full resize-none bg-transparent font-mono text-xs leading-relaxed text-emerald-400 focus:outline-none"
          />
        </div>

        {/* Console / Output Area */}
        <div className="flex flex-col bg-slate-900/60 p-4">
          <div className="mb-2 flex items-center justify-between text-[0.7rem] text-slate-400 font-mono">
            <span className="flex items-center gap-1.5">
              <Terminal className="size-3 text-brand-orange" /> OUTPUT RESULT
            </span>
            {hasRun && (
              <span className="flex items-center gap-1 text-emerald-400 font-bold">
                <CheckCircle2 className="size-3" /> {mockSqlResults.executionTimeMs}ms
              </span>
            )}
          </div>

          {hasRun ? (
            mode === "sql" ? (
              <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950">
                <table className="w-full text-left font-mono text-[0.72rem]">
                  <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
                    <tr>
                      {mockSqlResults.columns.map((col) => (
                        <th key={col} className="px-3 py-2 font-semibold">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {mockSqlResults.rows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40">
                        {row.map((val, cellIdx) => (
                          <td key={cellIdx} className="px-3 py-2">
                            {val}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-[0.78rem] text-slate-200 leading-relaxed">
                <p className="text-emerald-400">&gt; Python execution successful.</p>
                <p className="mt-1 font-bold text-white">Total ETH Volume: 157.5 ETH</p>
                <p className="text-slate-300">Average Gas Price: 24.3 Gwei</p>
                <p className="mt-2 text-slate-500">3 transactions processed in dataframe</p>
              </div>
            )
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center rounded-lg border border-dashed border-slate-800 py-12 text-center text-slate-500">
              <Terminal className="mb-2 size-6 text-slate-600" />
              <p className="text-xs">Click &quot;Run Query&quot; to execute your blockchain query</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
