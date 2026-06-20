"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { AssignmentsDetails } from "@/features/assignments/types";
import { useBasePath } from "@/lib/view-context";

export default function AssignmentCard({
  assignment,
  courseId,
}: {
  assignment: AssignmentsDetails;
  courseId: string;
}) {
  const basePath = useBasePath();
  return (
    <Link
      href={`${basePath}/courses/${courseId}/assignments/${assignment.id}`}
      className="block"
    >
      <Card className="cursor-pointer py-3 transition-shadow hover:shadow-md">
        <CardContent className="flex items-center gap-3 py-0">
          <div className="flex w-2.5 shrink-0 justify-center">
            {assignment.sandbox_enabled && (
              <span
                className="size-2.5 rounded-full bg-green-500"
                title="Sandbox enabled"
              />
            )}
          </div>

          <div className="min-w-0 space-y-0.5">
            <CardTitle className="truncate text-base">{assignment.title}</CardTitle>
            <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-0 text-xs">
              <span className="uppercase tracking-wider">{assignment.language}</span>
              <span>{assignment.max_score} pts</span>
              <span>
                {assignment.upload_quota.remaining} / {assignment.upload_quota.limit}{" "}
                uploads
              </span>
            </CardDescription>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
