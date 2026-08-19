import { PatternBackground } from "@/components/marketing/pattern-background";
import { TestimonialPlayer } from "@/components/marketing/testimonial-player";
import { homeTestimonials } from "@/lib/testimonials";

export function HomeTestimonialsSection() {
  const [featured, ...rest] = homeTestimonials;

  return (
    <section className="relative overflow-hidden border-y bg-background py-24 sm:py-32">
      <PatternBackground />
      <div className="relative mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-lg font-bold uppercase tracking-[0.12em] text-brand-orange sm:text-xl">
            Testimonials
          </p>
          <h2 className="mt-4 font-heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem]">
            Hear from our learners
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-muted-foreground">
            Real stories from people building blockchain analytics skills with Analytic Sages.
          </p>
        </div>

        <div className="mt-14 grid gap-10 lg:grid-cols-2 lg:gap-12">
          {featured && <TestimonialPlayer item={featured} featured />}
          {rest.map((item) => (
            <TestimonialPlayer key={item.id} item={item} />
          ))}
        </div>
      </div>
    </section>
  );
}
