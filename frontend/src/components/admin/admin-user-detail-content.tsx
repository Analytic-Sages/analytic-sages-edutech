"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ExternalLink, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatAdminDate } from "@/components/admin/admin-format";
import { ApiError, getAdminUserDetail, type AdminUserDetail } from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";

export function AdminUserDetailContent({ userId }: { userId: string }) {
  const [detail, setDetail] = useState<AdminUserDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminUserDetail(userId)
      .then(setDetail)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Failed to load user"))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading profile…
      </div>
    );
  }

  if (error || !detail) {
    return (
      <EmptyState
        icon={<Loader2 className="size-5" />}
        title="User not found"
        description={error ?? "This user could not be loaded."}
      />
    );
  }

  const { profile } = detail;

  return (
    <div>
      <div className="mb-4">
        <Link href="/admin/users" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
          <ArrowLeft className="size-4" />
          All users
        </Link>
      </div>

      <PageHeader title={profile.full_name || profile.email} description={profile.email} />

      <div className="mb-6 flex flex-wrap items-center gap-2">
        <Badge className="capitalize">{profile.role}</Badge>
        <Badge variant="outline">{profile.email_verified ? "Verified" : "Unverified"}</Badge>
        <Badge variant="outline">{profile.is_active ? "Active" : "Inactive"}</Badge>
        {profile.portfolio_public && <Badge variant="outline">Public portfolio</Badge>}
        <span className="text-sm text-muted-foreground">Joined {formatAdminDate(profile.created_at)}</span>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="shadow-card">
          <CardHeader><CardTitle className="text-base">Profile</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p><span className="text-muted-foreground">Phone:</span> {profile.phone_number || "—"}</p>
            <p><span className="text-muted-foreground">Country:</span> {profile.country_of_residence || "—"}</p>
            <p><span className="text-muted-foreground">Discord:</span> {profile.discord_username || "—"}</p>
            <p><span className="text-muted-foreground">Telegram:</span> {profile.telegram_username || "—"}</p>
            <div className="flex flex-wrap gap-2 pt-1">
              {profile.github_url && <a href={profile.github_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-orange hover:underline">GitHub <ExternalLink className="size-3" /></a>}
              {profile.x_url && <a href={profile.x_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-orange hover:underline">X <ExternalLink className="size-3" /></a>}
              {profile.linkedin_url && <a href={profile.linkedin_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-orange hover:underline">LinkedIn <ExternalLink className="size-3" /></a>}
              {profile.portfolio_url && <a href={profile.portfolio_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-orange hover:underline">Website <ExternalLink className="size-3" /></a>}
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-card">
          <CardHeader><CardTitle className="text-base">Live cohorts</CardTitle></CardHeader>
          <CardContent>
            {detail.cohorts.length === 0 ? (
              <p className="text-sm text-muted-foreground">No live cohorts.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {detail.cohorts.map((cohort) => (
                  <li key={cohort.cohort_id} className="flex items-center justify-between gap-2 rounded-md border p-2">
                    <div>
                      <p className="font-medium">{cohort.cohort_name}</p>
                      <p className="text-xs text-muted-foreground capitalize">{cohort.role}</p>
                    </div>
                    <Badge variant="outline" className="capitalize">{cohort.enrollment_status}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <section className="mt-6">
        <h2 className="mb-3 font-heading text-lg font-semibold">Self-paced courses</h2>
        {detail.courses.length === 0 ? (
          <p className="text-sm text-muted-foreground">No self-paced enrollments.</p>
        ) : (
          <div className="rounded-xl border shadow-card">
            <Table>
              <TableHeader><TableRow><TableHead>Course</TableHead><TableHead>Status</TableHead><TableHead>Enrolled</TableHead><TableHead>Completed</TableHead></TableRow></TableHeader>
              <TableBody>
                {detail.courses.map((course) => (
                  <TableRow key={course.course_id}>
                    <TableCell className="font-medium">{course.course_title}</TableCell>
                    <TableCell><Badge className="capitalize">{course.status}</Badge></TableCell>
                    <TableCell>{formatAdminDate(course.enrolled_at)}</TableCell>
                    <TableCell>{course.completed_at ? formatAdminDate(course.completed_at) : "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      <section className="mt-6">
        <h2 className="mb-3 font-heading text-lg font-semibold">Billing</h2>
        {detail.billing_accounts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No billing accounts.</p>
        ) : (
          <div className="rounded-xl border shadow-card">
            <Table>
              <TableHeader><TableRow><TableHead>Plan</TableHead><TableHead>Status</TableHead><TableHead>Paid</TableHead><TableHead>Outstanding</TableHead><TableHead>Next due</TableHead><TableHead>Access</TableHead></TableRow></TableHeader>
              <TableBody>
                {detail.billing_accounts.map((account) => (
                  <TableRow key={account.account_id}>
                    <TableCell>{account.plan_name || account.plan_type || "—"}</TableCell>
                    <TableCell><Badge className="capitalize">{account.billing_status.replace("_", " ")}</Badge></TableCell>
                    <TableCell>{formatPrice(Number(account.amount_paid), account.currency || "USD")}</TableCell>
                    <TableCell>{formatPrice(Number(account.amount_outstanding), account.currency || "USD")}</TableCell>
                    <TableCell>
                      {account.next_due_date
                        ? `${formatAdminDate(account.next_due_date)}${account.next_due_amount ? ` · ${formatPrice(Number(account.next_due_amount), account.currency || "USD")}` : ""}`
                        : "—"}
                    </TableCell>
                    <TableCell>
                      {account.access_blocked ? (
                        <Badge className="bg-destructive/10 text-destructive">Restricted</Badge>
                      ) : (
                        <Badge variant="outline">Enabled</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      <section className="mt-6">
        <h2 className="mb-3 font-heading text-lg font-semibold">Payments</h2>
        {detail.payments.length === 0 ? (
          <p className="text-sm text-muted-foreground">No payments.</p>
        ) : (
          <div className="rounded-xl border shadow-card">
            <Table>
              <TableHeader><TableRow><TableHead>Order</TableHead><TableHead>Item</TableHead><TableHead>Amount</TableHead><TableHead>Status</TableHead><TableHead>Date</TableHead></TableRow></TableHeader>
              <TableBody>
                {detail.payments.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell className="font-mono text-xs">{payment.order_id}</TableCell>
                    <TableCell>{payment.cohort_name || payment.course_title || "—"}</TableCell>
                    <TableCell>{formatPrice(payment.amount, payment.currency)}</TableCell>
                    <TableCell><Badge className="capitalize">{payment.status}</Badge></TableCell>
                    <TableCell>{formatAdminDate(payment.confirmed_at || payment.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      <div className="mt-6">
        <ButtonLink href="/admin/students" variant="outline">View students list</ButtonLink>
      </div>
    </div>
  );
}
