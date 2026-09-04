import { AboutPageContent } from "@/components/marketing/about-page-content";
import { JsonLd } from "@/components/seo/json-ld";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "About",
  description:
    "Analytic Sages is a global technology education platform helping people worldwide build practical skills in blockchain analytics, data engineering, AI, and quantitative finance.",
  path: "/about",
});

export default function AboutPage() {
  return (
    <>
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "About", path: "/about" },
        ])}
      />
      <AboutPageContent />
    </>
  );
}
