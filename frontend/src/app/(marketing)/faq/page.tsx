import { HomeFaqSection } from "@/components/marketing/home-faq-section";
import { JsonLd } from "@/components/seo/json-ld";
import { marketingFaqs } from "@/lib/marketing-faqs";
import { breadcrumbJsonLd, faqPageJsonLd, pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "FAQ",
  description:
    "Frequently asked questions about Analytic Sages - a global platform for blockchain analytics, data engineering, AI education, payments, and enrollment.",
  path: "/faq",
});

export default function FaqPage() {
  return (
    <div className="pb-8">
      <JsonLd data={faqPageJsonLd(marketingFaqs)} />
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "FAQ", path: "/faq" },
        ])}
      />
      <HomeFaqSection />
    </div>
  );
}
