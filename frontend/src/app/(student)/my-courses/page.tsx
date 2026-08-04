import { CourseCard } from "@/components/course/course-card";
import { PageHeader } from "@/components/layout/page-header";
import { getEnrolledCourses } from "@/lib/mock-data";

export const metadata = { title: "My Courses" };

export default function MyCoursesPage() {
  const enrolled = getEnrolledCourses();

  return (
    <div>
      <PageHeader title="My Courses" description="Courses you're enrolled in" />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {enrolled.map((course) => (
          <CourseCard key={course.id} course={course} variant="enrolled" />
        ))}
      </div>
    </div>
  );
}
