"use client";

import { DownloadIcon, EyeIcon, FileIcon } from "lucide-react";
import Image from "next/image";
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
  staffRunStudentFileContentPath,
  staffRunStudentFilesPath,
} from "@/features/staff/api";
import { languageFromFilename } from "@/features/assignments/workspace/file-utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MonacoEditor from "@/components/monaco-editor";
import { Input } from "@/components/ui/input";

type StudentFile = {
  filepath: string;
  size_bytes: number;
  previewable: boolean;
  preview_kind?: "text" | "image" | "none";
};

type FilePreview =
  | { kind: "text"; content: string }
  | { kind: "image"; contentType: string; contentBase64: string };

type RunSummary = {
  id: number;
  status: string;
  total_submission_count: number;
  success_count: number;
  warning_count: number;
  failure_count: number;
  timeout_count: number;
  created_at: string;
};

type StudentRunDetail = {
  student_name: string;
  canvas_id: string;
  bundle_files: string[];
  bundle_file_count: number;
  score: number;
  max_score: number;
  status: "success" | "failure" | "warning";
  feedback_preview: string;
  feedback_html: string;
  manual_results: Record<
    string,
    { label: string; points: number; score: number | null; comments: string }
  >;
  overall_comment: string;
  automated_results: {
    key: string;
    label: string;
    outcome: string;
    passed: boolean;
    points_awarded: number;
    points: number;
  }[];
  automated_score: number;
  automated_max_score: number;
};

type ManualProgress = {
  requires_manual_grading: boolean;
  completed_students: number;
  total_students: number;
  exports_ready: boolean;
};

type RunDetailsResponse = {
  run_id: number;
  status: string;
  students: StudentRunDetail[];
} & ManualProgress;

type ManualGradeSaveResponse = StudentRunDetail & {
  manual_progress: ManualProgress;
};

function sortStudentsByName(students: StudentRunDetail[]): StudentRunDetail[] {
  return [...students].sort((a, b) =>
    a.student_name.localeCompare(b.student_name),
  );
}

function formatBundleSummary(student: StudentRunDetail): string {
  const count = student.bundle_file_count ?? student.bundle_files?.length ?? 0;
  if (count === 0) {
    return "No submission files prepared";
  }
  return `${count} file${count === 1 ? "" : "s"}`;
}

function hasUngradedManualItems(student: StudentRunDetail): boolean {
  return Object.values(student.manual_results).some(
    (item) => item.score === null,
  );
}

type ScoreBucket = {
  key: string;
  shortLabel: string;
  rangeLabel: string;
  count: number;
};

function buildScoreHistogram(students: StudentRunDetail[]): ScoreBucket[] {
  const buckets: ScoreBucket[] = Array.from({ length: 10 }, (_, i) => ({
    key: `b${i}`,
    shortLabel: i === 9 ? "90+" : `${i * 10}`,
    rangeLabel: i === 9 ? "90–100%" : `${i * 10}–${i * 10 + 9}%`,
    count: 0,
  }));

  for (const student of students) {
    const max = student.max_score;
    const pct = max > 0 ? (student.score / max) * 100 : 0;
    const index = Math.min(9, Math.max(0, Math.floor(pct / 10)));
    buckets[index].count += 1;
  }

  return buckets;
}

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

  const [selectedCanvasId, setSelectedCanvasId] = useState<string | null>(null);
  const [isInspectOpen, setIsInspectOpen] = useState(false);
  const [inspectTab, setInspectTab] = useState("feedback");
  const [studentFiles, setStudentFiles] = useState<StudentFile[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [selectedFilepath, setSelectedFilepath] = useState<string | null>(null);
  const [filePreview, setFilePreview] = useState<FilePreview | null>(null);
  const [filePreviewCache, setFilePreviewCache] = useState<
    Record<string, FilePreview>
  >({});
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [contentError, setContentError] = useState<string | null>(null);

  const selectedStudent = useMemo(
    () =>
      details?.students.find(
        (student) => student.canvas_id === selectedCanvasId,
      ) ?? null,
    [details, selectedCanvasId],
  );

  const scoreHistogram = useMemo(
    () => buildScoreHistogram(details?.students ?? []),
    [details?.students],
  );
  const histogramMaxCount = useMemo(
    () => Math.max(...scoreHistogram.map((bucket) => bucket.count), 1),
    [scoreHistogram],
  );

  const selectedFile = useMemo(
    () =>
      studentFiles.find((file) => file.filepath === selectedFilepath) ?? null,
    [studentFiles, selectedFilepath],
  );

  const [manualGradesDraft, setManualGradesDraft] = useState<
    Record<string, { score: number | null; comments: string }>
  >({});
  const [overallCommentDraft, setOverallCommentDraft] = useState("");
  const [isSavingGrades, setIsSavingGrades] = useState(false);
  const isManualDraftDirty = useMemo(() => {
    if (!selectedStudent) return false;
    const savedGrades = Object.fromEntries(
      Object.entries(selectedStudent.manual_results).map(([key, item]) => [
        key,
        { score: item.score, comments: item.comments || "" },
      ]),
    );
    return (
      JSON.stringify(manualGradesDraft) !== JSON.stringify(savedGrades) ||
      overallCommentDraft !== (selectedStudent.overall_comment || "")
    );
  }, [manualGradesDraft, overallCommentDraft, selectedStudent]);

  const loadFileContent = async (canvasId: string, filepath: string) => {
    const cacheKey = `${canvasId}:${filepath}`;
    const cached = filePreviewCache[cacheKey];
    if (cached !== undefined) {
      setFilePreview(cached);
      setIsLoadingContent(false);
      return;
    }

    setIsLoadingContent(true);
    try {
      const data = await apiClient.get<{
        kind?: "text" | "image";
        content?: string;
        content_type?: string;
        content_base64?: string;
      }>(
        staffRunStudentFileContentPath(
          courseId,
          assignmentId,
          runId,
          canvasId,
          filepath,
        ),
      );
      const preview: FilePreview =
        data.kind === "image" && data.content_base64
          ? {
              kind: "image",
              contentType: data.content_type || "application/octet-stream",
              contentBase64: data.content_base64,
            }
          : { kind: "text", content: data.content ?? "" };
      setFilePreview(preview);
      setFilePreviewCache((prev) => ({ ...prev, [cacheKey]: preview }));
    } catch (err) {
      setContentError(
        err instanceof Error ? err.message : "Failed to load file content.",
      );
    } finally {
      setIsLoadingContent(false);
    }
  };

  const handleSelectFile = (canvasId: string, file: StudentFile) => {
    setSelectedFilepath(file.filepath);
    setFilePreview(null);
    setContentError(null);
    if (!file.previewable) {
      setIsLoadingContent(false);
      return;
    }
    void loadFileContent(canvasId, file.filepath);
  };

  const handleInspectStudent = async (
    student: StudentRunDetail,
    discardUnsaved = false,
  ) => {
    if (
      !discardUnsaved &&
      isManualDraftDirty &&
      !window.confirm("Discard unsaved feedback or grading changes?")
    ) {
      return;
    }
    setSelectedCanvasId(student.canvas_id);
    setIsInspectOpen(true);
    setInspectTab(
      Object.keys(student.manual_results).length > 0 &&
        hasUngradedManualItems(student)
        ? "manual"
        : "feedback",
    );
    setStudentFiles([]);
    setSelectedFilepath(null);
    setFilePreview(null);
    setFilePreviewCache({});
    setContentError(null);
    setIsLoadingFiles(true);

    const draft: Record<string, { score: number | null; comments: string }> =
      {};
    Object.entries(student.manual_results).forEach(([key, val]) => {
      draft[key] = {
        score: val.score,
        comments: val.comments || "",
      };
    });
    setManualGradesDraft(draft);
    setOverallCommentDraft(student.overall_comment || "");

    try {
      const data = await apiClient.get<{ files: StudentFile[] }>(
        staffRunStudentFilesPath(
          courseId,
          assignmentId,
          runId,
          student.canvas_id,
        ),
      );
      setStudentFiles(data.files);
      const firstTextFile = data.files.find(
        (file) => file.previewable && (file.preview_kind ?? "text") === "text",
      );
      const firstPreviewable =
        firstTextFile ?? data.files.find((file) => file.previewable);
      if (firstPreviewable) {
        handleSelectFile(student.canvas_id, firstPreviewable);
      }
    } catch (err) {
      console.error("Failed to load student files", err);
    } finally {
      setIsLoadingFiles(false);
    }
  };

  const handleSaveManualGrades = async (saveAndNext = false) => {
    if (!selectedCanvasId || !details) return;
    setIsSavingGrades(true);
    try {
      const updatedStudent = await apiClient.post<ManualGradeSaveResponse>(
        staffRunManualGradesPath(
          courseId,
          assignmentId,
          runId,
          selectedCanvasId,
        ),
        {
          grades: manualGradesDraft,
          overall_comment: overallCommentDraft,
        },
      );
      const updatedStudents = details.students.map((student) =>
        student.canvas_id === selectedCanvasId ? updatedStudent : student,
      );
      setDetails({
        ...details,
        ...updatedStudent.manual_progress,
        students: updatedStudents,
      });
      setSuccess(
        Object.keys(manualGradesDraft).length > 0
          ? "Grades and feedback saved."
          : "Feedback saved.",
      );
      setTimeout(() => setSuccess(null), 3000);
      if (saveAndNext) {
        const currentIndex = updatedStudents.findIndex(
          (student) => student.canvas_id === selectedCanvasId,
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
          await handleInspectStudent(nextUngraded, true);
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

    const pollStatus = async () => {
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
            await refreshFinished(statusData.state);
            return;
          }
        } catch {
          if (cancelled) return;
        }
        await sleep(getAdaptivePollDelayMs(attempt));
        attempt += 1;
      }
    };

    const pollDetails = async () => {
      while (!cancelled) {
        try {
          const detailsData = await apiClient.get<RunDetailsResponse>(
            `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/details`,
          );
          if (cancelled) return;
          setDetails({
            ...detailsData,
            students: sortStudentsByName(detailsData.students),
          });
        } catch {
          // Details may not exist briefly at start of a run.
        }
        await sleep(3000);
      }
    };

    void pollStatus();
    void pollDetails();
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
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                  Grade Distribution
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-2xl font-bold text-foreground">
                    {summary?.total_submission_count}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Total submissions
                  </p>
                </div>

                <div className="border-t border-border pt-3">
                  <p className="text-2xl font-bold text-foreground">
                    {details?.completed_students ?? 0} /{" "}
                    {details?.total_students ?? 0}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {details?.requires_manual_grading
                      ? "Manual grading complete"
                      : "No manual grading required"}
                  </p>
                </div>

                <div className="border-t border-border pt-4">
                  {(details?.students.length ?? 0) === 0 ? (
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
          </div>

          {/* Student list */}
          <div className="md:col-span-3">
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
                ) : (
                  <div className="space-y-3">
                    {details.students.map((student) => {
                      const ungradedCount = Object.values(
                        student.manual_results,
                      ).filter((m) => m.score === null).length;
                      const totalManualCount = Object.keys(
                        student.manual_results,
                      ).length;
                      return (
                        <div
                          key={student.canvas_id}
                          className="rounded-lg border border-border p-4 hover:shadow-xs transition-shadow bg-card text-card-foreground"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                            <div className="space-y-0.5">
                              <p className="font-semibold text-foreground">
                                {student.student_name}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                Canvas ID: {student.canvas_id} |{" "}
                                {formatBundleSummary(student)}
                              </p>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="text-sm font-semibold text-foreground mr-1">
                                {student.score} / {student.max_score} pts
                              </div>
                              {totalManualCount > 0 && (
                                <span
                                  className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${
                                    ungradedCount > 0
                                      ? "bg-warning/15 text-warning-foreground border border-warning/30"
                                      : "bg-muted text-muted-foreground border border-border"
                                  }`}
                                >
                                  {ungradedCount > 0
                                    ? `Ungraded (${ungradedCount})`
                                    : "Graded"}
                                </span>
                              )}
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => handleInspectStudent(student)}
                                className="relative text-xs h-7 px-2"
                              >
                                <EyeIcon className="size-3.5 mr-1" /> Inspect
                                {ungradedCount > 0 && (
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
                              <p className="line-clamp-2">
                                {student.feedback_preview}
                              </p>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        <Dialog
          open={isInspectOpen}
          onOpenChange={(open) => {
            if (
              !open &&
              isManualDraftDirty &&
              !window.confirm("Discard unsaved feedback or grading changes?")
            ) {
              return;
            }
            setIsInspectOpen(open);
            if (!open) {
              setSelectedCanvasId(null);
            }
          }}
        >
          <DialogContent className="flex h-[min(90vh,56rem)] w-[min(96vw,72rem)] max-w-none flex-col gap-0 overflow-hidden p-0 sm:max-w-none">
            <DialogHeader className="shrink-0 border-b border-border p-6 pr-12">
              <DialogTitle className="text-xl font-bold text-foreground">
                {selectedStudent?.student_name}
              </DialogTitle>
              <DialogDescription className="mt-1 text-xs text-muted-foreground">
                Canvas ID: {selectedStudent?.canvas_id} | Score:{" "}
                {selectedStudent?.score} / {selectedStudent?.max_score} pts
              </DialogDescription>
            </DialogHeader>

            <Tabs
              value={inspectTab}
              onValueChange={setInspectTab}
              className="flex min-h-0 flex-1 flex-col"
            >
              <div className="shrink-0 border-b border-border px-6">
                <TabsList className="border border-border bg-muted text-muted-foreground">
                  <TabsTrigger
                    value="feedback"
                    className="data-[state=active]:bg-background data-[state=active]:text-foreground"
                  >
                    Feedback Preview
                  </TabsTrigger>
                  <TabsTrigger
                    value="code"
                    className="data-[state=active]:bg-background data-[state=active]:text-foreground"
                  >
                    Code Explorer
                  </TabsTrigger>
                  {selectedStudent &&
                    Object.keys(selectedStudent.manual_results).length > 0 && (
                      <TabsTrigger
                        value="manual"
                        className="relative data-[state=active]:bg-background data-[state=active]:text-foreground"
                      >
                        Manual Grading
                        {hasUngradedManualItems(selectedStudent) && (
                          <span
                            aria-hidden
                            className="absolute top-1 right-1 size-1.5 rounded-full bg-destructive"
                          />
                        )}
                      </TabsTrigger>
                    )}
                </TabsList>
              </div>

              <TabsContent
                value="feedback"
                className="min-h-0 flex-1 overflow-y-auto p-6"
              >
                <div className="mx-auto flex max-w-4xl flex-col gap-6">
                  <div className="overflow-y-auto rounded-lg border border-border bg-card p-6 text-card-foreground shadow-xs">
                    {selectedStudent?.feedback_html ? (
                      // feedback_html is generated server-side; staff-only view
                      <div
                        dangerouslySetInnerHTML={{
                          __html: selectedStudent.feedback_html,
                        }}
                      />
                    ) : (
                      <p className="italic text-muted-foreground">
                        No feedback HTML summary available.
                      </p>
                    )}
                  </div>

                  <div className="space-y-3 rounded-lg border border-border bg-card p-4">
                    <div>
                      <label
                        className="text-sm font-semibold text-foreground"
                        htmlFor="overall-comment"
                      >
                        Overall student feedback
                      </label>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Optional note included in the student HTML report.
                      </p>
                    </div>
                    <textarea
                      id="overall-comment"
                      value={overallCommentDraft}
                      onChange={(event) =>
                        setOverallCommentDraft(event.target.value)
                      }
                      placeholder="Optional feedback included in the final HTML report..."
                      rows={4}
                      className="placeholder-muted-foreground w-full rounded border border-input bg-background p-2.5 text-xs text-foreground focus:border-primary focus:outline-none"
                    />
                    <div className="flex justify-end">
                      <Button
                        type="button"
                        disabled={isSavingGrades || !isManualDraftDirty}
                        onClick={() => void handleSaveManualGrades(false)}
                        className="px-4 py-2 text-xs"
                      >
                        {isSavingGrades ? "Saving..." : "Save feedback"}
                      </Button>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent
                value="code"
                className="min-h-0 flex-1 data-[state=active]:flex"
              >
                <div className="flex min-h-0 flex-1 divide-x divide-border">
                  <div className="flex w-64 shrink-0 flex-col space-y-2 overflow-y-auto bg-muted/40 p-4">
                    <h5 className="mb-2 text-xs font-semibold tracking-wider text-muted-foreground uppercase">
                      Submission Files
                    </h5>
                    {isLoadingFiles ? (
                      <p className="animate-pulse text-xs text-muted-foreground">
                        Loading file list...
                      </p>
                    ) : studentFiles.length === 0 ? (
                      <p className="text-xs text-muted-foreground italic">
                        No files found.
                      </p>
                    ) : (
                      <div className="space-y-1">
                        {studentFiles.map((file) => {
                          const isSelected = selectedFilepath === file.filepath;
                          return (
                            <button
                              key={file.filepath}
                              type="button"
                              onClick={() =>
                                selectedStudent &&
                                handleSelectFile(
                                  selectedStudent.canvas_id,
                                  file,
                                )
                              }
                              className={`flex w-full items-center gap-2 rounded px-2.5 py-1.5 text-left font-mono text-xs transition-colors ${
                                isSelected
                                  ? "bg-primary font-semibold text-primary-foreground"
                                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
                              }`}
                            >
                              <FileIcon className="size-3.5 shrink-0" />
                              <span className="truncate" title={file.filepath}>
                                {file.filepath}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  <div className="flex min-h-0 flex-1 flex-col bg-background">
                    {selectedFilepath ? (
                      <div className="flex min-h-0 flex-1 flex-col">
                        <div className="flex shrink-0 items-center justify-between border-b border-border bg-muted/50 px-4 py-2 text-xs">
                          <span className="truncate font-mono text-foreground">
                            {selectedFilepath}
                          </span>
                          <span className="font-mono text-muted-foreground">
                            {selectedFile?.size_bytes} bytes
                          </span>
                        </div>

                        <div className="relative min-h-0 flex-1">
                          {isLoadingContent ? (
                            <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/80">
                              <p className="animate-pulse text-xs text-muted-foreground">
                                Loading file contents...
                              </p>
                            </div>
                          ) : contentError ? (
                            <div className="p-6 text-center text-xs text-destructive">
                              {contentError}
                            </div>
                          ) : !selectedFile?.previewable ? (
                            <div className="p-6 text-center text-xs text-muted-foreground italic">
                              Preview not available for this file type or size.
                            </div>
                          ) : filePreview?.kind === "image" ? (
                            <div className="relative flex h-full w-full items-center justify-center overflow-auto bg-muted/20 p-4">
                              <Image
                                src={`data:${filePreview.contentType};base64,${filePreview.contentBase64}`}
                                alt={selectedFilepath}
                                width={1200}
                                height={900}
                                unoptimized
                                className="max-h-full max-w-full h-auto w-auto object-contain"
                              />
                            </div>
                          ) : (
                            <div className="h-full w-full">
                              <MonacoEditor
                                key={selectedFilepath}
                                height="100%"
                                width="100%"
                                defaultLanguage={languageFromFilename(
                                  selectedFilepath,
                                )}
                                defaultValue={
                                  filePreview?.kind === "text"
                                    ? filePreview.content
                                    : ""
                                }
                                options={{
                                  readOnly: true,
                                  minimap: { enabled: false },
                                }}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-1 items-center justify-center text-xs text-muted-foreground italic">
                        Select a file from the explorer to preview code.
                      </div>
                    )}
                  </div>
                </div>
              </TabsContent>

              <TabsContent
                value="manual"
                className="min-h-0 flex-1 overflow-y-auto p-6"
              >
                <div className="mx-auto max-w-3xl space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-foreground">
                      Manual Rubric Grading
                    </h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Score each criterion and add optional student-facing
                      feedback.
                    </p>
                  </div>

                  <div className="rounded-lg border border-border bg-card p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-foreground">
                        Automated results
                      </h4>
                      <span className="font-mono text-xs text-muted-foreground">
                        {selectedStudent?.automated_score} /{" "}
                        {selectedStudent?.automated_max_score}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {selectedStudent?.automated_results.map((item) => (
                        <div
                          key={item.key}
                          className="flex justify-between gap-3 text-xs"
                        >
                          <span className="text-muted-foreground">
                            {item.label}
                          </span>
                          <span
                            className={
                              item.passed
                                ? "font-semibold text-success"
                                : "font-semibold text-destructive"
                            }
                          >
                            {item.points_awarded} / {item.points}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-4">
                    {Object.entries(selectedStudent?.manual_results ?? {}).map(
                      ([key, item]) => {
                        const draft = manualGradesDraft[key] ?? {
                          score: item.score,
                          comments: item.comments || "",
                        };
                        return (
                          <div
                            key={key}
                            className="space-y-3 rounded-lg border border-border bg-card p-4"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-semibold text-foreground">
                                {item.label}
                              </span>
                              <div className="flex items-center gap-2">
                                <Input
                                  type="number"
                                  min={0}
                                  max={item.points}
                                  step={1}
                                  value={draft.score ?? ""}
                                  placeholder="—"
                                  onChange={(
                                    e: React.ChangeEvent<HTMLInputElement>,
                                  ) => {
                                    const raw = e.target.value;
                                    const score =
                                      raw === "" ? null : Number(raw);
                                    setManualGradesDraft((prev) => ({
                                      ...prev,
                                      [key]: {
                                        ...prev[key],
                                        score,
                                        comments: prev[key]?.comments ?? "",
                                      },
                                    }));
                                  }}
                                  className="h-8 w-20 border-input bg-background text-center font-mono text-xs text-foreground"
                                />
                                <span className="text-xs text-muted-foreground">
                                  / {item.points} pts
                                </span>
                              </div>
                            </div>

                            <textarea
                              value={draft.comments}
                              onChange={(
                                e: React.ChangeEvent<HTMLTextAreaElement>,
                              ) => {
                                setManualGradesDraft((prev) => ({
                                  ...prev,
                                  [key]: {
                                    ...prev[key],
                                    comments: e.target.value,
                                  },
                                }));
                              }}
                              placeholder="Feedback for this item..."
                              rows={2}
                              className="placeholder-muted-foreground w-full rounded border border-input bg-background p-2.5 text-xs text-foreground focus:border-primary focus:outline-none"
                            />
                          </div>
                        );
                      },
                    )}
                  </div>

                  <div className="flex justify-end gap-2 pt-2">
                    <Button
                      type="button"
                      disabled={isSavingGrades}
                      variant="outline"
                      onClick={() => void handleSaveManualGrades(false)}
                      className="px-4 py-2 text-xs"
                    >
                      {isSavingGrades ? "Saving..." : "Save"}
                    </Button>
                    <Button
                      type="button"
                      disabled={isSavingGrades}
                      onClick={() => void handleSaveManualGrades(true)}
                      className="px-4 py-2 text-xs"
                    >
                      {isSavingGrades ? "Saving..." : "Save & Next Ungraded"}
                    </Button>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
