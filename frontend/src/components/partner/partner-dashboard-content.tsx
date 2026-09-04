"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ApiError,
  getMyPartnerProfile,
  getPartnerConversions,
  getPartnerDashboard,
  getPartnerPayouts,
  requestPartnerPayout,
  type PartnerConversionRow,
  type PartnerDashboard,
  type PartnerPayoutRow,
  type PartnerPublic,
} from "@/lib/api";
import { cn } from "@/lib/utils";

function money(value: string | number | null | undefined, currency: string) {
  if (value == null || value === "") return "—";
  return `${currency} ${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
}

export function PartnerDashboardContent() {
  const [profile, setProfile] = useState<PartnerPublic | null | undefined>(undefined);
  const [dash, setDash] = useState<PartnerDashboard | null>(null);
  const [conversions, setConversions] = useState<PartnerConversionRow[]>([]);
  const [payouts, setPayouts] = useState<PartnerPayoutRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [payoutAmount, setPayoutAmount] = useState("");
  const [payoutCurrency, setPayoutCurrency] = useState("USD");
  const [payoutNote, setPayoutNote] = useState("");
  const [payoutMsg, setPayoutMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function reload() {
    return Promise.all([
      getPartnerDashboard().then((d) => {
        setDash(d);
        const preferred =
          d.balances_by_currency.find((b) => Number(b.available_balance) > 0)?.currency ||
          d.currency;
        setPayoutCurrency(preferred);
      }),
      getPartnerConversions().then(setConversions),
      getPartnerPayouts().then(setPayouts),
    ]);
  }

  useEffect(() => {
    getMyPartnerProfile()
      .then(async (p) => {
        setProfile(p);
        if (p?.status === "active") {
          await reload();
        }
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.detail : "Failed to load partner profile");
        setProfile(null);
      });
  }, []);

  async function onPayout(e: React.FormEvent) {
    e.preventDefault();
    setPayoutMsg(null);
    setBusy(true);
    try {
      await requestPartnerPayout(payoutAmount, payoutCurrency, payoutNote || undefined);
      setPayoutMsg("Payout requested. Admin will review and process manually.");
      setPayoutAmount("");
      await reload();
    } catch (err) {
      setPayoutMsg(err instanceof ApiError ? err.detail : "Could not request payout");
    } finally {
      setBusy(false);
    }
  }

  function share(url: string, network: "wa" | "tg" | "x") {
    const text = encodeURIComponent("Join Analytic Sages programmes with my referral link:");
    const encoded = encodeURIComponent(url);
    if (network === "wa") window.open(`https://wa.me/?text=${text}%20${encoded}`, "_blank");
    if (network === "tg")
      window.open(`https://t.me/share/url?url=${encoded}&text=${text}`, "_blank");
    if (network === "x")
      window.open(`https://twitter.com/intent/tweet?text=${text}&url=${encoded}`, "_blank");
  }

  if (profile === undefined) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading…
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="space-y-4 p-6">
        <PageHeader title="Partner dashboard" description="You are not a Referral Partner yet." />
        <Link
          href="/partners"
          className={cn(buttonVariants(), "bg-brand-orange text-white hover:bg-brand-orange/90")}
        >
          Apply on the partners page
        </Link>
      </div>
    );
  }

  if (profile.status !== "active") {
    return (
      <div className="space-y-4 p-6">
        <PageHeader
          title="Partner dashboard"
          description={`Application status: ${profile.status}. Active partners unlock the full dashboard.`}
        />
        <Link href="/partners" className={cn(buttonVariants({ variant: "outline" }))}>
          Back to programme info
        </Link>
      </div>
    );
  }

  if (!dash) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading dashboard…
      </div>
    );
  }

  const link = dash.referral_link || "";
  const selectedMin =
    dash.balances_by_currency.find((b) => b.currency === payoutCurrency)?.minimum_payout ||
    dash.minimum_payout;
  const selectedAvailable =
    dash.balances_by_currency.find((b) => b.currency === payoutCurrency)?.available_balance ||
    dash.available_balance;

  return (
    <div className="space-y-10 p-6">
      <PageHeader
        title={`Welcome, ${dash.display_name}`}
        description={`Commission rate ${(Number(dash.commission_rate) * 100).toFixed(0)}% · ${dash.hold_days}-day hold before payout eligibility`}
      />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Clicks", String(dash.clicks)],
          ["Registrations", String(dash.registrations)],
          ["Paid enrollments", String(dash.paid_enrollments)],
          ["Conversion", `${(dash.conversion_rate * 100).toFixed(1)}%`],
          ["Est. USD pending", money(dash.estimated_usd_pending, dash.reporting_currency)],
          ["Est. USD available", money(dash.estimated_usd_available, dash.reporting_currency)],
          ["Est. USD portfolio", money(dash.estimated_usd_portfolio, dash.reporting_currency)],
        ].map(([label, value]) => (
          <div key={label} className="border-b border-border/60 pb-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
            <p className="mt-1 text-xl font-semibold text-[#0B1F3A]">{value}</p>
          </div>
        ))}
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Balances by currency</h2>
        <p className="text-sm text-muted-foreground">
          Ledger balances stay in the payment currency. USD figures are reporting estimates only.
        </p>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Currency</TableHead>
              <TableHead>Pending</TableHead>
              <TableHead>Available</TableHead>
              <TableHead>Paid out</TableHead>
              <TableHead>Min payout</TableHead>
              <TableHead>Est. USD avail.</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {dash.balances_by_currency.map((row) => (
              <TableRow key={row.currency}>
                <TableCell className="font-medium">{row.currency}</TableCell>
                <TableCell>{money(row.pending_commission, row.currency)}</TableCell>
                <TableCell>{money(row.available_balance, row.currency)}</TableCell>
                <TableCell>{money(row.total_paid_out, row.currency)}</TableCell>
                <TableCell>{money(row.minimum_payout, row.currency)}</TableCell>
                <TableCell>
                  {money(row.estimated_usd_available, dash.reporting_currency)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">My referral link</h2>
        <div className="flex flex-wrap items-center gap-2">
          <code className="rounded bg-muted px-3 py-2 text-sm">{link}</code>
          <Button
            size="sm"
            variant="outline"
            onClick={() => navigator.clipboard.writeText(link)}
          >
            Copy
          </Button>
          <Button size="sm" variant="outline" onClick={() => share(link, "wa")}>
            WhatsApp
          </Button>
          <Button size="sm" variant="outline" onClick={() => share(link, "tg")}>
            Telegram
          </Button>
          <Button size="sm" variant="outline" onClick={() => share(link, "x")}>
            X
          </Button>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Commissions</h2>
        {conversions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No commissions yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Programme</TableHead>
                <TableHead>Learner</TableHead>
                <TableHead>Payment</TableHead>
                <TableHead>Commission</TableHead>
                <TableHead>Est. USD</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {conversions.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>{new Date(row.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>{row.programme}</TableCell>
                  <TableCell>{row.learner_label}</TableCell>
                  <TableCell>{money(row.eligible_amount, row.currency)}</TableCell>
                  <TableCell>{money(row.commission_amount, row.currency)}</TableCell>
                  <TableCell>
                    {money(row.reporting_usd_equivalent, dash.reporting_currency)}
                  </TableCell>
                  <TableCell className="capitalize">{row.status.replaceAll("_", " ")}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Payouts</h2>
        <p className="text-sm text-muted-foreground">
          Request payouts per currency (no mixed-currency aggregation). Minimum for{" "}
          {payoutCurrency}: {money(selectedMin, payoutCurrency)}. Available:{" "}
          {money(selectedAvailable, payoutCurrency)}.
        </p>
        <form onSubmit={onPayout} className="flex max-w-2xl flex-wrap items-end gap-3">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Currency</label>
            <select
              className="flex h-9 w-[110px] rounded-md border border-input bg-transparent px-3 text-sm"
              value={payoutCurrency}
              onChange={(e) => setPayoutCurrency(e.target.value)}
            >
              {dash.balances_by_currency.map((b) => (
                <option key={b.currency} value={b.currency}>
                  {b.currency}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Amount</label>
            <Input
              value={payoutAmount}
              onChange={(e) => setPayoutAmount(e.target.value)}
              placeholder={String(selectedMin)}
              required
            />
          </div>
          <div className="min-w-[180px] flex-1 space-y-1">
            <label className="text-xs text-muted-foreground">Payout instructions ref</label>
            <Input
              value={payoutNote}
              onChange={(e) => setPayoutNote(e.target.value)}
              placeholder="Bank / wallet reference for admin"
            />
          </div>
          <Button
            type="submit"
            disabled={busy}
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            {busy ? "Requesting…" : "Request payout"}
          </Button>
        </form>
        {payoutMsg ? <p className="text-sm text-muted-foreground">{payoutMsg}</p> : null}
        {payouts.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Requested</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {payouts.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>{new Date(row.requested_at).toLocaleDateString()}</TableCell>
                  <TableCell>{money(row.amount, row.currency)}</TableCell>
                  <TableCell className="capitalize">{row.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : null}
      </section>
    </div>
  );
}
