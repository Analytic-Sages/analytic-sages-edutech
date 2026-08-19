"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { SectionBackground } from "@/components/marketing/section-background";
import { siteConfig } from "@/config/site";

const faqs = [
  {
    question: "What is Analytic Sages?",
    answer:
      "Analytic Sages is a technology education and learning community that helps people build practical skills in blockchain analytics, data engineering, AI, and quantitative finance through real tools, real projects, and a global community of learners.",
  },
  {
    question: "What courses does Analytic Sages offer?",
    answer:
      "We offer Instructor-Led live cohorts and a Self-Paced catalog. Live training is available through Instructor-Led. Self-paced courses are listed as Launching soon until the on-demand player is ready.",
  },
  {
    question: "How can I sign up for a course?",
    answer:
      "For Instructor-Led training, create an account, open Instructor-Led Training, and register for an open cohort (payment unlocks Classroom). Self-paced checkout will open when those courses launch.",
  },
  {
    question: "Are the courses suitable for beginners?",
    answer:
      "Yes. Beginner paths like SQL for Blockchain Analytics are designed for newcomers. Check each course page for difficulty and requirements. Instructor-Led cohorts include live guidance.",
  },
  {
    question: "What is the duration of the courses?",
    answer:
      "Self-paced paths typically range from about 4 to 12 weeks of content. Instructor-Led cohorts follow a live schedule with multiple sessions. Check the cohort or course page for details.",
  },
  {
    question: "What is the cost of the courses?",
    answer:
      "Right now two courses are open for enrollment: Beginner Blockchain Analytics (SQL) at $35 and Python for Blockchain Data Analytics at $150. Everything else in the catalog, including Tableau, is launching soon.",
  },  {
    question: "Do you offer any free courses?",
    answer:
      "Full paid courses are listed in the catalog. Free learning resources include our blog, YouTube tutorials, and community discussions on Discord and Telegram. More free and preview content may be added as the platform grows.",
  },
  {
    question: "Can I access the courses on mobile devices?",
    answer:
      "Yes. The Analytic Sages website is responsive, so you can browse courses, manage your account, and continue learning from a phone or tablet browser. For longer coding labs, a laptop is recommended.",
  },
  {
    question: "What payment methods are accepted?",
    answer:
      "Checkout supports cards and bank transfer via Paystack, and crypto via NOWPayments.",
  },
  {
    question: "Are there any prerequisites for the courses?",
    answer:
      "Prerequisites depend on the course. Beginner paths often require only basic computer literacy or introductory Python; intermediate and advanced paths may expect SQL, statistics, or prior blockchain concepts. Check the Requirements section on each course page.",
  },
  {
    question: "Can I download course materials?",
    answer:
      "Downloadable lesson resources (datasets, slides, and reference files) are part of the learning experience and will expand as more curriculum is published. Enrolled students access materials from within the course player.",
  },
  {
    question: "How can I track my progress in a course?",
    answer:
      "After you enroll, open Dashboard or My Courses to see your enrollments and continue learning. Lesson-level progress tracking is being expanded as the course player matures.",
  },
  {
    question: "Do you offer group discounts?",
    answer: `For teams, cohorts, or organizational training, contact us at ${siteConfig.emails.admin} and our team will discuss available options.`,
  },
  {
    question: "Can I retake a course if I don't pass the first time?",
    answer:
      "Once enrolled, you keep access to your course content so you can revisit lessons and practice. Formal assessments and certificate retake policies will be published as those features go live.",
  },
];

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
            {faqs.map((faq) => (
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
