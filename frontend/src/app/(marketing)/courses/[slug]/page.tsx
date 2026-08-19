import type { Metadata } from "next";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import Image from "next/image";
import { CheckCircle, Clock, Star, Users } from "lucide-react";
import { SelfPacedCourseLanding } from "@/components/course/self-paced-course-landing";
import { CourseEnrollCta } from "@/components/course/course-enroll-cta";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, getSelfPacedCourse, type SelfPacedCoursePublic } from "@/lib/api";
import { getCourseBySlug } from "@/lib/mock-data";
import { featuredSelfPacedCourse } from "@/lib/self-paced";
import { pageMetadata } from "@/lib/seo";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ slug: string }> };

async function loadSelfPaced(slug: string): Promise<SelfPacedCoursePublic | null> {
  try {
    return await getSelfPacedCourse(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const live = (await loadSelfPaced(slug)) ?? featuredSelfPacedCourse(slug);
  if (live) {
    const description =
      live.description ||
      "Learn practical Dune SQL and dashboard techniques through this free self-paced course from Analytic Sages.";
    return pageMetadata({
      title: live.title,
      description,
      path: `/courses/${live.slug}`,
      image: live.thumbnail || "/dune-analytics-practical-sql-dashboard-techniques.png",
    });
  }
  const course = getCourseBySlug(slug);
  return { title: course?.title ?? "Course" };
}

export default async function CourseDetailsPage({ params }: Props) {
  const { slug } = await params;
  const live = (await loadSelfPaced(slug)) ?? featuredSelfPacedCourse(slug);
  if (live) {
    return (
      <Suspense>
        <SelfPacedCourseLanding initialCourse={live} />
      </Suspense>
    );
  }

  const course = getCourseBySlug(slug);
  if (!course) notFound();

  return (
    <div className="pb-16">
      <div className="border-b bg-brand-surface">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
            <div>
          <PageHeader
            breadcrumbs={[
              { label: "Courses", href: "/courses" },
              { label: course.title },
            ]}
            title={course.title}
            description={course.description}
          />
          <div className="mt-6 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            <Badge>{course.category}</Badge>
            <Badge variant="outline">{course.difficulty}</Badge>
            <span className="flex items-center gap-1">
              <Star className="size-4 fill-brand-orange text-brand-orange" />
              {course.rating}
            </span>
            <span className="flex items-center gap-1">
              <Users className="size-4" />
              {course.studentsCount.toLocaleString()} students
            </span>
            <span className="flex items-center gap-1">
              <Clock className="size-4" />
              {course.duration}
            </span>
          </div>
          <CourseEnrollCta
            slug={course.slug}
            price={course.price}
            currency={course.currency}
            comingSoon={course.comingSoon}
          />
            </div>
            <div className="relative aspect-video overflow-hidden rounded-xl shadow-elevated">
              <Image
                src={course.thumbnail}
                alt={course.title}
                fill
                className="object-cover"
                priority
                sizes="(max-width: 1024px) 100vw, 50vw"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-3 lg:px-8">
        <div className="space-y-8 lg:col-span-2">
          <section>
            <h2 className="font-heading text-xl font-semibold">Overview</h2>
            <p className="mt-3 text-muted-foreground">{course.longDescription}</p>
          </section>
          <section>
            <h2 className="font-heading text-xl font-semibold">What you&apos;ll learn</h2>
            <ul className="mt-4 grid gap-2 sm:grid-cols-2">
              {course.skills.map((skill) => (
                <li key={skill} className="flex items-center gap-2 text-sm">
                  <CheckCircle className="size-4 shrink-0 text-success" />
                  {skill}
                </li>
              ))}
            </ul>
          </section>
          <section>
            <h2 className="font-heading text-xl font-semibold">Curriculum</h2>
            <div className="mt-4 space-y-4">
              {course.modules.length > 0 ? (
                course.modules.map((module, i) => (
                  <Card key={module.id} className="shadow-card">
                    <CardHeader>
                      <CardTitle className="text-base">
                        {i + 1}. {module.title}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {module.lessons.map((lesson) => (
                        <div
                          key={lesson.id}
                          className="flex items-start justify-between gap-4 text-sm"
                        >
                          <span className="text-muted-foreground">{lesson.title}</span>
                          <span className="shrink-0 rounded-md bg-brand-orange/10 px-2 py-0.5 text-xs font-semibold text-brand-orange">
                            {lesson.duration}
                          </span>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">Curriculum coming soon.</p>
              )}
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="text-base">Requirements</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {course.requirements.map((req) => (
                  <li key={req}>• {req}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
