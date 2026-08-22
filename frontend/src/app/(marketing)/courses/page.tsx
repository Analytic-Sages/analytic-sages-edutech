import { Suspense } from "react";
import { CatalogPageContent } from "@/components/marketing/catalog-page-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Self-Paced Courses",
  description:
    "Free courses to get started. Paid courses for deeper, structured learning. Every card shows FREE, the price, or Coming soon.",
  path: "/courses",
  image: "/dune-analytics-practical-sql-dashboard-techniques.png",
});

export default function CoursesPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-muted-foreground">Loading courses…</div>}>
      <CatalogPageContent />
    </Suspense>
  );
}
