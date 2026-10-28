import React, { useMemo } from "react";
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
    <div className="space-y-4">
      <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
        Summary
      </h2>

      {totalSubmissionCount !== undefined && (
        <div>
          <p className="text-2xl font-semibold tabular-nums text-foreground">
            {totalSubmissionCount}
          </p>
          <p className="text-xs text-muted-foreground">Submissions</p>
        </div>
      )}

      {totalStudents !== undefined && (
        <div>
          <p className="text-2xl font-semibold tabular-nums text-foreground">
            {completedStudents ?? 0} / {totalStudents}
          </p>
          <p className="text-xs text-muted-foreground">
            {requiresManualGrading
              ? "Manual grading complete"
              : "No manual grading required"}
          </p>
        </div>
      )}

      <div>
        <p className="mb-2 text-xs text-muted-foreground">Score distribution</p>
        {students.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            Appears as student results load.
          </p>
        ) : (
          <div
            className="flex h-32 items-end gap-1"
            role="img"
            aria-label="Histogram of student scores by percent of max points"
          >
            {scoreHistogram.map((bucket) => {
              const heightPct =
                bucket.count === 0
                  ? 0
                  : Math.max(8, (bucket.count / histogramMaxCount) * 100);
              return (
                <div
                  key={bucket.key}
                  className="flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-1"
                  title={`${bucket.rangeLabel}: ${bucket.count} student${bucket.count === 1 ? "" : "s"}`}
                >
                  <span className="text-[10px] leading-none tabular-nums text-muted-foreground">
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
    </div>
  );
}
