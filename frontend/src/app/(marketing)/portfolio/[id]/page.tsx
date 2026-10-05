import { PublicPortfolioContent } from "@/components/marketing/public-portfolio-content";

export const metadata = { title: "Student Portfolio" };

export default async function PublicPortfolioPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <PublicPortfolioContent userId={id} />;
}
