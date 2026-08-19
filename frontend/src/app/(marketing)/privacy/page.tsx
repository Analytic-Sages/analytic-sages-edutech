import { LegalDocument } from "@/components/marketing/legal-document";
import { privacyPolicy } from "@/lib/legal";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: privacyPolicy.title,
  description: privacyPolicy.description,
  path: "/privacy",
});

export default function PrivacyPage() {
  return <LegalDocument document={privacyPolicy} />;
}
