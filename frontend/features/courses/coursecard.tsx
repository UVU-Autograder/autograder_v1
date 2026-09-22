import Link from "next/link";
import { Card } from "@/components/ui/card";
import { SandboxCourse, StaffCourse } from "@/features/courses/types";

type ViewMode = "sandbox" | "staff";


export default function CourseCard({
  course,
  mode,
}: {
  course: SandboxCourse | StaffCourse;
  mode: ViewMode;
}) {
  const linkHref = mode === "sandbox" ? `/sandbox/${course.id}/assignments` : `/staff/courses/${course.id}/assignments`;

  return (
    <Link href={linkHref} className="block group">
      <Card className="hover:shadow-md transition-all cursor-pointer border border-border bg-card text-card-foreground p-6 space-y-4">
        <div className="space-y-1">
          <span className="text-xs font-mono font-bold text-primary tracking-wider uppercase">
            {course.id}
          </span>
          <h3 className="font-bold text-lg text-foreground group-hover:text-primary transition-colors line-clamp-1">
            {course.title}
          </h3>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-border text-xs">
          <span className="text-muted-foreground font-medium">
            {course.term}
          </span>

          <span className="font-semibold text-primary group-hover:underline flex items-center gap-1">
            <span>View assignments</span>
            <span>→</span>
          </span>
        </div>
      </Card>
    </Link>
  );
}