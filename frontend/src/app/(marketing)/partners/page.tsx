import { PartnersPageContent } from "@/components/referrals/partners-page-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Referral Partners",
  description:
    "Earn 7% commission referring learners to Analytic Sages paid courses and programmes.",
  path: "/partners",
});

export default function PartnersPage() {
  return <PartnersPageContent />;
}
