"use client";

import { useEffect, useState } from "react";
import { getAdminCourses } from "@/features/courses/api";
import AllCoursesPage from "@/features/courses/admin/all-courses-page";
import { CourseAdminDetail } from "@/features/courses/types";

export default function AdminCoursesPage() {
  const [courses, setCourses] = useState<CourseAdminDetail[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadCourses = () => {
    getAdminCourses()
      .then((res) => setCourses(res))
      .catch((err) => {
        console.error(err);
        setError(err instanceof Error ? err.message : "Failed to load courses.");
      });
  };

  useEffect(() => {
    loadCourses();
  }, []);

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50 p-6">
        <div className="max-w-md rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 shadow-sm">
          <p className="mb-1 font-semibold">Failed to load courses</p>
          <p className="text-xs opacity-90">{error}</p>
        </div>
      </div>
    );
  }

  if (!courses) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="animate-pulse font-medium text-slate-500">Loading courses...</p>
      </div>
    );
  }

  return <AllCoursesPage initialCourses={courses} refreshCourses={loadCourses} />;
}
