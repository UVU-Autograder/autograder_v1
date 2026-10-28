import React from "react";
import { Button } from "@/components/ui/button";
import { StudentRunDetail } from "../types";
import { formatBundleSummary } from "../lib/student-filter";

interface StudentReviewCardProps {
  student: StudentRunDetail;
  onInspect: (student: StudentRunDetail) => void;
}

function statusLabel(student: StudentRunDetail): string {
  const manualResults = student.manual_results ?? {};
  const ungradedCount = Object.values(manualResults).filter(
    (m) => m.score === null,
  ).length;
  const totalManualCount = Object.keys(manualResults).length;
  const needsAdjudication =
    Boolean(student.requires_adjudication) || student.score === null;

  if (needsAdjudication) return "Needs adjudication";
  if (ungradedCount > 0) return `Ungraded (${ungradedCount})`;
  if (totalManualCount > 0) return "Graded";
  return "Complete";
}

export function StudentReviewCard({ student, onInspect }: StudentReviewCardProps) {
  const needsAdjudication =
    Boolean(student.requires_adjudication) || student.score === null;
  const hasUngraded =
    Object.values(student.manual_results ?? {}).some((m) => m.score === null) ||
    needsAdjudication;
  const status = statusLabel(student);

  return (
    <div className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
      <div className="min-w-0 space-y-0.5">
        <p className="truncate font-medium text-foreground">
          {student.student_name}
        </p>
        <p className="truncate text-xs text-muted-foreground">
          {student.canvas_id}
          {formatBundleSummary(student) ? ` · ${formatBundleSummary(student)}` : ""}
          {student.feedback_preview
            ? ` · ${student.feedback_preview}`
            : ""}
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <div className="text-right text-sm tabular-nums text-foreground">
          {needsAdjudication
            ? `— / ${student.max_score}`
            : `${student.score} / ${student.max_score}`}
        </div>
        <span
          className={`min-w-[7.5rem] text-xs ${
            hasUngraded ? "text-warning-foreground" : "text-muted-foreground"
          }`}
        >
          {status}
        </span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onInspect(student)}
          className="relative h-7 px-2 text-xs"
          data-testid={`inspect-${student.canvas_id}`}
        >
          Inspect
          {hasUngraded && (
            <span
              aria-hidden
              className="absolute -top-1 -right-1 size-2 rounded-full bg-destructive ring-2 ring-background"
            />
          )}
        </Button>
      </div>
    </div>
  );
}
