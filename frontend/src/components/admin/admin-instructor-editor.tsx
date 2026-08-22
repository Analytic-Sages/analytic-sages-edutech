"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Loader2, Plus, Trash2, UserRound } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ApiError,
  createAdminInstructorProfile,
  deleteAdminInstructorProfile,
  getAdminCohortInstructors,
  getAdminCourseInstructors,
  listAdminInstructorProfiles,
  putAdminCohortInstructors,
  putAdminCourseInstructors,
  updateAdminInstructorProfile,
  type InstructorProfileAdmin,
  type InstructorPublic,
} from "@/lib/api";

type Props = {
  kind: "course" | "cohort";
  slug: string;
  title: string;
};

type Draft = {
  name: string;
  title: string;
  photo_url: string;
  bullets: string[];
  role_label: string;
};

const EMPTY_DRAFT: Draft = {
  name: "",
  title: "",
  photo_url: "",
  bullets: ["", "", "", "", ""],
  role_label: "Instructor",
};

function toDraft(profile: Pick<InstructorPublic, "name" | "title" | "photo_url" | "bullets">): Draft {
  return {
    name: profile.name,
    title: profile.title,
    photo_url: profile.photo_url ?? "",
    bullets: [...profile.bullets, "", "", "", "", ""].slice(0, 5),
    role_label: "Instructor",
  };
}

function writePayload(draft: Draft) {
  return {
    name: draft.name.trim(),
    title: draft.title.trim(),
    photo_url: draft.photo_url.trim() || null,
    bullets: draft.bullets.map((item) => item.trim()).filter(Boolean),
  };
}

export function AdminInstructorEditor({ kind, slug, title }: Props) {
  const [profiles, setProfiles] = useState<InstructorProfileAdmin[]>([]);
  const [assigned, setAssigned] = useState<InstructorPublic[]>([]);
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [pickId, setPickId] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = () =>
    Promise.all([
      listAdminInstructorProfiles(),
      kind === "course" ? getAdminCourseInstructors(slug) : getAdminCohortInstructors(slug),
    ]).then(([nextProfiles, nextAssigned]) => {
      setProfiles(nextProfiles);
      setAssigned(nextAssigned);
    });

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    load()
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load instructors");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload when the target course/cohort changes
  }, [kind, slug]);

  const assignedIds = useMemo(() => new Set(assigned.map((item) => item.id)), [assigned]);
  const available = profiles.filter((item) => !assignedIds.has(item.id));

  function setDraftField<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function setBullet(index: number, value: string) {
    setDraft((current) => {
      const bullets = [...current.bullets];
      bullets[index] = value;
      return { ...current, bullets };
    });
  }

  async function persistAssignments(next: InstructorPublic[]) {
    setSaving(true);
    setError(null);
    try {
      const saved =
        kind === "course"
          ? await putAdminCourseInstructors(slug, next)
          : await putAdminCohortInstructors(slug, next);
      setAssigned(saved);
      setNotice("Instructors saved.");
      setProfiles(await listAdminInstructorProfiles());
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save instructors");
    } finally {
      setSaving(false);
    }
  }

  async function addExisting() {
    const profile = profiles.find((item) => item.id === pickId);
    if (!profile) return;
    const next: InstructorPublic = {
      id: profile.id,
      name: profile.name,
      title: profile.title,
      photo_url: profile.photo_url,
      bullets: profile.bullets,
      role_label: "Instructor",
      sort_order: assigned.length,
    };
    setPickId("");
    await persistAssignments([...assigned, next]);
  }

  async function createAndAssign() {
    if (!draft.name.trim()) {
      setError("Name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await createAdminInstructorProfile(writePayload(draft));
      const next: InstructorPublic = {
        id: created.id,
        name: created.name,
        title: created.title,
        photo_url: created.photo_url,
        bullets: created.bullets,
        role_label: draft.role_label.trim() || "Instructor",
        sort_order: assigned.length,
      };
      setDraft(EMPTY_DRAFT);
      const saved =
        kind === "course"
          ? await putAdminCourseInstructors(slug, [...assigned, next])
          : await putAdminCohortInstructors(slug, [...assigned, next]);
      setAssigned(saved);
      setProfiles(await listAdminInstructorProfiles());
      setNotice("Instructor added.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create instructor");
    } finally {
      setSaving(false);
    }
  }

  async function saveProfileEdits(id: string) {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateAdminInstructorProfile(id, writePayload(draft));
      setAssigned((current) =>
        current.map((item) =>
          item.id === id
            ? {
                ...item,
                name: updated.name,
                title: updated.title,
                photo_url: updated.photo_url,
                bullets: updated.bullets,
              }
            : item
        )
      );
      setProfiles(await listAdminInstructorProfiles());
      setEditingId(null);
      setDraft(EMPTY_DRAFT);
      setNotice("Profile updated.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update instructor");
    } finally {
      setSaving(false);
    }
  }

  async function removeAssigned(id: string) {
    await persistAssignments(assigned.filter((item) => item.id !== id));
  }

  async function removeProfile(id: string) {
    if (!window.confirm("Remove this instructor profile? They will also be unassigned from courses.")) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await deleteAdminInstructorProfile(id);
      setAssigned((current) => current.filter((item) => item.id !== id));
      setProfiles(await listAdminInstructorProfiles());
      setNotice("Instructor profile deleted.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not delete instructor");
    } finally {
      setSaving(false);
    }
  }

  function move(index: number, direction: -1 | 1) {
    const next = [...assigned];
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    const [row] = next.splice(index, 1);
    next.splice(target, 0, row);
    void persistAssignments(next);
  }

  function updateRole(id: string, role_label: string) {
    setAssigned((current) => current.map((item) => (item.id === id ? { ...item, role_label } : item)));
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading instructors…
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        breadcrumbs={[
          { label: "Courses", href: "/admin/courses" },
          { label: title },
        ]}
        title={`Instructors · ${title}`}
        description="Add one or more instructors. Leave this empty and the public page will hide Who teaches."
      />

      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      {notice ? <p className="mb-4 text-sm text-muted-foreground">{notice}</p> : null}

      <section className="space-y-4">
        <h2 className="font-heading text-lg font-semibold">Assigned to this {kind}</h2>
        {assigned.length === 0 ? (
          <EmptyState
            icon={<UserRound className="size-5" />}
            title="No instructors yet"
            description="Create a profile below or add someone who already exists."
          />
        ) : (
          <div className="space-y-3">
            {assigned.map((item, index) => (
              <div key={item.id} className="rounded-xl border p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-muted-foreground">{item.title || "No title yet"}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => move(index, -1)}
                      disabled={index === 0 || saving}
                      aria-label="Move up"
                    >
                      <ArrowUp className="size-4" />
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => move(index, 1)}
                      disabled={index === assigned.length - 1 || saving}
                      aria-label="Move down"
                    >
                      <ArrowDown className="size-4" />
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditingId(item.id);
                        setDraft({ ...toDraft(item), role_label: item.role_label });
                      }}
                    >
                      Edit profile
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => void removeAssigned(item.id)}
                      disabled={saving}
                    >
                      Unassign
                    </Button>
                  </div>
                </div>
                <div className="mt-3 max-w-sm">
                  <Label htmlFor={`role-${item.id}`}>Role on this {kind}</Label>
                  <Input
                    id={`role-${item.id}`}
                    value={item.role_label}
                    onChange={(event) => updateRole(item.id, event.target.value)}
                    onBlur={() => void persistAssignments(assigned)}
                  />
                </div>
                {editingId === item.id ? (
                  <div className="mt-4 rounded-lg bg-muted/40 p-4">
                    <ProfileFields draft={draft} setField={setDraftField} setBullet={setBullet} />
                    <div className="mt-3 flex gap-2">
                      <Button
                        type="button"
                        className="bg-brand-navy text-white hover:bg-brand-navy/90"
                        onClick={() => void saveProfileEdits(item.id)}
                        disabled={saving}
                      >
                        Save profile
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setEditingId(null);
                          setDraft(EMPTY_DRAFT);
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </section>

      {available.length > 0 ? (
        <section className="mt-10 space-y-3">
          <h2 className="font-heading text-lg font-semibold">Add existing instructor</h2>
          <div className="flex flex-wrap gap-2">
            <select
              className="h-10 min-w-56 rounded-lg border bg-background px-3 text-sm"
              value={pickId}
              onChange={(event) => setPickId(event.target.value)}
            >
              <option value="">Select a profile</option>
              {available.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <Button type="button" onClick={() => void addExisting()} disabled={!pickId || saving}>
              <Plus className="size-4" />
              Add
            </Button>
          </div>
        </section>
      ) : null}

      {editingId ? null : (
      <section className="mt-10 max-w-xl space-y-4">
        <h2 className="font-heading text-lg font-semibold">Create instructor</h2>
        <ProfileFields draft={draft} setField={setDraftField} setBullet={setBullet} />
        <div>
          <Label htmlFor="new-role">Role on this {kind}</Label>
          <Input
            id="new-role"
            value={draft.role_label}
            onChange={(event) => setDraftField("role_label", event.target.value)}
            placeholder="Lead instructor"
          />
        </div>
        <Button
          type="button"
          className="bg-brand-orange text-white hover:bg-brand-orange/90"
          onClick={() => void createAndAssign()}
          disabled={saving}
        >
          {saving ? "Saving…" : "Create and assign"}
        </Button>
      </section>
      )}

      {profiles.length > 0 ? (
        <section className="mt-12">
          <h2 className="font-heading text-lg font-semibold">All instructor profiles</h2>
          <ul className="mt-4 divide-y rounded-xl border">
            {profiles.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-3 px-4 py-3">
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.course_count} course{item.course_count === 1 ? "" : "s"} · {item.cohort_count}{" "}
                    cohort{item.cohort_count === 1 ? "" : "s"}
                  </p>
                </div>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="text-destructive"
                  onClick={() => void removeProfile(item.id)}
                  disabled={saving}
                >
                  <Trash2 className="size-4" />
                  Delete
                </Button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function ProfileFields({
  draft,
  setField,
  setBullet,
}: {
  draft: Draft;
  setField: <K extends keyof Draft>(key: K, value: Draft[K]) => void;
  setBullet: (index: number, value: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <Label htmlFor="instructor-name">Name</Label>
        <Input
          id="instructor-name"
          value={draft.name}
          onChange={(event) => setField("name", event.target.value)}
          placeholder="Ada Okafor"
        />
      </div>
      <div>
        <Label htmlFor="instructor-title">Title</Label>
        <Input
          id="instructor-title"
          value={draft.title}
          onChange={(event) => setField("title", event.target.value)}
          placeholder="Onchain analyst"
        />
      </div>
      <div>
        <Label htmlFor="instructor-photo">Photo URL</Label>
        <Input
          id="instructor-photo"
          value={draft.photo_url}
          onChange={(event) => setField("photo_url", event.target.value)}
          placeholder="/instructors/ada.jpg or https://…"
        />
        <p className="mt-1 text-xs text-muted-foreground">
          Use a file in /public (path starting with /) or a full https image URL.
        </p>
      </div>
      <div className="space-y-2">
        <Label>Fact bullets (up to 5)</Label>
        {draft.bullets.map((bullet, index) => (
          <Input
            key={index}
            value={bullet}
            onChange={(event) => setBullet(index, event.target.value)}
            placeholder={`Bullet ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
