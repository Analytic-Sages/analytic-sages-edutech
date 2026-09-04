import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { BlockchainDataEngineeringLanding } from "@/components/marketing/blockchain-data-engineering-landing";
import { ProgramLandingPage } from "@/components/marketing/program-landing-page";
import { JsonLd } from "@/components/seo/json-ld";
import {
  getEngineeringProgramPage,
  getProgramPage,
  listProgramPageSlugs,
} from "@/lib/program-pages";
import {
  breadcrumbJsonLd,
  courseJsonLd,
  educationalProgramJsonLd,
  pageMetadata,
} from "@/lib/seo";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return listProgramPageSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const engineering = getEngineeringProgramPage(slug);
  if (engineering) {
    return pageMetadata({
      title: engineering.seoTitle,
      description: engineering.seoDescription,
      path: engineering.canonicalPath,
      image: engineering.postcardImage,
    });
  }

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
  const engineering = getEngineeringProgramPage(slug);
  if (engineering) {
    return (
      <>
        <JsonLd
          data={educationalProgramJsonLd({
            name: engineering.h1,
            description: engineering.seoDescription,
            path: engineering.canonicalPath,
            image: engineering.postcardImage,
            timeToComplete: "P10W",
            educationalProgramMode: engineering.learningMode,
          })}
        />
        <JsonLd
          data={courseJsonLd({
            name: engineering.h1,
            description: engineering.seoDescription,
            path: engineering.canonicalPath,
            image: engineering.postcardImage,
          })}
        />
        <JsonLd
          data={breadcrumbJsonLd([
            { name: "Home", path: "/" },
            { name: "Instructor-Led Training", path: "/instructor-led" },
            { name: engineering.h1, path: engineering.canonicalPath },
          ])}
        />
        <BlockchainDataEngineeringLanding program={engineering} />
      </>
    );
  }

  const program = getProgramPage(slug);
  if (!program) notFound();

  return (
    <>
      <JsonLd
        data={courseJsonLd({
          name: program.headline,
          description: program.seoDescription,
          path: program.canonicalPath,
          image: program.postcardImage,
        })}
      />
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "Instructor-Led Training", path: "/instructor-led" },
          { name: program.headline, path: program.canonicalPath },
        ])}
      />
      <ProgramLandingPage program={program} />
    </>
  );
}
