import { Suspense } from "react";
import { CatalogPageContent } from "@/components/marketing/catalog-page-content";
import { CoursePlacementSection } from "@/components/marketing/course-placement-section";
import { JsonLd } from "@/components/seo/json-ld";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Self-Paced Courses",
  description:
    "Global self-paced learning from Analytic Sages. Free courses to get started; paid courses for deeper, structured learning. Every card shows FREE, the price, or Coming soon.",
  path: "/courses",
  image: "/dune-analytics-practical-sql-dashboard-techniques.png",
});

export default function CoursesPage() {
  return (
    <>
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "Self-Paced Courses", path: "/courses" },
        ])}
      />
      <CoursePlacementSection pageKey="courses" title="Featured Courses" description="Courses selected by the Analytic Sages team." />
      <Suspense fallback={<div className="p-12 text-center text-muted-foreground">Loading courses…</div>}>
        <CatalogPageContent />
      </Suspense>
    </>
  );
}
