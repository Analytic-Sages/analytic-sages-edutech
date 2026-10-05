"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiError,
  createProject,
  getMyProjects,
  type ProjectPublic,
} from "@/lib/api";

export function StudentProjectsSection({ cohortId }: { cohortId: string }) {
  const [projects, setProjects] = useState<ProjectPublic[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("planned");
  const [github, setGithub] = useState("");
  const [live, setLive] = useState("");
  const [bip, setBip] = useState("");
  const [docs, setDocs] = useState("");
  const [tech, setTech] = useState("");

  useEffect(() => {
    getMyProjects(cohortId)
      .then(setProjects)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Failed to load projects"));
  }, [cohortId]);

  async function save() {
    if (!title.trim()) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const created = await createProject(cohortId, {
        title,
        description,
        status,
        github_url: github,
        live_url: live,
        build_in_public_url: bip,
        documentation_url: docs,
        technologies: tech.split(",").map((t) => t.trim()).filter(Boolean),
      });
      setProjects((prev) => [created, ...prev]);
      setTitle("");
      setDescription("");
      setGithub("");
      setLive("");
      setBip("");
      setDocs("");
      setTech("");
      setShowForm(false);
      setMessage("Project saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not save project");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="mb-8">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-heading text-lg font-semibold">Projects</h2>
        <Button size="sm" variant="outline" onClick={() => setShowForm((v) => !v)}>
          <Plus className="size-4" />
          Add project
        </Button>
      </div>

      {showForm && (
        <Card className="mb-4 shadow-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">New project</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="p-title">Title</Label>
                <Input id="p-title" value={title} onChange={(e) => setTitle(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="p-status">Status</Label>
                <select
                  id="p-status"
                  className="h-9 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <option value="planned">Planned</option>
                  <option value="in_progress">In progress</option>
                  <option value="submitted">Submitted</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-desc">Description</Label>
              <Textarea id="p-desc" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="p-gh">GitHub URL</Label>
                <Input id="p-gh" value={github} onChange={(e) => setGithub(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="p-live">Live URL</Label>
                <Input id="p-live" value={live} onChange={(e) => setLive(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="p-bip">Build in public URL</Label>
                <Input id="p-bip" value={bip} onChange={(e) => setBip(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="p-docs">Documentation URL</Label>
                <Input id="p-docs" value={docs} onChange={(e) => setDocs(e.target.value)} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-tech">Technologies (comma separated)</Label>
              <Input id="p-tech" value={tech} onChange={(e) => setTech(e.target.value)} placeholder="Python, SQL, dbt" />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            {message && <p className="text-sm text-success">{message}</p>}
            <Button size="sm" onClick={save} disabled={saving}>
              {saving ? "Saving…" : "Save project"}
            </Button>
          </CardContent>
        </Card>
      )}

      {projects.length === 0 && !showForm ? (
        <p className="text-sm text-muted-foreground">No projects yet.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {projects.map((project) => (
            <Card key={project.id} className="shadow-card">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-base">{project.title}</CardTitle>
                  <Badge className="capitalize">{project.status.replace("_", " ")}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {project.description && <p className="text-sm text-muted-foreground">{project.description}</p>}
                {project.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {project.technologies.map((t) => (
                      <Badge key={t} variant="outline">{t}</Badge>
                    ))}
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  {project.github_url && (
                    <a href={project.github_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
                      GitHub <ExternalLink className="size-3" />
                    </a>
                  )}
                  {project.live_url && (
                    <a href={project.live_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-brand-orange hover:underline">
                      Live <ExternalLink className="size-3" />
                    </a>
                  )}
                </div>
                {project.feedback && (
                  <p className="rounded-md bg-muted p-2 text-sm">{project.feedback}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
