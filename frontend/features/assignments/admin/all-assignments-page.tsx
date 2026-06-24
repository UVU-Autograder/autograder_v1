import Link from "next/link";
import { ArrowLeftIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from "@/components/ui/card";
import { AssignmentsDetails } from "@/features/assignments/types";

type AssignmentWithCourse = AssignmentsDetails & { courseId: string };

export default function AllAssignmentsPage({
  assignments,
}: {
  assignments: AssignmentWithCourse[];
}) {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 pt-8">
      <Button variant="ghost" size="sm" className="mb-4 -ml-2" asChild>
        <Link href="/staff/admin">
          <ArrowLeftIcon />
          Back to admin
        </Link>
      </Button>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">All Assignments</h1>
        <Button disabled>Add assignment</Button>
      </div>

      {assignments.length === 0 ? (
        <p className="text-muted-foreground">No assignments available yet.</p>
      ) : (
        <div className="flex w-full flex-col gap-2">
          {assignments.map((assignment) => (
            <Card
              key={`${assignment.courseId}-${assignment.id}`}
              className="py-3 transition-shadow hover:shadow-md"
            >
              <CardContent className="flex items-center gap-3 py-0">
                <Link
                  href={`/staff/courses/${assignment.courseId}/assignments/${assignment.id}/setup`}
                  className="flex min-w-0 flex-1 items-center gap-3"
                >
                  <div className="flex w-2.5 shrink-0 justify-center">
                    {assignment.sandbox_enabled && (
                      <span
                        className="size-2.5 rounded-full bg-green-500"
                        title="Sandbox enabled"
                      />
                    )}
                  </div>
                  <div className="min-w-0 space-y-0.5">
                    <CardTitle className="truncate text-base">
                      {assignment.title}
                    </CardTitle>
                    <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-0 text-xs">
                      <span className="uppercase tracking-wider">
                        {assignment.courseId}
                      </span>
                      <span className="uppercase tracking-wider">
                        {assignment.language}
                      </span>
                      <span>{assignment.max_score} pts</span>
                      <span>
                        {assignment.upload_quota.remaining} /{" "}
                        {assignment.upload_quota.limit} uploads
                      </span>
                    </CardDescription>
                  </div>
                </Link>
                <div className="flex shrink-0 gap-2">
                  <Button variant="outline" size="sm" disabled>
                    Edit
                  </Button>
                  <Button variant="destructive" size="sm" disabled>
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
