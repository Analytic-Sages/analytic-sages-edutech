import { PartnersLeaderboardContent } from "@/components/referrals/partners-leaderboard-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Partner Leaderboard",
  description: "Analytic Sages Referral Partners ranked by successful paid enrollments.",
  path: "/partners/leaderboard",
});

export default function PartnersLeaderboardPage() {
  return <PartnersLeaderboardContent />;
}
