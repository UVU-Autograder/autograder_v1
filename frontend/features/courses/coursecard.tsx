import Link from "next/link";
import { SandboxCourse, StaffCourse } from "@/features/courses/types";

type ViewMode = "sandbox" | "staff";

export default function CourseCard({
  course,
  mode,
}: {
  course: SandboxCourse | StaffCourse;
  mode: ViewMode;
}) {
  const linkHref =
    mode === "sandbox"
      ? `/sandbox/${course.id}/assignments`
      : `/staff/courses/${course.id}/assignments`;

  const meta =
    mode === "staff"
      ? `${(course as StaffCourse).assignment_count} ${(course as StaffCourse).assignment_count === 1 ? "assignment" : "assignments"}`
      : `${(course as SandboxCourse).sandbox_enabled_assignments} open in sandbox`;

  return (
    <Link
      href={linkHref}
      className="flex flex-col gap-1 px-1 py-3 transition-colors hover:bg-muted/40 sm:flex-row sm:items-baseline sm:justify-between sm:gap-4"
    >
      <div className="min-w-0 space-y-0.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-primary">
          {course.id}
        </span>
        <h3 className="truncate text-base font-medium text-foreground group-hover:text-primary">
          {course.title}
        </h3>
      </div>
      <div className="flex shrink-0 flex-wrap items-center gap-x-3 text-xs text-muted-foreground sm:justify-end">
        <span>{course.term}</span>
        <span>{meta}</span>
      </div>
    </Link>
  );
}
