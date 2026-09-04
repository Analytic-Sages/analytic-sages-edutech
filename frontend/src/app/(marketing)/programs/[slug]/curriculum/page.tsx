import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { BlockchainDataEngineeringCurriculum } from "@/components/marketing/blockchain-data-engineering-curriculum";
import { getEngineeringProgramPage, listEngineeringProgramSlugs } from "@/lib/program-pages";
import { pageMetadata } from "@/lib/seo";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return listEngineeringProgramSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const program = getEngineeringProgramPage(slug);
  if (!program) return { title: "Curriculum" };
  return pageMetadata({
    title: program.curriculum.seoTitle,
    description: program.curriculum.seoDescription,
    path: program.curriculumPath,
    image: program.postcardImage,
  });
}

export default async function ProgramCurriculumPage({ params }: Props) {
  const { slug } = await params;
  const program = getEngineeringProgramPage(slug);
  if (!program) notFound();
  return <BlockchainDataEngineeringCurriculum program={program} />;
}
