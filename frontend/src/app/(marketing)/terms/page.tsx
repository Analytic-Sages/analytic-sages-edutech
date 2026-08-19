import { LegalDocument } from "@/components/marketing/legal-document";
import { termsOfUse } from "@/lib/legal";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: termsOfUse.title,
  description: termsOfUse.description,
  path: "/terms",
});

export default function TermsPage() {
  return <LegalDocument document={termsOfUse} />;
}
