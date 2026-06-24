"use client";

import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlayIcon } from "lucide-react";
import { AssignmentsDetails } from "@/features/assignments/types";

type ViewMode = "sandbox" | "staff";

export default function AssignmentCard({
  assignment,
  courseId,
  mode,
}: {
  assignment: AssignmentsDetails;
  courseId: string;
  mode: ViewMode;
}) {
  const router = useRouter();
  const linkHref =
    mode === "sandbox"
      ? `/sandbox/${courseId}/assignments/${assignment.id}`
      : `/staff/courses/${courseId}/assignments/${assignment.id}`;

  return (
    <Card
      onClick={() => router.push(linkHref)}
      className="cursor-pointer py-3 transition-shadow hover:shadow-md hover:bg-slate-50/50"
    >
      <CardContent className="flex items-center justify-between py-0 gap-3">
        <div className="flex items-center gap-3 min-w-0">
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
        </div>

        {mode === "staff" && (
          <Button
            size="sm"
            className="shrink-0 relative z-10"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              router.push(`/staff/courses/${courseId}/assignments/${assignment.id}/runs`);
            }}
          >
            <PlayIcon className="mr-1.5 size-3.5" /> Grade Now
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
