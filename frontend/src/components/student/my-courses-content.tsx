"use client";

import { useEffect, useState } from "react";
import { BookOpen, Loader2 } from "lucide-react";
import { CourseCard } from "@/components/course/course-card";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { ButtonLink } from "@/components/ui/button-link";
import { ApiError, getAccessToken } from "@/lib/api";
import { fetchEnrolledCourses, type EnrolledCourseBundle } from "@/lib/enrollments";

export function MyCoursesContent() {
  const [items, setItems] = useState<EnrolledCourseBundle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authed, setAuthed] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      if (!getAccessToken()) {
        if (!cancelled) {
          setAuthed(false);
          setItems([]);
          setLoading(false);
        }
        return;
      }

      try {
        const enrolled = await fetchEnrolledCourses();
        if (!cancelled) {
          setAuthed(true);
          setItems(enrolled);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load enrollments");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <PageHeader title="My Courses" description="Courses you're enrolled in" />

      {loading && (
        <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Loading your courses…
        </div>
      )}

      {!loading && !authed && (
        <EmptyState
          icon={<BookOpen className="size-5" />}
          title="Sign in to see your courses"
          description="Enrollments are tied to your account. Sign in to view courses you've purchased."
          action={{ label: "Sign in", href: "/login?next=/my-courses" }}
        />
      )}

      {!loading && authed && error && (
        <EmptyState
          icon={<BookOpen className="size-5" />}
          title="Couldn't load enrollments"
          description={error}
          action={{ label: "Browse courses", href: "/courses" }}
        />
      )}

      {!loading && authed && !error && items.length === 0 && (
        <EmptyState
          icon={<BookOpen className="size-5" />}
          title="You haven't enrolled in any courses yet."
          description="Explore a free self-paced course to start learning."
          action={{ label: "Explore Free Courses", href: "/courses" }}
        />
      )}

      {!loading && !error && items.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {items.map(({ course }) => (
            <CourseCard key={course.id} course={course} variant="enrolled" />
          ))}
        </div>
      )}

      {!loading && !authed && (
        <div className="mt-4 text-center">
          <ButtonLink href="/register" variant="ghost" size="sm">
            Create an account
          </ButtonLink>
        </div>
      )}
    </div>
  );
}
