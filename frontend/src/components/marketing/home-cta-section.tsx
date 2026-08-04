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
              Ready to start your journey?
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-base text-white/80 sm:text-lg">
              Join thousands of learners building careers in blockchain, data, and quantitative finance.
            </p>
            <ButtonLink
              href="/register"
              size="lg"
              className="group mt-10 h-14 bg-brand-orange px-10 text-base text-white shadow-elevated transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-float"
            >
              Get Started Today
              <ArrowRight className="ml-2 size-4 transition-transform group-hover:translate-x-1" />
            </ButtonLink>
          </div>
        </div>
      </div>
    </section>
  );
}
