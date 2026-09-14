import React from "react";
import { EyeIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StudentRunDetail } from "../types";
import { formatBundleSummary } from "../lib/student-filter";

interface StudentReviewCardProps {
  student: StudentRunDetail;
  onInspect: (student: StudentRunDetail) => void;
}

export function StudentReviewCard({ student, onInspect }: StudentReviewCardProps) {
  const manualResults = student.manual_results ?? {};
  const ungradedCount = Object.values(manualResults).filter(
    (m) => m.score === null,
  ).length;
  const totalManualCount = Object.keys(manualResults).length;
  const hasUngraded = ungradedCount > 0;

  return (
    <div className="rounded-lg border border-border p-4 hover:shadow-xs transition-shadow bg-card text-card-foreground">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div className="space-y-0.5">
          <p className="font-semibold text-foreground">{student.student_name}</p>
          <p className="text-xs text-muted-foreground">
            Canvas ID: {student.canvas_id} | {formatBundleSummary(student)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm font-semibold text-foreground mr-1">
            {student.score} / {student.max_score} pts
          </div>
          {totalManualCount > 0 && (
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${
                hasUngraded
                  ? "bg-warning/15 text-warning-foreground border border-warning/30"
                  : "bg-muted text-muted-foreground border border-border"
              }`}
            >
              {hasUngraded ? `Ungraded (${ungradedCount})` : "Graded"}
            </span>
          )}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onInspect(student)}
            className="relative text-xs h-7 px-2"
            data-testid={`inspect-${student.canvas_id}`}
          >
            <EyeIcon className="size-3.5 mr-1" /> Inspect
            {hasUngraded && (
              <span
                aria-hidden
                className="absolute -top-1 -right-1 size-2 rounded-full bg-destructive ring-2 ring-card"
              />
            )}
          </Button>
        </div>
      </div>

      {student.feedback_preview && (
        <div className="mt-3 rounded border border-border bg-muted/40 p-2.5 text-xs text-muted-foreground">
          <span className="font-semibold block text-foreground mb-1">
            Feedback Summary:
          </span>
          <p className="line-clamp-2">{student.feedback_preview}</p>
        </div>
      )}
    </div>
  );
}
