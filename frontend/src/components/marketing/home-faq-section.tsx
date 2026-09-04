"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { SectionBackground } from "@/components/marketing/section-background";
import { siteConfig } from "@/config/site";
import { marketingFaqs } from "@/lib/marketing-faqs";

export function HomeFaqSection() {
  return (
    <section className="relative overflow-hidden border-b bg-background py-24 sm:py-32">
      <SectionBackground variant="lines" />
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-lg font-bold uppercase tracking-[0.12em] text-brand-orange sm:text-xl">
            FAQ
          </p>
          <h1 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem]">
            We&apos;ve got answers!
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            Quick answers about Analytic Sages, our courses, payments, and learning experience.
          </p>
        </div>

        <div className="mx-auto mt-12 max-w-3xl rounded-2xl border bg-card px-4 py-2 shadow-card sm:px-6">
          <Accordion>
            {marketingFaqs.map((faq) => (
              <AccordionItem key={faq.question} value={faq.question}>
                <AccordionTrigger className="py-5 text-base font-semibold hover:no-underline sm:text-lg">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="pb-5 text-base leading-relaxed text-muted-foreground sm:text-[1.05rem]">
                  <p>{faq.answer}</p>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>

        <p className="mx-auto mt-8 max-w-2xl text-center text-sm text-muted-foreground">
          Still need help? Email{" "}
          <a
            href={`mailto:${siteConfig.emails.support}`}
            className="font-medium text-brand-orange hover:underline"
          >
            {siteConfig.emails.support}
          </a>{" "}
          or{" "}
          <a
            href={`mailto:${siteConfig.emails.admin}`}
            className="font-medium text-brand-orange hover:underline"
          >
            {siteConfig.emails.admin}
          </a>
          .
        </p>
      </div>
    </section>
  );
}
