import { RequirePartnersAccess } from "@/components/auth/require-partners-access";
import { PartnersLeaderboardContent } from "@/components/referrals/partners-leaderboard-content";
import { isPartnersPublic } from "@/lib/feature-flags";
import { pageMetadata } from "@/lib/seo";

export const metadata = isPartnersPublic()
  ? pageMetadata({
      title: "Partner Leaderboard",
      description: "Analytic Sages Referral Partners ranked by successful paid enrollments.",
      path: "/partners/leaderboard",
    })
  : { robots: { index: false, follow: false }, title: "Partner Leaderboard" };

export default function PartnersLeaderboardPage() {
  return (
    <RequirePartnersAccess>
      <PartnersLeaderboardContent />
    </RequirePartnersAccess>
  );
}
