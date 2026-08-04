import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Clock, Star, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { formatPrice } from "@/lib/mock-data";
import type { Course } from "@/types/course";
import { cn } from "@/lib/utils";

type CourseCardProps = {
  course: Course;
  variant?: "catalog" | "enrolled";
  className?: string;
};

const difficultyColors = {
  Beginner: "bg-success/10 text-success",
  Intermediate: "bg-warning/10 text-warning",
  Advanced: "bg-destructive/10 text-destructive",
};

export function CourseCard({ course, variant = "catalog", className }: CourseCardProps) {
  const href =
    variant === "enrolled"
      ? `/courses/${course.slug}/learn/l1`
      : `/courses/${course.slug}`;

  const toolTags = course.skills.slice(0, 3);

  return (
    <Card
      className={cn(
        "group overflow-hidden rounded-2xl shadow-card transition-all duration-300 hover:-translate-y-1.5 hover:shadow-float",
        className
      )}
    >
      <div className="relative aspect-video overflow-hidden bg-brand-surface">
        <Image
          src={course.thumbnail}
          alt={course.title}
          fill
          className="object-cover transition-transform duration-500 group-hover:scale-105"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent opacity-60 transition-opacity duration-300 group-hover:opacity-40" />

        {/* Hover reveal overlay */}
        <div className="absolute inset-0 flex flex-col justify-end bg-brand-navy/80 p-5 opacity-0 backdrop-blur-[2px] transition-all duration-300 group-hover:opacity-100">
          <p className="line-clamp-3 text-sm leading-relaxed text-white/90">
            {course.description}
          </p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {toolTags.map((tool) => (
              <span
                key={tool}
                className="rounded-md bg-white/15 px-2 py-0.5 text-xs font-medium text-white"
              >
                {tool}
              </span>
            ))}
          </div>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand-orange">
            View course
            <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-1" />
          </span>
        </div>

        <Badge className="absolute top-3 left-3 bg-background/90 text-foreground backdrop-blur-sm">
          {course.category}
        </Badge>
      </div>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={difficultyColors[course.difficulty]}>
            {course.difficulty}
          </Badge>
          <span className="flex items-center gap-1 text-sm text-muted-foreground">
            <Clock className="size-3.5" />
            {course.duration}
          </span>
        </div>
        <CardTitle className="line-clamp-2 text-xl leading-snug group-hover:text-brand-navy">
          <Link href={href}>{course.title}</Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="line-clamp-2 text-base text-muted-foreground">{course.description}</p>
        <div className="flex flex-wrap gap-1.5">
          {toolTags.map((tool) => (
            <Badge key={tool} variant="outline" className="text-xs font-normal">
              {tool}
            </Badge>
          ))}
        </div>
        <div className="flex items-center gap-2 border-t pt-3">
          <div className="flex size-7 items-center justify-center rounded-full bg-brand-navy text-[10px] font-medium text-white">
            {course.instructor.avatar}
          </div>
          <span className="truncate text-sm text-muted-foreground">
            {course.instructor.name}
          </span>
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Star className="size-3.5 fill-brand-orange text-brand-orange" />
            {course.rating}
          </span>
          <span className="flex items-center gap-1">
            <Users className="size-3.5" />
            {course.studentsCount.toLocaleString()}
          </span>
        </div>
        {variant === "enrolled" && course.progress !== undefined && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">{course.progress}%</span>
            </div>
            <Progress value={course.progress} className="h-1.5" />
          </div>
        )}
      </CardContent>
      <CardFooter className="flex items-center justify-between border-t bg-transparent">
        <span className="font-heading text-lg font-bold text-brand-navy">
          {formatPrice(course.price, course.currency)}
        </span>
        <ButtonLink
          href={href}
          size="sm"
          className={cn(
            variant === "enrolled"
              ? "bg-brand-navy hover:bg-brand-navy/90"
              : "bg-brand-orange hover:bg-brand-orange/90",
            "text-white transition-all hover:-translate-y-0.5"
          )}
        >
          {variant === "enrolled" ? "Continue" : "View Course"}
        </ButtonLink>
      </CardFooter>
    </Card>
  );
}
