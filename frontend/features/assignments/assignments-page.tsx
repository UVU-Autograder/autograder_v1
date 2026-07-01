import Link from "next/link";
import { ArrowLeftIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AssignmentsResponse } from "@/features/assignments/types";
import AssignmentCard from "@/features/assignments/assignment-card";

type ViewMode = "sandbox" | "staff";

export default function AssignmentsPage({
  data,
  mode,
}: {
  data: AssignmentsResponse;
  mode: ViewMode;
}) {
  const backHref = mode === "sandbox" ? "/sandbox" : "/staff/courses";

  return (
    <div className="w-full px-4 pt-8">
      <div className="mb-6">
        <Button variant="ghost" size="sm" className="mb-4 -ml-2" asChild>
          <Link href={backHref}>
            <ArrowLeftIcon />
            Back to courses
          </Link>
        </Button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Assignments</h1>
            <p className="text-muted-foreground mt-1">{data.course_id}</p>
          </div>
          {mode === "staff" && (
            <div className="flex gap-2">
              <Button variant="outline" asChild>
                <Link href={`/staff/courses/${data.course_id}/settings`}>
                  Course Settings
                </Link>
              </Button>
              <Button asChild>
                <Link href={`/staff/courses/${data.course_id}/assignments/new`}>
                  New Assignment
                </Link>
              </Button>
            </div>
          )}
        </div>
      </div>

      {data.assignments.length === 0 ? (
        <p className="text-muted-foreground">No assignments available yet.</p>
      ) : (
        <div className="flex w-full flex-col gap-2">
          {data.assignments.map((assignment) => (
            <AssignmentCard
              key={assignment.id}
              assignment={assignment}
              courseId={data.course_id}
              mode={mode}
            />
          ))}
        </div>
      )}
    </div>
  );
}
