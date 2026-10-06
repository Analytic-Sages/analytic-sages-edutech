import { WaitlistContent } from "@/components/marketing/waitlist-content";

export const metadata = { title: "Join the waitlist" };

export default async function WaitlistPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return <WaitlistContent slug={slug} />;
}