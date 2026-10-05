"use client";

import { useEffect, useState } from "react";
import { Award, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, getMyCertificateEligibility, type CertificateEligibility } from "@/lib/api";

export function CertificatesContent() {
  const [items, setItems] = useState<CertificateEligibility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyCertificateEligibility()
      .then(setItems)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Failed to load certificates"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading certificates…
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Certificates"
        description="Certificate eligibility is tracked automatically from your live programme progress."
      />

      {error && <p className="mb-4 text-sm text-destructive">{error}</p>}

      {items.length === 0 ? (
        <EmptyState
          icon={<Award className="size-5" />}
          title="No live programmes yet"
          description="Enrol in a live cohort to start working toward a certificate."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((cert) => (
            <Card key={cert.cohort_id} className="shadow-card">
              <CardHeader className="flex flex-row items-center justify-between gap-2">
                <CardTitle className="font-heading text-lg">
                  {cert.programme_title || cert.cohort_name}
                </CardTitle>
                <Badge className={cert.eligible ? "bg-success/10 text-success" : "bg-muted text-muted-foreground"}>
                  {cert.eligible ? "Eligible" : "In progress"}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-muted-foreground">
                <p>Attendance: {cert.attendance_percent}%</p>
                <p>Assignments: {cert.assignments_submitted}/{cert.assignments_total}</p>
                <p>Projects completed: {cert.projects_completed}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
