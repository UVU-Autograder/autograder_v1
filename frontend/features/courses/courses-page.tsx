import { PageEmpty } from "@/components/page-status";
import {
  SandboxCoursesResponse,
  StaffCoursesResponse,
} from "@/features/courses/types";
import CourseCard from "@/features/courses/coursecard";

type ViewMode = "sandbox" | "staff";

export default function CoursesPage({
  data,
  mode,
}: {
  data: SandboxCoursesResponse | StaffCoursesResponse;
  mode: ViewMode;
}) {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 pt-8 pb-12">
      <div className="mb-6 space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Courses
        </h1>
        <p className="text-sm text-muted-foreground">
          {mode === "staff"
            ? "Courses you can set up and grade."
            : "Practice assignments without signing in. Scores are estimates, not Canvas grades."}
        </p>
      </div>

      {data.courses.length === 0 ? (
        <PageEmpty>No courses available yet.</PageEmpty>
      ) : (
        <ul className="divide-y divide-border border-y border-border">
          {data.courses.map((course) => (
            <li key={course.id} className="group">
              <CourseCard course={course} mode={mode} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
