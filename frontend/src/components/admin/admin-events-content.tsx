"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiError, getAdminEvents, type EventAdmin } from "@/lib/api";
import { eventLifecycleLabel, eventTypeLabel, formatEventWhen } from "@/lib/events";

export function AdminEventsContent() {
  const [rows, setRows] = useState<EventAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAdminEvents()
      .then((data) => {
        if (!cancelled) setRows(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Could not load events.");
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
        Loading events…
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={<CalendarDays className="size-5" />}
        title="Couldn't load events"
        description={error}
        action={{ label: "Back to admin", href: "/admin" }}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Events"
        description="Create, publish, and cancel free public events. Join tracking records when a registered student clicks Join — not YouTube attendance."
        action={
          <ButtonLink href="/admin/events/new" className="bg-brand-orange text-white hover:bg-brand-orange/90">
            New event
          </ButtonLink>
        }
      />
      {rows.length === 0 ? (
        <EmptyState
          icon={<CalendarDays className="size-5" />}
          title="No events yet"
          description="Create a workshop or webinar, then publish it to /events."
          action={{ label: "New event", href: "/admin/events/new" }}
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Event</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>When</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Registrations</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>
                    <div className="font-medium">{row.title}</div>
                    <div className="text-xs text-muted-foreground">{row.slug}</div>
                  </TableCell>
                  <TableCell>{eventTypeLabel(row.event_type)}</TableCell>
                  <TableCell className="whitespace-nowrap text-sm">{formatEventWhen(row)}</TableCell>
                  <TableCell>
                    <Badge variant={row.published && !row.cancelled ? "default" : "outline"}>
                      {eventLifecycleLabel(row.lifecycle)}
                    </Badge>
                  </TableCell>
                  <TableCell>{row.registered_count}</TableCell>
                  <TableCell className="text-right">
                    <ButtonLink href={`/admin/events/${row.id}`} variant="ghost" size="sm">
                      Edit
                    </ButtonLink>
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
