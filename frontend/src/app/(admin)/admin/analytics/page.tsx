import { ComingSoonPanel } from "@/components/admin/coming-soon-panel";
import { PageHeader } from "@/components/layout/page-header";

export const metadata = { title: "Analytics" };

export default function AdminAnalyticsPage() {
  return (
    <div>
      <PageHeader title="Analytics" description="Learning analytics are not connected." />
      <ComingSoonPanel
        title="Coming soon"
        description="Watch time, quiz pass rate, and completion charts are not tracked yet. Use the Cohort 9 monitor for signups and payments."
      />
    </div>
  );
}
