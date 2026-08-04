import { PageHeader } from "@/components/layout/page-header";
import { StatsCard } from "@/components/shared/stats-card";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata = { title: "Admin Dashboard" };

export default function AdminDashboardPage() {
  return (
    <div>
      <PageHeader
        title="Admin Dashboard"
        description="Platform overview and key metrics"
        action={
          <ButtonLink
            href="/admin/courses/new"
            className="bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            Create Course
          </ButtonLink>
        }
      />
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="Total Students" value="4,880" icon="users" trend="+12%" description="vs last month" />
        <StatsCard title="Active Courses" value={4} icon="courses" />
        <StatsCard title="Revenue (MTD)" value="₦2.4M" icon="payments" trend="+8%" />
        <StatsCard title="Completion Rate" value="72%" icon="trending" trend="+3%" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Recent Enrollments</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { name: "Ada Okonkwo", course: "Python for Blockchain Analytics", time: "2 hours ago" },
              { name: "James Adeyemi", course: "Quantitative Trading with Python", time: "5 hours ago" },
              { name: "Fatima Bello", course: "Blockchain Data Engineering", time: "1 day ago" },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-muted-foreground">{item.course}</p>
                </div>
                <span className="text-xs text-muted-foreground">{item.time}</span>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2">
            <ButtonLink href="/admin/courses" variant="outline" className="justify-start">
              Manage Courses
            </ButtonLink>
            <ButtonLink href="/admin/users" variant="outline" className="justify-start">
              View Students
            </ButtonLink>
            <ButtonLink href="/admin/payments" variant="outline" className="justify-start">
              Payment History
            </ButtonLink>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
