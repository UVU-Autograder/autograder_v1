"use client";

import Link from "next/link";
import { ArrowLeftIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AssignmentsResponse } from "@/features/assignments/types";
import AssignmentCard from "@/features/assignments/assignment-card";
import { useBasePath } from "@/lib/view-context";

export default function AssignmentsPage({ data }: { data: AssignmentsResponse }) {
  const basePath = useBasePath();
  return (
    <div className="w-full px-4 pt-8">
      <div className="mb-6">
        <Button variant="ghost" size="sm" className="mb-4 -ml-2" asChild>
          <Link href={`${basePath}/courses`}>
            <ArrowLeftIcon />
            Back to courses
          </Link>
        </Button>
        <h1 className="text-2xl font-semibold tracking-tight">Assignments</h1>
        <p className="text-muted-foreground mt-1">{data.course_id}</p>
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
            />
          ))}
        </div>
      )}
    </div>
  );
}
