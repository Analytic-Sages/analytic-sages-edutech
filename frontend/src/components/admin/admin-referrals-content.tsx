"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
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
  getAdminReferralConversions,
  getAdminReferralOverview,
  getAdminReferralPartners,
  getAdminReferralPayouts,
  getAdminReferralReviewQueue,
  patchAdminReferralPartner,
  patchAdminReferralPayout,
  type AdminConversionRow,
  type AdminReferralOverview,
  type PartnerPublic,
  type PartnerPayoutRow,
} from "@/lib/api";

type Tab = "overview" | "partners" | "conversions" | "payouts" | "review";

export function AdminReferralsContent() {
  const [tab, setTab] = useState<Tab>("overview");
  const [overview, setOverview] = useState<AdminReferralOverview | null>(null);
  const [partners, setPartners] = useState<PartnerPublic[]>([]);
  const [conversions, setConversions] = useState<AdminConversionRow[]>([]);
  const [payouts, setPayouts] = useState<PartnerPayoutRow[]>([]);
  const [review, setReview] = useState<AdminConversionRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getAdminReferralOverview()
      .then(async (o) => {
        const [p, c, pay, r] = await Promise.all([
          getAdminReferralPartners(),
          getAdminReferralConversions(),
          getAdminReferralPayouts(),
          getAdminReferralReviewQueue(),
        ]);
        if (cancelled) return;
        setOverview(o);
        setPartners(p);
        setConversions(c);
        setPayouts(pay);
        setReview(r);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load referrals");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [o, p, c, pay, r] = await Promise.all([
        getAdminReferralOverview(),
        getAdminReferralPartners(),
        getAdminReferralConversions(),
        getAdminReferralPayouts(),
        getAdminReferralReviewQueue(),
      ]);
      setOverview(o);
      setPartners(p);
      setConversions(c);
      setPayouts(pay);
      setReview(r);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load referrals");
    } finally {
      setLoading(false);
    }
  }

  async function setPartnerStatus(id: string, status: string) {
    await patchAdminReferralPartner(id, { status });
    await load();
  }

  async function setPayoutStatus(id: string, status: string) {
    await patchAdminReferralPayout(id, status);
    await load();
  }

  if (loading && !overview) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading referrals…
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Referral Partners"
        description="Approve partners, review commissions, and process payouts manually."
      />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["overview", "Overview"],
            ["partners", "Partners"],
            ["conversions", "Conversions"],
            ["payouts", "Payouts"],
            ["review", "Review queue"],
          ] as const
        ).map(([id, label]) => (
          <Button
            key={id}
            size="sm"
            variant={tab === id ? "default" : "outline"}
            className={tab === id ? "bg-brand-orange text-white hover:bg-brand-orange/90" : ""}
            onClick={() => setTab(id)}
          >
            {label}
          </Button>
        ))}
      </div>

      {tab === "overview" && overview ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(
            [
              ["Partners", overview.total_partners],
              ["Active", overview.active_partners],
              ["Pending apps", overview.pending_applications],
              ["Clicks", overview.total_clicks],
              ["Registrations", overview.total_registrations],
              ["Paid enrollments", overview.total_paid_enrollments],
              [`Pending (${overview.currency})`, overview.commission_pending],
              [`Available (${overview.currency})`, overview.commission_available],
              [`Paid (${overview.currency})`, overview.commission_paid],
            ] as const
          ).map(([label, value]) => (
            <div key={label} className="border-b pb-3">
              <p className="text-xs uppercase text-muted-foreground">{label}</p>
              <p className="mt-1 text-xl font-semibold">{String(value)}</p>
            </div>
          ))}
        </div>
      ) : null}

      {tab === "partners" ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Code</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {partners.map((p) => (
              <TableRow key={p.id}>
                <TableCell>{p.display_name}</TableCell>
                <TableCell>{p.referral_code || "—"}</TableCell>
                <TableCell className="capitalize">{p.status}</TableCell>
                <TableCell className="space-x-2">
                  {p.status === "pending" ? (
                    <>
                      <Button size="sm" onClick={() => setPartnerStatus(p.id, "active")}>
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setPartnerStatus(p.id, "rejected")}
                      >
                        Reject
                      </Button>
                    </>
                  ) : null}
                  {p.status === "active" ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setPartnerStatus(p.id, "suspended")}
                    >
                      Suspend
                    </Button>
                  ) : null}
                  {p.status === "suspended" ? (
                    <Button size="sm" onClick={() => setPartnerStatus(p.id, "active")}>
                      Reactivate
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}

      {tab === "conversions" ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Partner</TableHead>
              <TableHead>Learner</TableHead>
              <TableHead>Programme</TableHead>
              <TableHead>Eligible</TableHead>
              <TableHead>Commission</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {conversions.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.partner_name}</TableCell>
                <TableCell>{row.learner_email}</TableCell>
                <TableCell>{row.programme}</TableCell>
                <TableCell>
                  {row.currency} {row.eligible_amount}
                </TableCell>
                <TableCell>
                  {row.currency} {row.commission_amount}
                </TableCell>
                <TableCell className="capitalize">{row.status.replaceAll("_", " ")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}

      {tab === "payouts" ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Amount</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Requested</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {payouts.map((row) => (
              <TableRow key={row.id}>
                <TableCell>
                  {row.currency} {row.amount}
                </TableCell>
                <TableCell className="capitalize">{row.status}</TableCell>
                <TableCell>{new Date(row.requested_at).toLocaleString()}</TableCell>
                <TableCell className="space-x-2">
                  {row.status === "requested" ? (
                    <>
                      <Button size="sm" onClick={() => setPayoutStatus(row.id, "approved")}>
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setPayoutStatus(row.id, "rejected")}
                      >
                        Reject
                      </Button>
                    </>
                  ) : null}
                  {row.status === "approved" ? (
                    <Button size="sm" onClick={() => setPayoutStatus(row.id, "processing")}>
                      Mark processing
                    </Button>
                  ) : null}
                  {row.status === "processing" ? (
                    <Button size="sm" onClick={() => setPayoutStatus(row.id, "paid")}>
                      Mark paid
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}

      {tab === "review" ? (
        review.length === 0 ? (
          <p className="text-sm text-muted-foreground">No items need review.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Partner</TableHead>
                <TableHead>Learner</TableHead>
                <TableHead>Commission</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {review.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>{row.partner_name}</TableCell>
                  <TableCell>{row.learner_email}</TableCell>
                  <TableCell>
                    {row.currency} {row.commission_amount}
                  </TableCell>
                  <TableCell>{row.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )
      ) : null}
    </div>
  );
}
