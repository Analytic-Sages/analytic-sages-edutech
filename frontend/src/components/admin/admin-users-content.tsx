"use client";

import { useEffect, useState } from "react";
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
import { ApiError, getAdminUsers, inviteAuthor, inviteEditor, inviteInstructor, inviteOperations, type AdminUserRow } from "@/lib/api";

export function AdminUsersContent() {
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);
  const [inviteRole, setInviteRole] = useState<"instructor" | "operations" | "editor" | "author">(
    "instructor"
  );
  const [inviting, setInviting] = useState(false);

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
        description="Live learner accounts. Invite instructors, operations, Insights editors, or authors. Authors cannot publish."
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
            <div className="space-y-2">
              <Label htmlFor="invite-email">Email</Label>
              <Input
                id="invite-email"
                type="email"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="staff@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite-role">Role</Label>
              <select
                id="invite-role"
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
                value={inviteRole}
                onChange={(e) =>
                  setInviteRole(e.target.value as "instructor" | "operations" | "editor" | "author")
                }
              >
                <option value="instructor">Instructor (classroom)</option>
                <option value="operations">Operations</option>
                <option value="editor">Editor (publishes Insights)</option>
                <option value="author">Author (drafts only)</option>
              </select>
            </div>
            <Button
              type="submit"
              disabled={inviting || !inviteEmail}
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
            >
              {inviting ? "Sending…" : "Send invite"}
            </Button>
          </form>
          {inviteSuccess && <p className="mt-3 text-sm text-success">{inviteSuccess}</p>}
          {inviteError && <p className="mt-3 text-sm text-destructive">{inviteError}</p>}
        </CardContent>
      </Card>

      {users.length === 0 ? (
        <EmptyState
          icon={<Loader2 className="size-6" />}
          title="No signups yet"
          description="New accounts will appear here as people register from ads and the site."
        />
      ) : (
        <div className="rounded-xl border shadow-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Verified</TableHead>
                <TableHead>Cohort 9</TableHead>
                <TableHead>Joined</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
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
                    <Badge variant="outline" className="capitalize">
                      {user.role}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {user.email_verified ? (
                      <span className="text-success">Yes</span>
                    ) : user.role === "instructor" ||
                      user.role === "operations" ||
                      user.role === "editor" ||
                      user.role === "author" ? (
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
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
