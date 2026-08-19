import { AboutPageContent } from "@/components/marketing/about-page-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "About",
  description:
    "Analytic Sages is a technology education and learning community helping people build practical skills in blockchain analytics, data engineering, AI, and quantitative finance.",
  path: "/about",
});

export default function AboutPage() {
  return <AboutPageContent />;
}
