"use client";

import { useEffect, useMemo, useState, Fragment } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatAdminDate, initialsFor } from "@/components/admin/admin-format";
import {
  ApiError,
  getAdminUsers,
  inviteAuthor,
  inviteEditor,
  inviteInstructor,
  inviteOperations,
  type AdminUserRow,
} from "@/lib/api";
import { isStaffRole, roleAccess, STAFF_ROLES } from "@/lib/role-access";

type StaffInviteRole = "instructor" | "operations" | "editor" | "author";
type UserFilter = "all" | "staff" | "students";

const ROLE_LABELS: Record<StaffInviteRole, string> = {
  instructor: "instructor",
  operations: "operations",
  editor: "editor",
  author: "author",
};

function matchesQuery(user: AdminUserRow, query: string) {
  const q = query.trim().toLowerCase();
  if (!q) return false;
  return (
    user.email.toLowerCase().includes(q) ||
    (user.full_name || "").toLowerCase().includes(q)
  );
}

export function AdminUsersContent() {
  const searchParams = useSearchParams();
  const initialFilter = searchParams.get("filter") === "staff" ? "staff" : "all";
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);
  const [inviteRole, setInviteRole] = useState<StaffInviteRole>("instructor");
  const [inviting, setInviting] = useState(false);
  const [filter, setFilter] = useState<UserFilter>(initialFilter);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  function loadUsers() {
    return getAdminUsers()
      .then(setUsers)
      .catch((err) => {
        setError(err instanceof ApiError ? err.detail : "Failed to load users");
      });
  }

  useEffect(() => {
    let cancelled = false;
    getAdminUsers()
      .then((rows) => {
        if (!cancelled) setUsers(rows);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load users");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const matches = useMemo(() => {
    if (inviteEmail.trim().length < 2) return [];
    return users.filter((user) => matchesQuery(user, inviteEmail)).slice(0, 6);
  }, [inviteEmail, users]);

  const exactMatch = useMemo(() => {
    const email = inviteEmail.trim().toLowerCase();
    if (!email) return null;
    return users.find((user) => user.email.toLowerCase() === email) || null;
  }, [inviteEmail, users]);

  const submitLabel = useMemo(() => {
    if (!exactMatch) return "Send invite";
    if (exactMatch.role === inviteRole) return "Already this role";
    if (exactMatch.role === "admin") return "Already admin";
    if (exactMatch.role === "student") return `Promote to ${ROLE_LABELS[inviteRole]}`;
    return `Change to ${ROLE_LABELS[inviteRole]}`;
  }, [exactMatch, inviteRole]);

  const staffCount = useMemo(() => users.filter((u) => isStaffRole(u.role)).length, [users]);
  const studentCount = useMemo(() => users.filter((u) => u.role === "student").length, [users]);

  const tableUsers = useMemo(() => {
    let rows = users;
    if (filter === "staff") rows = rows.filter((user) => isStaffRole(user.role));
    if (filter === "students") rows = rows.filter((user) => user.role === "student");
    if (inviteEmail.trim().length >= 2) {
      rows = rows.filter((user) => matchesQuery(user, inviteEmail));
    }
    return rows;
  }, [users, filter, inviteEmail]);

  function selectMatch(user: AdminUserRow) {
    setInviteEmail(user.email);
    if (user.full_name) setInviteName(user.full_name);
  }

  async function onInvite(event: React.FormEvent) {
    event.preventDefault();
    setInviteError(null);
    setInviteSuccess(null);
    setInviting(true);
    try {
      const result =
        inviteRole === "operations"
          ? await inviteOperations(inviteEmail.trim(), inviteName.trim() || undefined)
          : inviteRole === "editor"
            ? await inviteEditor(inviteEmail.trim(), inviteName.trim() || undefined)
            : inviteRole === "author"
              ? await inviteAuthor(inviteEmail.trim(), inviteName.trim() || undefined)
              : await inviteInstructor(inviteEmail.trim(), inviteName.trim() || undefined);
      setInviteSuccess(result.message);
      setInviteEmail("");
      setInviteName("");
      await loadUsers();
    } catch (err) {
      setInviteError(err instanceof ApiError ? err.detail : "Could not send invite");
    } finally {
      setInviting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading users…
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={<Loader2 className="size-6" />}
        title="Couldn’t load users"
        description={error}
        action={{ label: "Retry", href: "/admin/users" }}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Users"
        description="Students and staff with admin access. Expand a staff row to see what they can open."
      />

      <Card className="mb-8 shadow-card">
        <CardHeader>
          <CardTitle>Invite staff</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onInvite} className="grid gap-4 sm:grid-cols-[1fr_1fr_auto_auto] sm:items-end">
            <div className="space-y-2">
              <Label htmlFor="invite-name">Name</Label>
              <Input
                id="invite-name"
                value={inviteName}
                onChange={(e) => setInviteName(e.target.value)}
                placeholder="Ada Okonkwo"
              />
            </div>
            <div className="relative space-y-2">
              <Label htmlFor="invite-email">Email or search users</Label>
              <Input
                id="invite-email"
                type="text"
                inputMode="email"
                autoComplete="off"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="Search by name or email…"
              />
              {matches.length > 0 ? (
                <div className="absolute z-20 mt-1 max-h-56 w-full overflow-auto rounded-lg border bg-background shadow-card">
                  {matches.map((user) => (
                    <button
                      key={user.id}
                      type="button"
                      className="flex w-full items-start gap-3 px-3 py-2 text-left text-sm hover:bg-muted/60"
                      onClick={() => selectMatch(user)}
                    >
                      <Avatar className="mt-0.5 size-7">
                        <AvatarFallback className="bg-brand-navy text-[10px] text-white">
                          {initialsFor(user.full_name, user.email)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium">{user.full_name || user.email}</span>
                        <span className="block truncate text-xs text-muted-foreground">{user.email}</span>
                      </span>
                      <Badge variant="outline" className="capitalize">
                        {user.role}
                      </Badge>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite-role">Role</Label>
              <select
                id="invite-role"
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as StaffInviteRole)}
              >
                <option value="instructor">Instructor (classroom)</option>
                <option value="operations">Operations</option>
                <option value="editor">Editor (publishes Insights)</option>
                <option value="author">Author (drafts only)</option>
              </select>
            </div>
            <Button
              type="submit"
              disabled={
                inviting ||
                !inviteEmail.trim() ||
                exactMatch?.role === "admin" ||
                exactMatch?.role === inviteRole
              }
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
            >
              {inviting ? "Saving…" : submitLabel}
            </Button>
          </form>
          {exactMatch && exactMatch.role !== inviteRole && exactMatch.role !== "admin" ? (
            <p className="mt-3 text-xs text-muted-foreground">
              Matched {exactMatch.full_name || exactMatch.email} ({exactMatch.role}). Submitting will
              {exactMatch.role === "student" ? " promote" : " change"} them to {ROLE_LABELS[inviteRole]}.
            </p>
          ) : null}
          {inviteSuccess && <p className="mt-3 text-sm text-success">{inviteSuccess}</p>}
          {inviteError && <p className="mt-3 text-sm text-destructive">{inviteError}</p>}
        </CardContent>
      </Card>

      <div className="mb-4 flex flex-wrap gap-2">
        <Button
          size="sm"
          variant={filter === "all" ? "default" : "outline"}
          onClick={() => setFilter("all")}
        >
          All ({users.length})
        </Button>
        <Button
          size="sm"
          variant={filter === "staff" ? "default" : "outline"}
          onClick={() => setFilter("staff")}
        >
          Staff access ({staffCount})
        </Button>
        <Button
          size="sm"
          variant={filter === "students" ? "default" : "outline"}
          onClick={() => setFilter("students")}
        >
          Students ({studentCount})
        </Button>
      </div>

      {filter === "staff" ? (
        <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {STAFF_ROLES.map((role) => {
            const access = roleAccess(role);
            const count = users.filter((u) => u.role === role).length;
            return (
              <div key={role} className="rounded-xl border px-4 py-3 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{access.label}</p>
                  <Badge variant="outline">{count}</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{access.summary}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Home {access.home} · {access.areas.slice(0, 3).join(", ")}
                  {access.areas.length > 3 ? "…" : ""}
                </p>
              </div>
            );
          })}
        </div>
      ) : null}

      {users.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No signups yet"
          description="New accounts will appear here as people register from ads and the site."
        />
      ) : tableUsers.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No matching users"
          description="Try a different filter, name, or email."
        />
      ) : (
        <div className="rounded-xl border shadow-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Access</TableHead>
                <TableHead>Verified</TableHead>
                <TableHead>Featured</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {tableUsers.map((user) => {
                const access = roleAccess(user.role);
                const open = expandedId === user.id;
                return (
                  <Fragment key={user.id}>
                    <TableRow>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="size-8">
                            <AvatarFallback className="bg-brand-navy text-xs text-white">
                              {initialsFor(user.full_name, user.email)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium">{user.full_name || "-"}</p>
                            <p className="text-xs text-muted-foreground">{user.email}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={isStaffRole(user.role) ? "default" : "outline"}
                          className="capitalize"
                        >
                          {access.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[16rem] text-xs text-muted-foreground">
                        {access.areas.slice(0, 3).join(" · ")}
                        {access.areas.length > 3 ? "…" : ""}
                      </TableCell>
                      <TableCell>
                        {user.email_verified ? (
                          <span className="text-success">Yes</span>
                        ) : isStaffRole(user.role) && user.role !== "admin" ? (
                          <span className="text-brand-orange">Invite sent</span>
                        ) : (
                          <span className="text-muted-foreground">No</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {user.role === "instructor" && user.in_featured_cohort ? (
                          <span className="font-medium text-brand-orange">Staff</span>
                        ) : user.in_featured_cohort ? (
                          <span className="font-medium text-brand-orange">Seat</span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatAdminDate(user.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setExpandedId(open ? null : user.id)}
                        >
                          {open ? "Hide" : "What they see"}
                        </Button>
                      </TableCell>
                    </TableRow>
                    {open ? (
                      <TableRow>
                        <TableCell colSpan={7} className="bg-brand-surface/40">
                          <div className="grid gap-3 py-2 text-sm sm:grid-cols-3">
                            <div>
                              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Lands on
                              </p>
                              <p className="mt-1 font-medium">{access.home}</p>
                              <p className="mt-2 text-muted-foreground">{access.summary}</p>
                            </div>
                            <div>
                              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Nav / areas
                              </p>
                              <p className="mt-1">{access.areas.join(" · ")}</p>
                              <p className="mt-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Can
                              </p>
                              <ul className="mt-1 list-disc space-y-0.5 pl-4 text-muted-foreground">
                                {access.can.map((item) => (
                                  <li key={item}>{item}</li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Cannot
                              </p>
                              <ul className="mt-1 list-disc space-y-0.5 pl-4 text-muted-foreground">
                                {access.cannot.map((item) => (
                                  <li key={item}>{item}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : null}
                  </Fragment>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
