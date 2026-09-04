"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { StatsCard } from "@/components/shared/stats-card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  formatAdminDate,
  initialsFor,
  paymentStatusClass,
} from "@/components/admin/admin-format";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  ApiError,
  getAdminCohort,
  getAdminOverview,
  type AdminCohortDetail,
} from "@/lib/api";
import { FEATURED_COHORT_SLUG } from "@/lib/auth-redirect";
import { formatPrice } from "@/lib/mock-data";

export function AdminCohortContent() {
  const [detail, setDetail] = useState<AdminCohortDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        try {
          const featured = await getAdminCohort(FEATURED_COHORT_SLUG);
          if (!cancelled) setDetail(featured);
          return;
        } catch (err) {
          if (!(err instanceof ApiError) || err.status !== 404) throw err;
        }
        const overview = await getAdminOverview();
        if (!overview.featured_cohort) {
          if (!cancelled) setDetail(null);
          return;
        }
        const fallback = await getAdminCohort(overview.featured_cohort.slug);
        if (!cancelled) setDetail(fallback);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load featured cohort");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading featured cohort…
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn’t load featured cohort"
        description={error}
        action={{ label: "Retry", href: "/admin/cohort" }}
      />
    );
  }

  if (!detail) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Featured cohort is not seeded"
        description="No featured cohort was found. Seed Blockchain Data Engineering on the API, then refresh."
      />
    );
  }

  const { cohort, members, payments } = detail;
  const students = members.filter((member) => member.role === "student");

  return (
    <div>
      <PageHeader
        title={cohort.name}
        description={`Live roster and checkouts. Price ${formatPrice(cohort.price, cohort.currency)}.`}
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="Student seats" value={cohort.student_seats} icon="users" />
        <StatsCard title="Staff" value={cohort.staff_count} icon="courses" />
        <StatsCard title="Paid" value={cohort.confirmed_payments} icon="payments" />
        <StatsCard
          title="Pending checkout"
          value={cohort.pending_payments}
          icon="trending"
          description={`Deadline ${formatAdminDate(cohort.registration_deadline)}`}
        />
      </div>

      <div className="mb-10">
        <h2 className="mb-4 font-heading text-xl font-semibold">Roster</h2>
        {students.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No student seats yet. Seats appear after payment is confirmed.
          </p>
        ) : (
          <div className="rounded-xl border shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Student</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Verified</TableHead>
                  <TableHead>Joined</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="size-8">
                          <AvatarFallback className="bg-brand-navy text-xs text-white">
                            {initialsFor(member.full_name, member.email)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{member.full_name || "-"}</p>
                          <p className="text-xs text-muted-foreground">{member.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="capitalize">{member.role}</TableCell>
                    <TableCell>{member.email_verified ? "Yes" : "No"}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatAdminDate(member.joined_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-4 font-heading text-xl font-semibold">Cohort checkouts</h2>
        {payments.length === 0 ? (
          <p className="text-sm text-muted-foreground">No Cohort 9 checkouts yet.</p>
        ) : (
          <div className="rounded-xl border shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Order</TableHead>
                  <TableHead>Student</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {payments.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell className="font-mono text-xs">{payment.order_id}</TableCell>
                    <TableCell>
                      <p className="font-medium">{payment.user_name || "-"}</p>
                      <p className="text-xs text-muted-foreground">{payment.user_email}</p>
                    </TableCell>
                    <TableCell>{formatPrice(payment.amount, payment.currency)}</TableCell>
                    <TableCell>
                      <Badge className={paymentStatusClass(payment.status)}>{payment.status}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatAdminDate(payment.confirmed_at || payment.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
}
