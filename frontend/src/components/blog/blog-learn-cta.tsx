import { ButtonLink } from "@/components/ui/button-link";
import { FEATURED_FREE_COURSE_SLUG } from "@/lib/self-paced";

export function BlogLearnCta() {
  return (
    <aside className="rounded-2xl border bg-card p-6 shadow-card sm:p-8">
      <p className="text-xs font-semibold tracking-wide text-brand-orange uppercase">Keep learning</p>
      <h2 className="mt-2 font-heading text-xl font-bold">Want more like this?</h2>
      <p className="mt-2 max-w-xl text-sm text-muted-foreground">
        Start the free Dune Analytics course, or see live instructor-led training.
      </p>
      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <ButtonLink
          href={`/courses/${FEATURED_FREE_COURSE_SLUG}`}
          className="bg-brand-orange text-white hover:bg-brand-orange/90"
        >
          Start the free course
        </ButtonLink>
        <ButtonLink href="/instructor-led" variant="outline">
          See instructor-led training
        </ButtonLink>
      </div>
    </aside>
  );
}
