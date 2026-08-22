import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Clock, Layers } from "lucide-react";
import { CatalogOfferBadges } from "@/components/course/catalog-offer-badges";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { catalogBrowseCta, catalogFooterPriceLabel } from "@/lib/catalog-price";
import type { SelfPacedCourseCard as SelfPacedCourseCardType } from "@/lib/api";

export function SelfPacedCatalogCard({
  course,
  comingSoon = false,
}: {
  course: SelfPacedCourseCardType;
  comingSoon?: boolean;
}) {
  const href = `/courses/${course.slug}`;
  const thumb = course.thumbnail || "/dune-analytics-practical-sql-dashboard-techniques.png";
  const offer = {
    price: course.price,
    currency: course.currency,
    is_free: course.is_free,
    comingSoon,
  };
  const priceLabel = catalogFooterPriceLabel(offer);
  const cta = catalogBrowseCta(offer);

  return (
    <Card className="overflow-hidden rounded-2xl shadow-card transition-all duration-300 hover:-translate-y-1.5 hover:shadow-float">
      <div className="relative aspect-video overflow-hidden bg-brand-surface">
        <Image
          src={thumb}
          alt={course.title}
          fill
          className="object-cover"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
        />
        <CatalogOfferBadges
          price={course.price}
          currency={course.currency}
          is_free={course.is_free}
          comingSoon={comingSoon}
        />
      </div>
      <CardHeader>
        <CardTitle className="line-clamp-2 text-xl leading-snug">
          <Link href={href}>{course.title}</Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="line-clamp-3 text-base text-muted-foreground">{course.description}</p>
        <div className="flex flex-wrap gap-x-2 gap-y-1 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Layers className="size-3.5" />
            {course.lessons_count} lessons
          </span>
          <span aria-hidden>·</span>
          <span className="inline-flex items-center gap-1">
            <Clock className="size-3.5" />
            {course.duration || `~${course.estimated_minutes} minutes`}
          </span>
        </div>
        <p className="text-sm font-medium text-brand-navy dark:text-brand-orange">{course.difficulty}</p>
      </CardContent>
      <CardFooter className="justify-between gap-3 border-t">
        <span className="font-heading text-lg font-bold text-brand-navy dark:text-brand-orange">
          {priceLabel}
        </span>
        <ButtonLink
          href={href}
          size="sm"
          className="shrink-0 bg-brand-orange text-white hover:bg-brand-orange/90"
        >
          {cta}
          <ArrowRight className="ml-1 size-3.5" />
        </ButtonLink>
      </CardFooter>
    </Card>
  );
}
