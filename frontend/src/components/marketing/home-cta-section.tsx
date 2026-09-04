import { ArrowRight } from "lucide-react";
import { ButtonLink } from "@/components/ui/button-link";
import { SectionBackground } from "@/components/marketing/section-background";

export function HomeCtaSection() {
  return (
    <section className="relative py-28 sm:py-32">
      <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="relative overflow-hidden rounded-3xl bg-brand-navy px-8 py-20 sm:px-16 sm:py-24">
          <SectionBackground variant="glow" className="opacity-60" />
          <div className="relative mx-auto max-w-2xl text-center">
            <h2 className="font-heading text-4xl font-bold text-white sm:text-5xl">
              Your career in blockchain starts with one decision.
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-base text-white/90 sm:text-lg">
              The demand for blockchain engineers, analysts, and AI builders is growing.
              The question isn&apos;t whether opportunities exist. It&apos;s whether
              you&apos;ll be ready when they arrive.
            </p>
            <p className="mt-4 text-base font-medium text-white/90 sm:text-lg">
              Blockchain Data Engineering is open for registration. SQL Blockchain Data Analytics
              is coming soon — each is its own programme.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <ButtonLink
                href="/programs/blockchain-data-engineering"
                size="lg"
                className="group h-14 bg-brand-orange px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-float"
              >
                Explore Blockchain Data Engineering
                <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
              </ButtonLink>
              <ButtonLink
                href="/courses"
                size="lg"
                variant="outline"
                className="h-14 border-white/30 bg-transparent px-10 text-base text-white transition-all hover:-translate-y-0.5 hover:bg-white/10 hover:text-white"
              >
                Explore self-paced
              </ButtonLink>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
