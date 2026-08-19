import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Clock, Star, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { getContinueHref, getFirstLesson } from "@/lib/course-paths";
import { formatPrice } from "@/lib/mock-data";
import type { Course } from "@/types/course";
import { cn } from "@/lib/utils";

type CourseCardProps = {
  course: Course;
  variant?: "catalog" | "enrolled" | "path";
  className?: string;
};

const difficultyColors = {
  Beginner: "bg-success/10 text-success",
  Intermediate: "bg-warning/10 text-warning",
  Advanced: "bg-destructive/10 text-destructive",
};

export function CourseCard({ course, variant = "catalog", className }: CourseCardProps) {
  const href = variant === "enrolled" ? getContinueHref(course) : `/courses/${course.slug}`;
  const enrolledCta = course.completed
    ? "Review Course"
    : getFirstLesson(course) || course.resumeLessonSlug
      ? "Continue Learning"
      : "Open course";

  const toolTags = course.skills.slice(0, 3);
  const description =
    variant === "path" && course.roleDescription
      ? course.roleDescription
      : course.description;
  const careerOutcomes = course.careerOutcomes ?? [];

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
        {course.comingSoon ? (
          <Badge className="absolute top-3 right-3 bg-brand-orange text-white shadow-sm">
            Launching soon
          </Badge>
        ) : course.isFree ? (
          <Badge className="absolute top-3 right-3 bg-brand-orange text-white shadow-sm">
            FREE
          </Badge>
        ) : null}
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
        <p className="line-clamp-2 text-base text-muted-foreground">{description}</p>
        {variant === "path" && careerOutcomes.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-orange">
              Career outcomes
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {careerOutcomes.map((role) => (
                <Badge key={role} variant="outline" className="text-xs font-normal">
                  {role}
                </Badge>
              ))}
            </div>
          </div>
        )}
        {variant !== "path" && (
          <div className="flex flex-wrap gap-1.5">
            {toolTags.map((tool) => (
              <Badge key={tool} variant="outline" className="text-xs font-normal">
                {tool}
              </Badge>
            ))}
          </div>
        )}
        {variant !== "path" && course.rating > 0 && (
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Star className="size-3.5 fill-brand-orange text-brand-orange" />
              {course.rating}
            </span>
            {course.studentsCount > 0 && (
              <span className="flex items-center gap-1">
                <Users className="size-3.5" />
                {course.studentsCount.toLocaleString()}
              </span>
            )}
          </div>
        )}
        {variant === "enrolled" && course.progress !== undefined && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">
                {course.progress}%
                {course.lessonsTotal
                  ? ` · ${course.lessonsCompleted ?? 0} / ${course.lessonsTotal} lessons`
                  : ""}
              </span>
            </div>
            <Progress value={course.progress} className="h-1.5" />
          </div>
        )}
      </CardContent>
      <CardFooter className="flex items-center justify-between border-t bg-transparent">
        {course.comingSoon ? (
          <span className="rounded-full bg-brand-orange/10 px-3 py-1 text-sm font-semibold text-brand-orange">
            Launching soon
          </span>
        ) : course.isFree || course.price === 0 ? (
          <span className="font-heading text-lg font-bold text-brand-navy dark:text-brand-orange">
            FREE
          </span>
        ) : (
          <span className="font-heading text-lg font-bold text-brand-navy dark:text-brand-orange">
            {formatPrice(course.price, course.currency)}
          </span>
        )}
        <ButtonLink
          href={href}
          size="sm"
          className={cn(
            variant === "enrolled"
              ? "bg-brand-navy hover:bg-brand-navy/90"
              : course.comingSoon
                ? "bg-muted text-foreground hover:bg-muted"
                : "bg-brand-orange hover:bg-brand-orange/90",
            !course.comingSoon && "text-white",
            "transition-all hover:-translate-y-0.5"
          )}
        >
          {variant === "enrolled"
            ? enrolledCta
            : course.comingSoon
              ? "View details"
              : "View Course"}
        </ButtonLink>
      </CardFooter>
    </Card>
  );
}
