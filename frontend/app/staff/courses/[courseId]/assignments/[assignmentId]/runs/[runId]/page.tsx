"use client";

import { use } from "react";
import { DownloadIcon } from "lucide-react";
import { AdminPageHeader } from "@/components/admin-page-header";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { PageLoading } from "@/components/page-status";
import { Button } from "@/components/ui/button";
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
    return <PageLoading className="h-screen">Loading run details...</PageLoading>;
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pt-8 pb-12">
        <Breadcrumbs
          items={[
            { label: "Courses", href: "/staff/courses" },
            { label: "Assignments", href: `/staff/courses/${courseId}/assignments` },
            {
              label: assignmentId,
              href: `/staff/courses/${courseId}/assignments/${assignmentId}`,
            },
            {
              label: "Grade",
              href: `/staff/courses/${courseId}/assignments/${assignmentId}/runs`,
            },
            { label: `Run #${runId}` },
          ]}
        />

        <AdminPageHeader
          title={`Run #${runId}`}
          actions={
            <>
              <Button
                variant="outline"
                size="sm"
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
                size="sm"
                onClick={handleCsvExport}
                disabled={reviewUnavailable || !details?.exports_ready}
                title={
                  details?.exports_ready
                    ? undefined
                    : "Complete all manual scores before exporting."
                }
              >
                <DownloadIcon className="mr-1.5 size-4" /> Grades CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleFeedbackExport}
                disabled={reviewUnavailable || !details?.exports_ready}
                title={
                  details?.exports_ready
                    ? undefined
                    : "Complete all manual scores before exporting."
                }
              >
                <DownloadIcon className="mr-1.5 size-4" /> Feedback ZIP
              </Button>
            </>
          }
        />
        <p role="status" className="-mt-4 mb-6 text-sm text-muted-foreground">
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

        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          <div className="md:col-span-1">
            <GradeHistogram
              students={details?.students ?? []}
              totalSubmissionCount={summary?.total_submission_count}
              completedStudents={details?.completed_students}
              totalStudents={details?.total_students}
              requiresManualGrading={details?.requires_manual_grading}
            />
          </div>

          <div className="space-y-3 md:col-span-3">
            <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
              Students
            </h2>
            <StudentFilterToolbar
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              statusFilter={statusFilter}
              onStatusFilterChange={setStatusFilter}
              counts={filterCounts}
            />

            {!details || details.students.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                {summary?.status === "queue" || summary?.status === "run"
                  ? "Grading in progress… results appear as students finish."
                  : "No student details returned."}
              </p>
            ) : filteredStudents.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No students match the current filter or search.
              </p>
            ) : (
              <ul className="divide-y divide-border border-y border-border">
                {filteredStudents.map((student) => (
                  <li key={student.canvas_id}>
                    <StudentReviewCard
                      student={student}
                      onInspect={handleInspectStudent}
                    />
                  </li>
                ))}
              </ul>
            )}
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
  );
}
