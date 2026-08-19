import { HomeFaqSection } from "@/components/marketing/home-faq-section";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "FAQ",
  description:
    "Frequently asked questions about Analytic Sages courses, payments, enrollment, and learning.",
  path: "/faq",
});

export default function FaqPage() {
  return (
    <div className="pb-8">
      <HomeFaqSection />
    </div>
  );
}
