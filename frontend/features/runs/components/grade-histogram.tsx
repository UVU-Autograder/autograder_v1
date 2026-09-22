import React, { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StudentRunDetail } from "../types";
import { buildScoreHistogram } from "../lib/student-filter";

interface GradeHistogramProps {
  students: StudentRunDetail[];
  totalSubmissionCount?: number;
  completedStudents?: number;
  totalStudents?: number;
  requiresManualGrading?: boolean;
}

export function GradeHistogram({
  students,
  totalSubmissionCount,
  completedStudents,
  totalStudents,
  requiresManualGrading,
}: GradeHistogramProps) {
  const scoreHistogram = useMemo(
    () => buildScoreHistogram(students),
    [students],
  );
  const histogramMaxCount = useMemo(
    () => Math.max(...scoreHistogram.map((bucket) => bucket.count), 1),
    [scoreHistogram],
  );

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          Grade Distribution
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {totalSubmissionCount !== undefined && (
          <div>
            <p className="text-2xl font-bold text-foreground">
              {totalSubmissionCount}
            </p>
            <p className="text-xs text-muted-foreground">
              Total submissions
            </p>
          </div>
        )}

        {totalStudents !== undefined && (
          <div className="border-t border-border pt-3">
            <p className="text-2xl font-bold text-foreground">
              {completedStudents ?? 0} / {totalStudents}
            </p>
            <p className="text-xs text-muted-foreground">
              {requiresManualGrading
                ? "Manual grading complete"
                : "No manual grading required"}
            </p>
          </div>
        )}

        <div className="border-t border-border pt-4">
          {students.length === 0 ? (
            <p className="text-xs text-muted-foreground italic">
              Score distribution appears as student results load.
            </p>
          ) : (
            <div
              className="flex h-40 items-end gap-1"
              role="img"
              aria-label="Histogram of student scores by percent of max points"
            >
              {scoreHistogram.map((bucket) => {
                const heightPct =
                  bucket.count === 0
                    ? 0
                    : Math.max(
                        8,
                        (bucket.count / histogramMaxCount) * 100,
                      );
                return (
                  <div
                    key={bucket.key}
                    className="flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-1"
                    title={`${bucket.rangeLabel}: ${bucket.count} student${bucket.count === 1 ? "" : "s"}`}
                  >
                    <span className="text-[10px] leading-none text-muted-foreground tabular-nums">
                      {bucket.count > 0 ? bucket.count : ""}
                    </span>
                    <div
                      className={`w-full rounded-t ${
                        bucket.count > 0 ? "bg-primary" : "bg-muted"
                      }`}
                      style={{
                        height: `${bucket.count > 0 ? heightPct : 2}%`,
                      }}
                    />
                    <span className="truncate text-[9px] leading-none text-muted-foreground">
                      {bucket.shortLabel}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
