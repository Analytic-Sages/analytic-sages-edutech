import { ComingSoonPanel } from "@/components/admin/coming-soon-panel";
import { PageHeader } from "@/components/layout/page-header";

export const metadata = { title: "Create Course" };

export default function CreateCoursePage() {
  return (
    <div>
      <PageHeader
        breadcrumbs={[
          { label: "Admin", href: "/admin" },
          { label: "Courses", href: "/admin/courses" },
          { label: "New Course" },
        ]}
        title="Create Course"
        description="Course creation is not live yet."
      />
      <ComingSoonPanel
        title="Coming soon"
        description="New courses cannot be created here yet. This form is disabled so it cannot be mistaken for a working publisher."
      />
    </div>
  );
}
