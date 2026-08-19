import { MarketingFooter } from "@/components/layout/marketing-footer";
import { MarketingHeader } from "@/components/layout/marketing-header";
import { ButtonLink } from "@/components/ui/button-link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col">
      <MarketingHeader />
      <main className="flex flex-1 items-center justify-center px-4 py-20 sm:px-6">
        <div className="mx-auto max-w-lg text-center">
          <p className="text-sm font-semibold tracking-wide text-brand-orange uppercase">
            404
          </p>
          <h1 className="mt-3 font-heading text-3xl font-bold tracking-tight text-brand-navy sm:text-4xl dark:text-white">
            This page is not here
          </h1>
          <p className="mt-4 text-muted-foreground">
            The link may be outdated, or the page may have moved. Head back to a live
            Analytic Sages page and continue from there.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <ButtonLink
              href="/"
              className="h-11 px-6 bg-brand-navy text-white hover:bg-brand-navy/90"
            >
              Go to homepage
            </ButtonLink>
            <ButtonLink
              href="/programs"
              variant="outline"
              className="h-11 px-6"
            >
              Our Programs
            </ButtonLink>
            <ButtonLink href="/courses" variant="outline" className="h-11 px-6">
              Self-paced courses
            </ButtonLink>
          </div>
        </div>
      </main>
      <MarketingFooter />
    </div>
  );
}
