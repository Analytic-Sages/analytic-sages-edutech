import { ProgrammeDetailContent } from "@/components/student/programme-detail-content";

export const metadata = { title: "Live Programme" };

export default async function ProgrammeDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return <ProgrammeDetailContent slug={slug} />;
}
