import { LegalDocument } from "@/components/marketing/legal-document";
import { privacyPolicy } from "@/lib/legal";

export const metadata = {
  title: privacyPolicy.title,
  description: privacyPolicy.description,
};

export default function PrivacyPage() {
  return <LegalDocument document={privacyPolicy} />;
}
