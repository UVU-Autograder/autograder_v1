"use client";

import { useEffect, useState } from "react";
import { getStaffCourses } from "@/features/courses/api";
import CoursesPage from "@/features/courses/courses-page";
import { StaffCoursesResponse } from "@/features/courses/types";

export default function Page() {
  const [data, setData] = useState<StaffCoursesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStaffCourses()
      .then((res) => setData(res))
      .catch((err) => {
        console.error(err);
        setError(err instanceof Error ? err.message : "Failed to load courses.");
      });
  }, []);

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-background p-6">
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive max-w-md shadow-xs">
          <p className="font-semibold mb-1">Failed to load courses</p>
          <p className="text-xs opacity-90">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground font-medium animate-pulse">Loading courses...</p>
      </div>
    );
  }

  return <CoursesPage data={data} mode="staff" />;
}