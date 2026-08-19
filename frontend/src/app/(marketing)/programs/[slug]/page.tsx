import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ProgramLandingPage } from "@/components/marketing/program-landing-page";
import {
  getProgramPage,
  listProgramPageSlugs,
} from "@/lib/program-pages";
import { pageMetadata } from "@/lib/seo";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return listProgramPageSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const program = getProgramPage(slug);
  if (!program) return { title: "Program" };

  return pageMetadata({
    title: program.seoTitle,
    description: program.seoDescription,
    path: program.canonicalPath,
    image: program.postcardImage,
  });
}

export default async function CohortProgramPage({ params }: Props) {
  const { slug } = await params;
  const program = getProgramPage(slug);
  if (!program) notFound();

  return <ProgramLandingPage program={program} />;
}
