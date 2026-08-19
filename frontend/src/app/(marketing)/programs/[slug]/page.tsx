import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ProgramLandingPage } from "@/components/marketing/program-landing-page";
import {
  getProgramPage,
  listProgramPageSlugs,
  PUBLIC_SITE_ORIGIN,
} from "@/lib/program-pages";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return listProgramPageSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const program = getProgramPage(slug);
  if (!program) return { title: "Program" };

  const url = `${PUBLIC_SITE_ORIGIN}${program.canonicalPath}`;
  return {
    title: program.seoTitle,
    description: program.seoDescription,
    alternates: { canonical: url },
    openGraph: {
      title: `${program.seoTitle} | Analytic Sages`,
      description: program.seoDescription,
      url,
      siteName: "Analytic Sages",
      type: "website",
    },
  };
}

export default async function CohortProgramPage({ params }: Props) {
  const { slug } = await params;
  const program = getProgramPage(slug);
  if (!program) notFound();

  return <ProgramLandingPage program={program} />;
}
