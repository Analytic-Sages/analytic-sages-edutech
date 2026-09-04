"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getReferralLeaderboard, type LeaderboardEntry } from "@/lib/api";
import { cn } from "@/lib/utils";

export function PartnersLeaderboardContent() {
  const [period, setPeriod] = useState<"all" | "monthly">("all");
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getReferralLeaderboard(period)
      .then((res) => setEntries(res.entries))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [period]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <p className="text-sm font-medium uppercase tracking-wide text-brand-orange">Partners</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-[#0B1F3A]">Leaderboard</h1>
      <p className="mt-2 text-muted-foreground">
        Ranked by successful paid enrollments — not earnings.
      </p>
      <div className="mt-6 flex gap-2">
        <Button
          variant={period === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setPeriod("all")}
          className={period === "all" ? "bg-brand-orange text-white hover:bg-brand-orange/90" : ""}
        >
          All time
        </Button>
        <Button
          variant={period === "monthly" ? "default" : "outline"}
          size="sm"
          onClick={() => setPeriod("monthly")}
          className={
            period === "monthly" ? "bg-brand-orange text-white hover:bg-brand-orange/90" : ""
          }
        >
          This month
        </Button>
        <Link href="/partners" className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}>
          Back
        </Link>
      </div>
      <div className="mt-8">
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No ranked partners yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rank</TableHead>
                <TableHead>Partner</TableHead>
                <TableHead className="text-right">Paid enrollments</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((row) => (
                <TableRow key={`${row.rank}-${row.display_name}`}>
                  <TableCell>{row.rank}</TableCell>
                  <TableCell>{row.display_name}</TableCell>
                  <TableCell className="text-right">{row.successful_enrollments}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
