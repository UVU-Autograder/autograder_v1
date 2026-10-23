"use client";

import { use } from "react";
import { DownloadIcon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { retentionMessage } from "@/features/runs/lib/retention";
import { runProcessedCount } from "@/features/assignments/types";
import { GradeHistogram } from "@/features/runs/components/grade-histogram";
import { StudentFilterToolbar } from "@/features/runs/components/student-filter-toolbar";
import { StudentReviewCard } from "@/features/runs/components/student-review-card";
import { StudentInspectDialog } from "@/features/runs/components/student-inspect-dialog";
import { useRunStatusPolling } from "@/features/runs/hooks/use-run-status-polling";
import { useStudentRunFilters } from "@/features/runs/hooks/use-student-run-filters";
import { useManualGrading } from "@/features/runs/hooks/use-manual-grading";

type PageProps = {
  params: Promise<{ courseId: string; assignmentId: string; runId: string }>;
};

export default function RunDetailPage({ params }: PageProps) {
  const { courseId, assignmentId, runId } = use(params);

  const {
    summary,
    runStatus,
    details,
    setDetails,
    isLoading,
    error: pollingError,
    reviewUnavailable,
    isCleaning,
    handleCleanup,
    handleCsvExport,
    handleFeedbackExport,
    handleAcknowledgeIntake,
  } = useRunStatusPolling({ courseId, assignmentId, runId });

  const {
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    filterCounts,
    filteredStudents,
  } = useStudentRunFilters(details?.students);

  const {
    selectedStudent,
    isInspectOpen,
    isSavingGrades,
    success,
    error: manualError,
    handleInspectStudent,
    handleInspectOpenChange,
    handleSaveManualGrades,
  } = useManualGrading({
    courseId,
    assignmentId,
    runId,
    details,
    setDetails,
  });

  const error = pollingError || manualError;

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
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={handleCleanup}
              disabled={
                isCleaning ||
                !summary ||
                summary.status === "queue" ||
                summary.status === "run" ||
                summary.retention_state === "deleted"
              }
            >
              {isCleaning ? "Cleaning…" : "Delete review data"}
            </Button>
            <Button
              variant="outline"
              onClick={handleCsvExport}
              disabled={reviewUnavailable || !details?.exports_ready}
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
              disabled={reviewUnavailable || !details?.exports_ready}
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
        <p role="status" className="mb-6 text-sm text-muted-foreground">
          {retentionMessage(summary)}
        </p>
        {details && !details.exports_ready && (
          <p className="-mt-4 mb-6 text-right text-xs text-warning font-medium">
            {details.intake_pending
              ? "Exports unlock after intake warnings are acknowledged and review is complete."
              : "Exports unlock after every manual rubric item has a score."}
          </p>
        )}

        {details &&
          ((details.unmatched_files?.length ?? 0) > 0 ||
            (details.filename_collisions?.length ?? 0) > 0) && (
            <div className="mb-6 rounded-lg border border-warning/40 bg-warning/5 p-4 text-sm text-foreground">
              <p className="font-semibold text-warning">
                Intake ambiguities need review
              </p>
              {(details.unmatched_files?.length ?? 0) > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-muted-foreground">
                    Unmatched archive files
                  </p>
                  <ul className="mt-1 list-inside list-disc text-xs">
                    {details.unmatched_files!.map((name) => (
                      <li key={name} className="font-mono">
                        {name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {(details.filename_collisions?.length ?? 0) > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-muted-foreground">
                    Filename collisions (larger file kept)
                  </p>
                  <ul className="mt-1 space-y-2 text-xs">
                    {details.filename_collisions!.map((collision) => (
                      <li
                        key={`${collision.canvas_user_id}-${collision.clean_filename}`}
                      >
                        <span className="font-medium">
                          {collision.student_name || collision.canvas_user_id}
                        </span>
                        {": "}
                        <span className="font-mono">{collision.clean_filename}</span>
                        {" — kept "}
                        <span className="font-mono">{collision.kept}</span>
                        {" from "}
                        {collision.candidates.length} candidates
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {!details.intake_acknowledged && (
                <Button
                  className="mt-3"
                  variant="outline"
                  size="sm"
                  onClick={() => void handleAcknowledgeIntake()}
                >
                  Acknowledge intake warnings
                </Button>
              )}
              {details.intake_acknowledged && (
                <p className="mt-3 text-xs text-muted-foreground">
                  Intake warnings acknowledged.
                </p>
              )}
            </div>
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

        {!reviewUnavailable && (
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
        )}
      </div>
    </div>
  );
}
