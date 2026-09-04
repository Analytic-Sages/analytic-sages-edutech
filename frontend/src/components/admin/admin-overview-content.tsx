"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { StatsCard } from "@/components/shared/stats-card";
import { EmptyState } from "@/components/shared/empty-state";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  formatAdminDate,
  formatMoneyList,
  paymentStatusClass,
} from "@/components/admin/admin-format";
import { ApiError, getAdminOverview, type AdminOverview, type AdminUserRow } from "@/lib/api";
import { formatPrice } from "@/lib/mock-data";
import { isStaffRole, roleAccess, STAFF_ROLES } from "@/lib/role-access";

export function AdminOverviewContent() {
  const [data, setData] = useState<AdminOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedRole, setExpandedRole] = useState<string | null>("admin");

  useEffect(() => {
    let cancelled = false;
    getAdminOverview()
      .then((overview) => {
        if (!cancelled) setData(overview);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load admin overview");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading live numbers…
      </div>
    );
  }

  if (error || !data) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn’t load admin data"
        description={error || "Try signing in again as an admin."}
        action={{ label: "Retry", href: "/admin" }}
      />
    );
  }

  const cohort = data.featured_cohort;
  const staffUsers = data.staff_users ?? [];
  const staffTotal = data.staff_total ?? staffUsers.length;
  const roleCounts = new Map((data.roles ?? []).map((row) => [row.name, row.value]));

  return (
    <div>
      <PageHeader
        title="Featured cohort monitor"
        description="Live signups, payments, seats, and staff access from production data."
        action={
          <ButtonLink href="/admin/users" variant="outline">
            Manage users & staff
          </ButtonLink>
        }
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Signups (7 days)"
          value={data.signups_7d}
          icon="users"
          description={`${data.signups_24h} in the last 24 hours`}
        />
        <StatsCard
          title="Accounts"
          value={data.users_total}
          icon="users"
          description={`${data.users_verified} verified · ${data.students_total} students · ${staffTotal} staff`}
        />
        <StatsCard
          title="Confirmed payments"
          value={data.payments_confirmed}
          icon="payments"
          description={`${data.payments_pending} pending · ${formatMoneyList(data.revenue_by_currency)}`}
        />
        <StatsCard
          title="Featured seats"
          value={cohort?.student_seats ?? 0}
          icon="courses"
          description={
            cohort
              ? `${cohort.pending_payments} pending checkouts · ${cohort.confirmed_payments} paid`
              : "Featured cohort is not in the database yet"
          }
        />
      </div>

      {cohort && (
        <Card className="mb-8 shadow-card">
          <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle>{cohort.name}</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">
                {formatPrice(cohort.price, cohort.currency)} · Starts{" "}
                {formatAdminDate(cohort.starts_at)} · Deadline{" "}
                {formatAdminDate(cohort.registration_deadline)}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="capitalize">
                {cohort.status}
              </Badge>
              <ButtonLink href="/admin/cohort" variant="outline">
                Open roster
              </ButtonLink>
            </div>
          </CardHeader>
        </Card>
      )}

      <Card className="mb-8 shadow-card">
        <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>Staff with admin access</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              People who are not students — what each role can open in the product.
            </p>
          </div>
          <ButtonLink href="/admin/users?filter=staff" variant="outline" className="h-8 px-3 text-xs">
            All staff
          </ButtonLink>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Role counts
            </p>
            <div className="flex flex-wrap gap-2">
              {STAFF_ROLES.map((role) => {
                const access = roleAccess(role);
                const count = roleCounts.get(role) ?? 0;
                const active = expandedRole === role;
                return (
                  <button
                    key={role}
                    type="button"
                    onClick={() => setExpandedRole(active ? null : role)}
                    className={`rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                      active
                        ? "border-brand-orange bg-brand-orange/10"
                        : "hover:bg-muted/60"
                    }`}
                  >
                    <span className="font-medium">{access.label}</span>
                    <span className="ml-2 text-muted-foreground">{count}</span>
                  </button>
                );
              })}
            </div>
            {expandedRole ? (
              <RoleAccessPanel role={expandedRole} />
            ) : (
              <p className="text-sm text-muted-foreground">Select a role to see what they can access.</p>
            )}
          </div>
          <div className="space-y-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Staff accounts ({staffTotal})
            </p>
            {staffUsers.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No staff yet. Invite instructors, operations, editors, or authors from Users.
              </p>
            ) : (
              staffUsers.map((user) => <StaffUserRow key={user.id} user={user} />)
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="shadow-card">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent signups</CardTitle>
            <ButtonLink href="/admin/users" variant="outline" className="h-8 px-3 text-xs">
              All users
            </ButtonLink>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.recent_signups.length === 0 ? (
              <p className="text-sm text-muted-foreground">No accounts yet.</p>
            ) : (
              data.recent_signups.map((user) => (
                <div key={user.id} className="flex items-center justify-between gap-3 text-sm">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{user.full_name || user.email}</p>
                    <p className="truncate text-muted-foreground">{user.email}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <Badge variant="outline" className="mb-1 capitalize">
                      {user.role}
                    </Badge>
                    <p className="text-xs text-muted-foreground">{formatAdminDate(user.created_at)}</p>
                    {user.in_featured_cohort && (
                      <p className="text-xs font-medium text-brand-orange">Featured cohort</p>
                    )}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="shadow-card">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent payments</CardTitle>
            <ButtonLink href="/admin/payments" variant="outline" className="h-8 px-3 text-xs">
              All payments
            </ButtonLink>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.recent_payments.length === 0 ? (
              <p className="text-sm text-muted-foreground">No checkout attempts yet.</p>
            ) : (
              data.recent_payments.map((payment) => (
                <div key={payment.id} className="flex items-center justify-between gap-3 text-sm">
                  <div className="min-w-0">
                    <p className="truncate font-medium">
                      {payment.user_name || payment.user_email}
                    </p>
                    <p className="truncate text-muted-foreground">
                      {payment.cohort_name || payment.course_title || "Checkout"} ·{" "}
                      {formatPrice(payment.amount, payment.currency)}
                    </p>
                  </div>
                  <Badge className={paymentStatusClass(payment.status)}>{payment.status}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StaffUserRow({ user }: { user: AdminUserRow }) {
  const access = roleAccess(user.role);
  return (
    <div className="rounded-lg border px-3 py-2 text-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium">{user.full_name || user.email}</p>
          <p className="truncate text-xs text-muted-foreground">{user.email}</p>
        </div>
        <Badge variant={isStaffRole(user.role) ? "default" : "outline"} className="capitalize shrink-0">
          {access.label}
        </Badge>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Lands on {access.home} · Sees: {access.areas.slice(0, 4).join(", ")}
        {access.areas.length > 4 ? "…" : ""}
      </p>
    </div>
  );
}

function RoleAccessPanel({ role }: { role: string }) {
  const access = roleAccess(role);
  return (
    <div className="rounded-lg border bg-brand-surface/40 px-3 py-3 text-sm">
      <p className="font-medium">{access.label}</p>
      <p className="mt-1 text-muted-foreground">{access.summary}</p>
      <p className="mt-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Nav they see
      </p>
      <p className="mt-1">{access.areas.join(" · ")}</p>
      <p className="mt-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">Can</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-4 text-muted-foreground">
        {access.can.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <p className="mt-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Cannot
      </p>
      <ul className="mt-1 list-disc space-y-0.5 pl-4 text-muted-foreground">
        {access.cannot.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
