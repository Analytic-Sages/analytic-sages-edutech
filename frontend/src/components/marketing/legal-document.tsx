import Link from "next/link";
import { PageHeader } from "@/components/layout/page-header";
import { siteConfig } from "@/config/site";
import type { LegalBlock, LegalDocumentContent } from "@/lib/legal";

function Block({ block }: { block: LegalBlock }) {
  if (block.type === "h3") {
    return <h3 className="mt-6 font-heading text-lg font-semibold text-foreground">{block.text}</h3>;
  }
  if (block.type === "ul") {
    return (
      <ul className="my-3 list-disc space-y-1.5 pl-5 text-base leading-relaxed text-muted-foreground">
        {block.items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    );
  }
  return <p className="mt-3 text-base leading-relaxed text-muted-foreground">{block.text}</p>;
}

export function LegalDocument({ document }: { document: LegalDocumentContent }) {
  const other = document.slug === "/privacy" ? { href: "/terms", label: "Terms of Use" } : { href: "/privacy", label: "Privacy Policy" };

  return (
    <article className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        breadcrumbs={[{ label: document.title }]}
        title={document.title}
        description={document.description}
      />
      <p className="mb-8 text-sm text-muted-foreground">Last updated: {document.updated}</p>

      {document.intro.map((paragraph) => (
        <p key={paragraph.slice(0, 48)} className="mt-4 text-base leading-relaxed text-muted-foreground">
          {paragraph}
        </p>
      ))}

      {document.sections.map((section) => (
        <section key={section.heading} className="mt-10">
          <h2 className="font-heading text-xl font-bold tracking-tight sm:text-2xl">{section.heading}</h2>
          {section.blocks.map((block, index) => (
            <Block key={`${section.heading}-${index}`} block={block} />
          ))}
        </section>
      ))}

      <div className="mt-12 space-y-2 border-t pt-8 text-sm text-muted-foreground">
        <p className="font-medium text-foreground">{siteConfig.name}</p>
        <p>
          Website:{" "}
          <a href="https://analyticsages.io" className="text-brand-orange hover:underline">
            analyticsages.io
          </a>
        </p>
        <p>
          Email:{" "}
          <a href={`mailto:${siteConfig.emails.support}`} className="text-brand-orange hover:underline">
            {siteConfig.emails.support}
          </a>
        </p>
        <p>
          Also:{" "}
          <a href={`mailto:${siteConfig.emails.admin}`} className="text-brand-orange hover:underline">
            {siteConfig.emails.admin}
          </a>
        </p>
        <p className="pt-4">
          See also our{" "}
          <Link href={other.href} className="font-medium text-brand-orange hover:underline">
            {other.label}
          </Link>
          .
        </p>
      </div>
    </article>
  );
}
