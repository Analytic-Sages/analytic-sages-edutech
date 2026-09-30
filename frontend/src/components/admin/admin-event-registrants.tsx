"use client";

import { useEffect, useMemo, useState } from "react";
import { Download, Loader2, Users } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ButtonLink } from "@/components/ui/button-link";
import { ApiError, downloadAdminEventRegistrants, emailAdminEventRegistrants, getAdminEvent, getAdminEventRegistrants, type EventAdmin, type EventRegistrantAdmin } from "@/lib/api";

export function AdminEventRegistrants({ eventId }: { eventId: string }) {
  const [event, setEvent] = useState<EventAdmin | null>(null);
  const [registrants, setRegistrants] = useState<EventRegistrantAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [includeEventLink, setIncludeEventLink] = useState(true);
  const [sending, setSending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getAdminEvent(eventId), getAdminEventRegistrants(eventId)])
      .then(([eventData, rows]) => {
        setEvent(eventData);
        setRegistrants(rows);
      })
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Could not load registrants."))
      .finally(() => setLoading(false));
  }, [eventId]);

  async function download() {
    setDownloading(true);
    try {
      const blob = await downloadAdminEventRegistrants(eventId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${event?.slug || "event"}-registrants.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not download registrants.");
    } finally {
      setDownloading(false);
    }
  }

  const activeRegistrants = useMemo(() => registrants.filter((row) => row.status === "registered"), [registrants]);
  const allSelected = activeRegistrants.length > 0 && activeRegistrants.every((row) => selected.has(row.user_id));

  async function sendMessage(sendAll = false) {
    const ids = sendAll ? [] : activeRegistrants.filter((row) => selected.has(row.user_id)).map((row) => row.user_id);
    if (!subject.trim() || !message.trim() || (!sendAll && ids.length === 0)) return;
    setSending(true);
    setError(null);
    setNotice(null);
    try {
      const result = await emailAdminEventRegistrants(eventId, {
        recipient_user_ids: ids,
        subject: subject.trim(),
        message: message.trim(),
        include_event_link: includeEventLink,
      });
      setNotice(`Sent to ${result.sent} registrant${result.sent === 1 ? "" : "s"}${result.failed ? `; ${result.failed} failed` : ""}.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not send email.");
    } finally {
      setSending(false);
    }
  }

  if (loading) return <div className="flex min-h-[40vh] items-center justify-center gap-2 text-muted-foreground"><Loader2 className="size-5 animate-spin" />Loading registrants…</div>;
  if (error || !event) return <EmptyState icon={<Users className="size-5" />} title="Could not load registrants" description={error || "Event not found."} action={{ label: "Back to events", href: "/admin/events" }} />;

  return (
    <div>
      <PageHeader
        breadcrumbs={[{ label: "Events", href: "/admin/events" }, { label: event.title, href: `/admin/events/${event.id}` }, { label: "Registrants" }]}
        title="Event registrants"
        description="Use this list for event reminders and relevant follow-up emails."
        action={<div className="flex gap-2"><ButtonLink href={`/admin/events/${event.id}`} variant="outline">Edit event</ButtonLink><Button onClick={() => void download()} disabled={downloading}><Download className="size-4" />{downloading ? "Preparing…" : "Download CSV"}</Button></div>}
      />
      <div className="mb-4 text-sm text-muted-foreground">{registrants.filter((row) => row.status === "registered").length} active registrants · {registrants.length} total records</div>
      <section className="mb-8 rounded-xl border p-5">
        <h2 className="font-heading text-xl font-bold">Email registrants</h2>
        <p className="mt-1 text-sm text-muted-foreground">Choose selected attendees or send to every active registrant.</p>
        <div className="mt-4 grid gap-3">
          <Input value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Subject" aria-label="Email subject" />
          <Textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Write your message..." rows={5} aria-label="Email message" />
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={includeEventLink} onChange={(event) => setIncludeEventLink(event.target.checked)} /> Include event page link</label>
          <div className="flex flex-wrap gap-2"><Button variant="outline" disabled={sending || selected.size === 0} onClick={() => setSelected(new Set())}>Clear selection</Button><Button variant="outline" disabled={sending || !subject.trim() || !message.trim() || selected.size === 0} onClick={() => void sendMessage(false)}>{sending ? "Sending…" : `Send to selected (${selected.size})`}</Button><Button disabled={sending || !subject.trim() || !message.trim() || activeRegistrants.length === 0} onClick={() => void sendMessage(true)}>{sending ? "Sending…" : "Send to all active"}</Button></div>
          {notice ? <p className="text-sm text-success">{notice}</p> : null}
        </div>
      </section>
      {registrants.length === 0 ? <div className="rounded-xl border p-8 text-center text-sm text-muted-foreground">No registrations yet.</div> : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="min-w-full text-sm">
            <thead><tr className="border-b text-left"><th className="px-4 py-3"><input type="checkbox" checked={allSelected} onChange={(event) => setSelected(event.target.checked ? new Set(activeRegistrants.map((row) => row.user_id)) : new Set())} aria-label="Select all active registrants" /></th><th className="px-4 py-3">Name</th><th className="px-4 py-3">Email</th><th className="px-4 py-3">Phone</th><th className="px-4 py-3">Country</th><th className="px-4 py-3">Registered</th><th className="px-4 py-3">Status</th></tr></thead>
            <tbody>{registrants.map((row) => <tr key={row.id} className="border-b last:border-0"><td className="px-4 py-3"><input type="checkbox" checked={selected.has(row.user_id)} disabled={row.status !== "registered"} onChange={(event) => setSelected((current) => { const next = new Set(current); if (event.target.checked) next.add(row.user_id); else next.delete(row.user_id); return next; })} aria-label={`Select ${row.email}`} /></td><td className="px-4 py-3">{row.full_name || "-"}</td><td className="px-4 py-3">{row.email}</td><td className="px-4 py-3">{row.phone_number || "-"}</td><td className="px-4 py-3">{row.country_of_residence || "-"}</td><td className="px-4 py-3 text-muted-foreground">{new Date(row.registered_at).toLocaleDateString()}</td><td className="px-4 py-3 capitalize">{row.status}</td></tr>)}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}
