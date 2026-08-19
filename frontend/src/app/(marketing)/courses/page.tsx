import { CatalogPageContent } from "@/components/marketing/catalog-page-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Self-Paced Courses",
  description:
    "Free and upcoming self-paced blockchain analytics courses from Analytic Sages, including Dune SQL and dashboard techniques.",
  path: "/courses",
  image: "/dune-analytics-practical-sql-dashboard-techniques.png",
});

export default function CoursesPage() {
  return <CatalogPageContent />;
}
