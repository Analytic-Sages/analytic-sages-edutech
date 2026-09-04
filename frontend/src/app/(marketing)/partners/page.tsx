import { RequirePartnersAccess } from "@/components/auth/require-partners-access";
import { PartnersPageContent } from "@/components/referrals/partners-page-content";
import { isPartnersPublic } from "@/lib/feature-flags";
import { pageMetadata } from "@/lib/seo";

export const metadata = isPartnersPublic()
  ? pageMetadata({
      title: "Referral Partners",
      description:
        "Earn 7% commission referring learners to Analytic Sages paid courses and programmes.",
      path: "/partners",
    })
  : { robots: { index: false, follow: false }, title: "Referral Partners" };

export default function PartnersPage() {
  return (
    <RequirePartnersAccess>
      <PartnersPageContent />
    </RequirePartnersAccess>
  );
}
