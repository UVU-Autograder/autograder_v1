"use client";

import { useEffect, useState } from "react";
import Loading from "@/app/sandbox/loading";
import { Button } from "@/components/ui/button";
import { getSandboxCourses } from "@/features/courses/api";
import CoursesPage from "@/features/courses/courses-page";

type SandboxCoursesData = Awaited<ReturnType<typeof getSandboxCourses>>;

export default function SandboxCoursesClient() {
  const [data, setData] = useState<SandboxCoursesData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    getSandboxCourses()
      .then(setData)
      .catch(() => setError("Failed to load sandbox courses."));
  }, [attempt]);

  if (error) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-6">
        <p className="text-center text-muted-foreground">{error}</p>
        <Button
          onClick={() => {
            setError(null);
            setAttempt((n) => n + 1);
          }}
        >
          Try again
        </Button>
      </div>
    );
  }
  if (!data) {
    return <Loading />;
  }
  return <CoursesPage data={data} mode="sandbox" />;
}
