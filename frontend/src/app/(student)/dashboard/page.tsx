import { CourseCard } from "@/components/course/course-card";
import { CertificateCard } from "@/components/course/certificate-card";
import { PageHeader } from "@/components/layout/page-header";
import { StatsCard } from "@/components/shared/stats-card";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { certificates, getEnrolledCourses } from "@/lib/mock-data";

export const metadata = { title: "Dashboard" };

export default function DashboardPage() {
  const enrolled = getEnrolledCourses();
  const continueCourse = enrolled[0];

  return (
    <div>
      <PageHeader
        title="Welcome back, Ada"
        description="Continue your learning journey"
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="Courses in Progress" value={1} icon="courses" />
        <StatsCard title="Hours Learned" value="24h" icon="clock" trend="+4h" description="this week" />
        <StatsCard title="Certificates" value={1} icon="award" />
        <StatsCard title="Overall Progress" value="68%" icon="trending" trend="+12%" description="this month" />
      </div>

      {continueCourse && (
        <Card className="mb-8 border-brand-navy/20 bg-gradient-to-r from-brand-navy/5 to-brand-orange/5 shadow-card">
          <CardHeader>
            <CardTitle className="text-lg">Continue Learning</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="font-heading font-semibold">{continueCourse.title}</h3>
                <p className="text-sm text-muted-foreground">
                  Lesson 3: Reading Etherscan with Python
                </p>
              </div>
              <ButtonLink
                href={`/courses/${continueCourse.slug}/learn/l3`}
                className="bg-brand-orange text-white hover:bg-brand-orange/90"
              >
                Resume
              </ButtonLink>
            </div>
            <div className="space-y-1.5">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Course progress</span>
                <span className="font-medium">{continueCourse.progress}%</span>
              </div>
              <Progress value={continueCourse.progress ?? 0} className="h-2" />
            </div>
          </CardContent>
        </Card>
      )}

      <section className="mb-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-heading text-lg font-semibold">My Courses</h2>
          <ButtonLink href="/my-courses" variant="ghost" size="sm">
            View all
          </ButtonLink>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {enrolled.map((course) => (
            <CourseCard key={course.id} course={course} variant="enrolled" />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 font-heading text-lg font-semibold">Recent Certificates</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {certificates.map((cert) => (
            <CertificateCard key={cert.id} certificate={cert} />
          ))}
        </div>
      </section>
    </div>
  );
}
