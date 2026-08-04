import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata = { title: "Analytics" };

export default function AdminAnalyticsPage() {
  return (
    <div>
      <PageHeader
        title="Analytics"
        description="Platform metrics and learning insights"
      />
      <div className="grid gap-6 lg:grid-cols-2">
        {[
          { title: "Course Completion Rate", value: "72%", detail: "Across all active courses" },
          { title: "Average Watch Time", value: "18 min", detail: "Per lesson session" },
          { title: "Quiz Pass Rate", value: "84%", detail: "First attempt average" },
          { title: "Monthly Active Learners", value: "1,240", detail: "+15% from last month" },
        ].map((metric) => (
          <Card key={metric.title} className="shadow-card">
            <CardHeader>
              <CardTitle className="text-base text-muted-foreground">{metric.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-heading text-3xl font-bold">{metric.value}</p>
              <p className="mt-1 text-sm text-muted-foreground">{metric.detail}</p>
              <div className="mt-4 h-24 rounded-lg bg-brand-surface flex items-center justify-center text-xs text-muted-foreground">
                Chart (connects with PostHog in Phase 2)
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
