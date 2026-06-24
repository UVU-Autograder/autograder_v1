"use client";

import { useEffect, useState } from "react";
import { getAssignments } from "@/features/assignments/api";
import { AssignmentsDetails } from "@/features/assignments/types";
import AllAssignmentsPage from "@/features/assignments/admin/all-assignments-page";
import { getStaffCourses } from "@/features/courses/api";

type AssignmentWithCourse = AssignmentsDetails & { courseId: string };

export default function AdminAssignmentsPage() {
  const [assignments, setAssignments] = useState<AssignmentWithCourse[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStaffCourses()
      .then(async (coursesResponse) => {
        const results = await Promise.all(
          coursesResponse.courses.map(async (course) => {
            try {
              const response = await getAssignments(course.id);
              return response.assignments.map((assignment) => ({
                ...assignment,
                courseId: course.id,
              }));
            } catch {
              return [];
            }
          })
        );

        const flattened = results
          .flat()
          .sort((a, b) => {
            const courseCompare = a.courseId.localeCompare(b.courseId);
            if (courseCompare !== 0) return courseCompare;
            return a.title.localeCompare(b.title);
          });

        setAssignments(flattened);
      })
      .catch((err) => {
        console.error(err);
        setError(err instanceof Error ? err.message : "Failed to load assignments.");
      });
  }, []);

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50 p-6">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 max-w-md shadow-sm">
          <p className="font-semibold mb-1">Failed to load assignments</p>
          <p className="text-xs opacity-90">{error}</p>
        </div>
      </div>
    );
  }

  if (!assignments) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">Loading assignments...</p>
      </div>
    );
  }

  return <AllAssignmentsPage assignments={assignments} />;
}
