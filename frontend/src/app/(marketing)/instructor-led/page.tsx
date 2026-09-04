import { InstructorLedPageContent } from "@/components/marketing/instructor-led-page-content";
import { JsonLd } from "@/components/seo/json-ld";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Instructor-Led Training",
  description:
    "Join Analytic Sages live expert-led cohorts worldwide - scheduled classroom sessions, projects, and mentorship in blockchain data and related tech skills.",
  path: "/instructor-led",
});

export default function InstructorLedPage() {
  return (
    <>
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "Instructor-Led Training", path: "/instructor-led" },
        ])}
      />
      <InstructorLedPageContent />
    </>
  );
}
