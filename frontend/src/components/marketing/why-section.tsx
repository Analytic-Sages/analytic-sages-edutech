import Image from "next/image";
import { SectionBackground } from "@/components/marketing/section-background";

const highlights = [
  "Build dashboards",
  "Analyze blockchain protocols",
  "Publish research",
  "Contribute to open-source projects",
  "Participate and win hackathons",
  "Join internships",
  "Become part of a growing global blockchain data community",
];

export function WhySection() {
  return (
    <section className="relative overflow-hidden border-y bg-background py-28 sm:py-32">
      <SectionBackground variant="diamonds" />
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="grid gap-14 lg:grid-cols-12 lg:items-center lg:gap-16">
          {/* Student building a real dashboard: proof of "learn by doing" */}
          <div className="relative order-last mx-auto w-full max-w-md lg:order-first lg:col-span-5 lg:max-w-none xl:-ml-4">
            <div
              aria-hidden
              className="absolute -top-5 -left-5 h-2/3 w-2/3 rounded-[28px] bg-brand-navy/10 dark:bg-brand-orange/10"
            />
            <div className="group relative aspect-[3/4] overflow-hidden rounded-[24px] shadow-elevated">
              <Image
                src="/1.png"
                alt="Analytic Sages student building an onchain analytics dashboard during a workshop"
                fill
                className="object-cover object-center transition-transform duration-500 ease-out group-hover:scale-[1.015]"
                sizes="(max-width: 1024px) 100vw, 40vw"
              />
            </div>
          </div>

          <div className="lg:col-span-7">
            <p className="text-base font-semibold uppercase tracking-wide text-brand-orange sm:text-lg">
              Why Analytic Sages
            </p>
            <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem]">
              More than an online school
            </h2>
            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground">
              Most online courses end after the last video. Ours is where your career begins.
            </p>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground">
              Our students don&apos;t just consume content. They:
            </p>
            <ul className="mt-10 grid gap-4 sm:grid-cols-2">
              {highlights.map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-3 rounded-2xl border bg-card p-5 text-left shadow-card"
                >
                  <span className="mt-2 size-2 shrink-0 rounded-full bg-brand-orange" />
                  <span className="text-base text-foreground">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
