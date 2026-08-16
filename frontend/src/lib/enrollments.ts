import {
  getAccessToken,
  getMyEnrollments,
  listApiCourses,
  type ApiCourse,
  type EnrollmentPublic,
} from "@/lib/api";
import { getCourseBySlug, isCourseLive } from "@/lib/mock-data";
import type { Course, Difficulty } from "@/types/course";

function asDifficulty(value: string): Difficulty {
  if (value === "Beginner" || value === "Intermediate" || value === "Advanced") {
    return value;
  }
  return "Beginner";
}

export function mapApiCourseToCourse(
  course: ApiCourse,
  options?: { enrolled?: boolean; progress?: number }
): Course {
  // Until curriculum lives in the API, reuse mock modules/skills for the player.
  const mock = getCourseBySlug(course.slug);

  return {
    id: course.id,
    slug: course.slug,
    title: course.title,
    description: course.description,
    longDescription: mock?.longDescription ?? course.description,
    thumbnail: course.thumbnail || mock?.thumbnail || "/python-for-blockchain-analytics.png",
    category: course.category,
    difficulty: asDifficulty(course.difficulty),
    duration: course.duration,
    lessonsCount: course.lessons_count,
    price: course.price,
    currency: course.currency,
    comingSoon: mock?.comingSoon ?? !isCourseLive(course.slug),
    instructor: mock?.instructor ?? {
      name: "Analytic Sages",
      title: "Instructor",
      avatar: "AS",
    },
    rating: mock?.rating ?? 4.8,
    studentsCount: mock?.studentsCount ?? 0,
    modules: mock?.modules ?? [],
    skills: mock?.skills ?? [],
    requirements: mock?.requirements ?? [],
    enrolled: options?.enrolled ?? true,
    progress: options?.progress ?? mock?.progress ?? 0,
  };
}

export type EnrolledCourseBundle = {
  enrollment: EnrollmentPublic;
  course: Course;
};

export async function fetchEnrolledCourses(): Promise<EnrolledCourseBundle[]> {
  if (!getAccessToken()) {
    return [];
  }

  const [enrollments, courses] = await Promise.all([
    getMyEnrollments(),
    listApiCourses(),
  ]);

  const courseById = new Map(courses.map((course) => [course.id, course]));

  return enrollments
    .filter((enrollment) => enrollment.status === "active")
    .map((enrollment) => {
      const apiCourse = courseById.get(enrollment.course_id);
      if (!apiCourse) return null;
      return {
        enrollment,
        course: mapApiCourseToCourse(apiCourse, { enrolled: true, progress: 0 }),
      };
    })
    .filter((item): item is EnrolledCourseBundle => item !== null)
    .sort(
      (a, b) =>
        new Date(b.enrollment.enrolled_at).getTime() -
        new Date(a.enrollment.enrolled_at).getTime()
    );
}
