import { InstructorLedPageContent } from "@/components/marketing/instructor-led-page-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Instructor-Led Training",
  description:
    "Join Analytic Sages live expert-led cohorts with scheduled classroom sessions, projects, and mentorship.",
  path: "/instructor-led",
});

export default function InstructorLedPage() {
  return <InstructorLedPageContent />;
}
