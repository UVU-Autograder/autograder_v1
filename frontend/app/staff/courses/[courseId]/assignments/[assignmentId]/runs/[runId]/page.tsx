"use client";

import { DownloadIcon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { use, useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import type { RunStatusResponse } from "@/features/assignments/types";
import { runProcessedCount } from "@/features/assignments/types";
import {
  getAdaptivePollDelayMs,
  getRunStatus,
  sleep,
} from "@/features/assignments/api";
import {
  staffRunCsvExportPath,
  staffRunFeedbackExportPath,
  staffRunManualGradesPath,
} from "@/features/staff/api";
import { GradeHistogram } from "@/features/runs/components/grade-histogram";
import { StudentFilterToolbar } from "@/features/runs/components/student-filter-toolbar";
import { StudentReviewCard } from "@/features/runs/components/student-review-card";
import { StudentInspectDialog } from "@/features/runs/components/student-inspect-dialog";
import {
  filterStudents,
  hasUngradedManualItems,
  sortStudentsByName,
} from "@/features/runs/lib/student-filter";
import type {
  RunSummary,
  RunDetailsResponse,
  ManualGradeSaveResponse,
  StudentRunDetail,
  StatusFilter,
} from "@/features/runs/types";

type PageProps = {
  params: Promise<{ courseId: string; assignmentId: string; runId: string }>;
};

export default function RunDetailPage({ params }: PageProps) {
  const { courseId, assignmentId, runId } = use(params);
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatusResponse | null>(null);
  const [details, setDetails] = useState<RunDetailsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const [selectedCanvasId, setSelectedCanvasId] = useState<string | null>(null);
  const [isInspectOpen, setIsInspectOpen] = useState(false);
  const [isSavingGrades, setIsSavingGrades] = useState(false);

  const selectedStudent = useMemo(
    () =>
      details?.students.find(
        (student) => student.canvas_id === selectedCanvasId,
      ) ?? null,
    [details, selectedCanvasId],
  );

  const filterCounts = useMemo(() => {
    const counts = { all: 0, ungraded: 0, graded: 0, failed: 0 };
    for (const s of details?.students ?? []) {
      counts.all += 1;
      const isUngraded =
        Object.keys(s.manual_results ?? {}).length > 0 &&
        hasUngradedManualItems(s);
      if (isUngraded) {
        counts.ungraded += 1;
      } else {
        counts.graded += 1;
      }
      if (s.status === "failure") {
        counts.failed += 1;
      }
    }
    return counts;
  }, [details?.students]);

  const filteredStudents = useMemo(
    () => filterStudents(details?.students ?? [], searchQuery, statusFilter),
    [details?.students, searchQuery, statusFilter],
  );

  const handleInspectStudent = (student: StudentRunDetail) => {
    setSelectedCanvasId(student.canvas_id);
    setIsInspectOpen(true);
  };

  const handleInspectOpenChange = (open: boolean) => {
    setIsInspectOpen(open);
    if (!open) {
      setSelectedCanvasId(null);
    }
  };

  const handleSaveManualGrades = async (
    canvasId: string,
    grades: Record<string, { score: number | null; comments: string }>,
    overallComment: string,
    saveAndNext = false,
  ) => {
    if (!details) return;
    setIsSavingGrades(true);
    try {
      const updatedStudent = await apiClient.post<ManualGradeSaveResponse>(
        staffRunManualGradesPath(
          courseId,
          assignmentId,
          runId,
          canvasId,
        ),
        {
          grades,
          overall_comment: overallComment,
        },
      );
      const updatedStudents = details.students.map((student) =>
        student.canvas_id === canvasId ? updatedStudent : student,
      );
      setDetails({
        ...details,
        ...updatedStudent.manual_progress,
        students: updatedStudents,
      });
      setSuccess(
        Object.keys(grades).length > 0
          ? "Grades and feedback saved."
          : "Feedback saved.",
      );
      setTimeout(() => setSuccess(null), 3000);

      if (saveAndNext) {
        const currentIndex = updatedStudents.findIndex(
          (student) => student.canvas_id === canvasId,
        );
        const remainingQueue = [
          ...updatedStudents.slice(currentIndex + 1),
          ...updatedStudents.slice(0, currentIndex),
        ];
        const nextUngraded = remainingQueue.find((student) =>
          Object.values(student.manual_results).some(
            (item) => item.score === null,
          ),
        );
        if (nextUngraded) {
          setSelectedCanvasId(nextUngraded.canvas_id);
        } else {
          setIsInspectOpen(false);
          setSelectedCanvasId(null);
        }
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save manual grades.",
      );
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsSavingGrades(false);
    }
  };

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) {
        setIsLoading(true);
        setError(null);
      }
    });

    const loadData = async () => {
      try {
        const summaryData = await apiClient.get<RunSummary>(
          `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}`,
        );
        if (!active) return;
        setSummary(summaryData);

        try {
          const detailsData = await apiClient.get<RunDetailsResponse>(
            `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/details`,
          );
          if (!active) return;
          setDetails({
            ...detailsData,
            students: sortStudentsByName(detailsData.students),
          });
        } catch {
          if (!active) return;
          if (summaryData.status === "queue" || summaryData.status === "run") {
            setDetails(null);
          }
        }
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof Error ? err.message : "Failed to load run details.",
        );
      } finally {
        if (!active) return;
        setIsLoading(false);
      }
    };

    loadData();
    return () => {
      active = false;
    };
  }, [courseId, assignmentId, runId]);

  useEffect(() => {
    const status = summary?.status;
    if (status !== "queue" && status !== "run") {
      return;
    }

    let cancelled = false;

    const refreshFinished = async (state: string) => {
      const [summaryData, detailsData] = await Promise.all([
        apiClient.get<RunSummary>(
          `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}`,
        ),
        state === "complete"
          ? apiClient.get<RunDetailsResponse>(
              `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/details`,
            )
          : Promise.resolve(null),
      ]);
      if (cancelled) return;
      setSummary(summaryData);
      if (detailsData) {
        setDetails({
          ...detailsData,
          students: sortStudentsByName(detailsData.students),
        });
      }
    };

    const pollRun = async () => {
      let attempt = 0;
      while (!cancelled) {
        try {
          const statusData = await getRunStatus(`/runs/${runId}/status`);
          if (cancelled) return;
          setRunStatus(statusData);
          if (
            statusData.state === "complete" ||
            statusData.state === "failure"
          ) {
            cancelled = true;
            await refreshFinished(statusData.state);
            return;
          }

          // Fetch intermediate details while run is in progress
          try {
            const detailsData = await apiClient.get<RunDetailsResponse>(
              `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/details`,
            );
            if (!cancelled && detailsData) {
              setDetails({
                ...detailsData,
                students: sortStudentsByName(detailsData.students),
              });
            }
          } catch {
            // Details may not exist briefly at start of a run.
          }
        } catch {
          if (cancelled) return;
        }
        await sleep(getAdaptivePollDelayMs(attempt));
        attempt += 1;
      }
    };

    void pollRun();
    return () => {
      cancelled = true;
    };
  }, [summary?.status, courseId, assignmentId, runId]);

  const handleCsvExport = async () => {
    setError(null);
    try {
      await apiClient.download(
        staffRunCsvExportPath(courseId, assignmentId, runId),
        `run-${runId}-grades.csv`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV export failed.");
    }
  };

  const handleFeedbackExport = async () => {
    setError(null);
    try {
      await apiClient.download(
        staffRunFeedbackExportPath(courseId, assignmentId, runId),
        `run-${runId}-feedback.zip`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feedback export failed.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground font-medium animate-pulse">
          Loading run details...
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6 md:p-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <BackLink
              href={`/staff/courses/${courseId}/assignments`}
              variant="compact"
            >
              Back to course details
            </BackLink>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Run #{runId} Details
            </h1>
            <p className="text-muted-foreground">
              Grading results overview and student lists
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={handleCsvExport}
              disabled={!details?.exports_ready}
              title={
                details?.exports_ready
                  ? undefined
                  : "Complete all manual scores before exporting."
              }
            >
              <DownloadIcon className="mr-2 size-4" /> Export Grades CSV
            </Button>
            <Button
              variant="outline"
              onClick={handleFeedbackExport}
              disabled={!details?.exports_ready}
              title={
                details?.exports_ready
                  ? undefined
                  : "Complete all manual scores before exporting."
              }
            >
              <DownloadIcon className="mr-2 size-4" /> Export Feedback ZIP
            </Button>
          </div>
        </div>
        {details && !details.exports_ready && (
          <p className="-mt-4 mb-6 text-right text-xs text-warning font-medium">
            Exports unlock after every manual rubric item has a score.
          </p>
        )}

        {runStatus &&
          (runStatus.state === "queue" || runStatus.state === "run") &&
          runStatus.counters && (
            <div className="mb-6 rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm text-foreground">
              <p className="font-semibold text-primary">
                Grading in progress: {runProcessedCount(runStatus.counters)} /{" "}
                {runStatus.counters.total} students complete
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {runStatus.counters.completed} passed
                {runStatus.counters.warnings > 0 &&
                  `, ${runStatus.counters.warnings} with warnings`}
                {runStatus.counters.failed > 0 &&
                  `, ${runStatus.counters.failed} failed`}
                {runStatus.counters.running > 0 &&
                  ` · ${runStatus.counters.running} in progress`}
              </p>
            </div>
          )}

        {error && (
          <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive font-medium">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 rounded-lg border border-success/30 bg-success/10 p-4 text-sm text-success font-medium">
            {success}
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
          <div className="space-y-4 md:col-span-1">
            <GradeHistogram
              students={details?.students ?? []}
              totalSubmissionCount={summary?.total_submission_count}
              completedStudents={details?.completed_students}
              totalStudents={details?.total_students}
              requiresManualGrading={details?.requires_manual_grading}
            />
          </div>

          {/* Student list */}
          <div className="space-y-4 md:col-span-3">
            <StudentFilterToolbar
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              statusFilter={statusFilter}
              onStatusFilterChange={setStatusFilter}
              counts={filterCounts}
            />

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Graded Students</CardTitle>
              </CardHeader>
              <CardContent>
                {!details || details.students.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-6">
                    {summary?.status === "queue" || summary?.status === "run"
                      ? "Grading in progress… student results will appear here as they finish."
                      : "No student details returned."}
                  </p>
                ) : filteredStudents.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-6">
                    No students match the current filter or search query.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {filteredStudents.map((student) => (
                      <StudentReviewCard
                        key={student.canvas_id}
                        student={student}
                        onInspect={handleInspectStudent}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        <StudentInspectDialog
          isOpen={isInspectOpen}
          onOpenChange={handleInspectOpenChange}
          student={selectedStudent}
          courseId={courseId}
          assignmentId={assignmentId}
          runId={runId}
          onSaveManualGrades={handleSaveManualGrades}
          isSavingGrades={isSavingGrades}
        />
      </div>
    </div>
  );
}
