import { CourseCard } from "@/components/course/course-card";
import { PageHeader } from "@/components/layout/page-header";
import { courses } from "@/lib/mock-data";

export const metadata = { title: "Explore Courses" };

export default function ExplorePage() {
  return (
    <div>
      <PageHeader
        title="Explore Courses"
        description="Discover new skills and advance your career"
      />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {courses.map((course) => (
          <CourseCard key={course.id} course={course} />
        ))}
      </div>
    </div>
  );
}
