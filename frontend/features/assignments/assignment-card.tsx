"use client";

import Link from "next/link";
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
  const linkHref =
    mode === "sandbox"
      ? `/sandbox/${courseId}/assignments/${assignment.id}`
      : `/staff/courses/${courseId}/assignments/${assignment.id}`;

  return (
    <Card className="py-3 transition-shadow hover:shadow-md hover:bg-muted/50">
      <CardContent className="flex items-center justify-between py-0 gap-3">
        <Link href={linkHref} className="min-w-0 flex-1 flex items-center gap-3 group">
          <div className="min-w-0 space-y-0.5">
            <CardTitle className="truncate text-base group-hover:text-primary transition-colors">
              {assignment.title}
            </CardTitle>
            <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
              <span className="uppercase tracking-wider text-muted-foreground">
                {assignment.language}
              </span>
              <span className="text-muted-foreground">
                {assignment.max_score} pts
              </span>
              {mode === "staff" && assignment.sandbox_enabled && (
                <span className="text-muted-foreground">Sandbox on</span>
              )}
            </CardDescription>
          </div>
        </Link>

        {mode === "staff" && (
          <Button asChild size="sm" className="shrink-0">
            <Link href={`/staff/courses/${courseId}/assignments/${assignment.id}/runs`}>
              <PlayIcon className="mr-1.5 size-3.5" /> Grade Now
            </Link>
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
