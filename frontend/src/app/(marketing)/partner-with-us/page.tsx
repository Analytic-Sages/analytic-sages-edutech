import { PartnerWithUsPageContent } from "@/components/marketing/partner-with-us-page-content";
import { JsonLd } from "@/components/seo/json-ld";
import { partnerFaqs } from "@/lib/partner-with-us";
import { breadcrumbJsonLd, faqPageJsonLd, pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Partner With Analytic Sages | Blockchain Ecosystem Talent & Intelligence",
  description:
    "Partner with Analytic Sages to develop blockchain talent, understand ecosystem data and turn technical learning into real ecosystem contribution.",
  path: "/partner-with-us",
  absoluteTitle: true,
});

export default function PartnerWithUsPage() {
  return (
    <>
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "Partner With Us", path: "/partner-with-us" },
        ])}
      />
      <JsonLd data={faqPageJsonLd(partnerFaqs)} />
      <PartnerWithUsPageContent />
    </>
  );
}
