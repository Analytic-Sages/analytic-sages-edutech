import { LegalDocument } from "@/components/marketing/legal-document";
import { termsOfUse } from "@/lib/legal";

export const metadata = {
  title: termsOfUse.title,
  description: termsOfUse.description,
};

export default function TermsPage() {
  return <LegalDocument document={termsOfUse} />;
}
