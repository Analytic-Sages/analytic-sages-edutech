"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, Save } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  getAdminCohortTutors,
  getAdminCourseTutors,
  getAdminUsers,
  putAdminCohortTutors,
  putAdminCourseTutors,
  type AdminTutorRow,
  type AdminUserRow,
} from "@/lib/api";

type Props = { kind: "course" | "cohort"; slug: string; title: string };

const STAFF_ROLES = new Set(["admin", "operations", "partnerships", "editor", "author", "instructor"]);

export function AdminTutorAccessEditor({ kind, slug, title }: Props) {
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [assigned, setAssigned] = useState<AdminTutorRow[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [staff, tutors] = await Promise.all([
          getAdminUsers(500),
          kind === "course" ? getAdminCourseTutors(slug) : getAdminCohortTutors(slug),
        ]);
        if (cancelled) return;
        setUsers(staff.filter((user) => user.is_active && STAFF_ROLES.has(user.role)));
        setAssigned(tutors);
        setSelected(new Set(tutors.map((tutor) => tutor.user_id)));
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load tutors");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [kind, slug]);

  const visibleUsers = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return users;
    return users.filter((user) =>
      `${user.email} ${user.full_name ?? ""}`.toLowerCase().includes(needle),
    );
  }, [users, query]);

  function toggle(userId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) next.delete(userId);
      else next.add(userId);
      return next;
    });
  }

  async function save() {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const result =
        kind === "course"
          ? await putAdminCourseTutors(slug, [...selected])
          : await putAdminCohortTutors(slug, [...selected]);
      setAssigned(result);
      setMessage(`Saved — ${result.length} tutor${result.length === 1 ? "" : "s"} assigned.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save tutors");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading tutor access…
      </div>
    );
  }

  return (
    <div className="rounded-xl border shadow-card">
      <div className="border-b px-4 py-3">
        <h3 className="font-heading text-base font-semibold">Tutors with login access</h3>
        <p className="text-sm text-muted-foreground">
          These staff accounts can open {title} and its live sessions.
        </p>
      </div>
      <div className="p-4">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Input
            className="w-64"
            placeholder="Search staff"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Button size="sm" onClick={save} disabled={saving}>
            <Save className="size-4" />
            {saving ? "Saving…" : "Save tutors"}
          </Button>
          <span className="text-sm text-muted-foreground">
            {assigned.length} assigned · {selected.size} selected
          </span>
        </div>

        {error && (
          <p className="mb-3 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}
        {message && (
          <p className="mb-3 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
            {message}
          </p>
        )}

        {visibleUsers.length === 0 ? (
          <p className="py-6 text-sm text-muted-foreground">
            No staff accounts match. Invite instructors from Users first.
          </p>
        ) : (
          <ul className="grid gap-2 sm:grid-cols-2">
            {visibleUsers.map((user) => {
              const checked = selected.has(user.id);
              return (
                <li key={user.id}>
                  <label className="flex cursor-pointer items-center gap-2 rounded-md border p-2 text-sm hover:bg-muted/40">
                    <input type="checkbox" checked={checked} onChange={() => toggle(user.id)} />
                    <span className="min-w-0">
                      <span className="block truncate font-medium">
                        {user.full_name || user.email}
                      </span>
                      <span className="block truncate text-xs text-muted-foreground">
                        {user.email}
                      </span>
                    </span>
                    <Badge variant="outline" className="ml-auto capitalize">
                      {user.role}
                    </Badge>
                  </label>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
