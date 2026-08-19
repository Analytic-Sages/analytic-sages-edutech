"use client";

import { use, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { MockCoursePlayer } from "@/components/course/mock-course-player";
import { SelfPacedLearnPage } from "@/components/course/self-paced-learn-page";
import { ApiError, getSelfPacedCourse } from "@/lib/api";

type Props = {
  params: Promise<{ slug: string; lessonId: string }>;
};

export default function CoursePlayerPage({ params }: Props) {
  const { slug, lessonId } = use(params);
  const [mode, setMode] = useState<"loading" | "self-paced" | "mock">("loading");

  useEffect(() => {
    let cancelled = false;
    getSelfPacedCourse(slug)
      .then(() => {
        if (!cancelled) setMode("self-paced");
      })
      .catch((err) => {
        if (!cancelled) {
          if (err instanceof ApiError && err.status === 404) setMode("mock");
          else setMode("self-paced");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (mode === "loading") {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading course…
      </div>
    );
  }

  if (mode === "self-paced") {
    return <SelfPacedLearnPage slug={slug} lessonSlug={lessonId} />;
  }

  return <MockCoursePlayer params={Promise.resolve({ slug, lessonId })} />;
}
