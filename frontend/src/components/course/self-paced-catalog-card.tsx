import Image from "next/image";
import Link from "next/link";
import { Clock, Layers } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import type { SelfPacedCourseCard as SelfPacedCourseCardType } from "@/lib/api";

export function SelfPacedCatalogCard({ course }: { course: SelfPacedCourseCardType }) {
  const href = `/courses/${course.slug}`;
  const thumb = course.thumbnail || "/dune-analytics-practical-sql-dashboard-techniques.png";

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
        <Badge className="absolute top-3 left-3 bg-brand-orange text-white">FREE</Badge>
      </div>
      <CardHeader>
        <CardTitle className="line-clamp-2 text-xl leading-snug">
          <Link href={href}>{course.title}</Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="line-clamp-3 text-base text-muted-foreground">{course.description}</p>
        <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Layers className="size-3.5" />
            {course.lessons_count} lessons
          </span>
          <span className="inline-flex items-center gap-1">
            <Clock className="size-3.5" />
            {course.duration || `~${course.estimated_minutes} minutes`}
          </span>
        </div>
        <p className="text-sm font-medium text-brand-navy dark:text-brand-orange">{course.difficulty}</p>
      </CardContent>
      <CardFooter className="justify-between border-t">
        <span className="font-heading text-lg font-bold text-brand-navy dark:text-brand-orange">Free</span>
        <ButtonLink href={href} size="sm" className="bg-brand-orange text-white hover:bg-brand-orange/90">
          View Course
        </ButtonLink>
      </CardFooter>
    </Card>
  );
}
