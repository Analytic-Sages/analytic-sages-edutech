import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { BlockchainDataEngineeringCurriculum } from "@/components/marketing/blockchain-data-engineering-curriculum";
import { SqlBlockchainDataAnalyticsCurriculum } from "@/components/marketing/sql-blockchain-data-analytics-curriculum";
import { getEngineeringProgramPage, getProgramPage, listEngineeringProgramSlugs, listProgramPageSlugs } from "@/lib/program-pages";
import { pageMetadata } from "@/lib/seo";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return [...new Set([...listEngineeringProgramSlugs(), ...listProgramPageSlugs()])].map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const program = getEngineeringProgramPage(slug);
  if (program) {
    return pageMetadata({
      title: program.curriculum.seoTitle,
      description: program.curriculum.seoDescription,
      path: program.curriculumPath,
      image: program.postcardImage,
    });
  }
  const sqlProgram = getProgramPage(slug);
  if (!sqlProgram) return { title: "Curriculum" };
  return pageMetadata({
    title: `${sqlProgram.seoTitle} Curriculum`,
    description: sqlProgram.seoDescription,
    path: sqlProgram.curriculumPath,
    image: sqlProgram.postcardImage,
  });
}

export default async function ProgramCurriculumPage({ params }: Props) {
  const { slug } = await params;
  const program = getEngineeringProgramPage(slug);
  if (program) return <BlockchainDataEngineeringCurriculum program={program} />;
  const sqlProgram = getProgramPage(slug);
  if (!sqlProgram) notFound();
  return <SqlBlockchainDataAnalyticsCurriculum />;
}
