import { ReferralLanding } from "@/components/referrals/referral-landing";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Referral",
  description: "Analytic Sages Referral Partner link",
  path: "/ref",
});

export default function ReferralCodePage() {
  return <ReferralLanding />;
}
