import { ComingSoonPanel } from "@/components/admin/coming-soon-panel";
import { PageHeader } from "@/components/layout/page-header";

export const metadata = { title: "Courses" };

export default function AdminCoursesPage() {
  return (
    <div>
      <PageHeader title="Courses" description="Course authoring is not live yet." />
      <ComingSoonPanel
        title="Coming soon"
        description="Self-paced course publishing is not wired. Use Instructor-Led cohorts for go-live. This screen will not save or publish anything."
      />
    </div>
  );
}
