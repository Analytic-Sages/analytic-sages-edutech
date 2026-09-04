import { Suspense } from "react";
import { CatalogPageContent } from "@/components/marketing/catalog-page-content";
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
      <Suspense fallback={<div className="p-12 text-center text-muted-foreground">Loading courses…</div>}>
        <CatalogPageContent />
      </Suspense>
    </>
  );
}
