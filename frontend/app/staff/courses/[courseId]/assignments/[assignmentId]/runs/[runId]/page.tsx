"use client";

import { DownloadIcon, AwardIcon, EyeIcon, FileIcon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { use, useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import {
  staffRunCsvExportPath,
  staffRunFeedbackExportPath,
  staffRunManualGradesPath,
  staffRunStudentFileContentPath,
  staffRunStudentFilesPath,
} from "@/features/staff/api";
import { languageFromFilename } from "@/features/assignments/workspace/file-utils";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MonacoEditor from "@/components/monaco-editor";
import { Input } from "@/components/ui/input";

type StudentFile = {
  filepath: string;
  size_bytes: number;
  previewable: boolean;
};

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
  matched_file: string;
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

type PageProps = {
  params: Promise<{ courseId: string; assignmentId: string; runId: string }>;
};

export default function RunDetailPage({ params }: PageProps) {
  const { courseId, assignmentId, runId } = use(params);
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [details, setDetails] = useState<RunDetailsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [selectedCanvasId, setSelectedCanvasId] = useState<string | null>(null);
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const [studentFiles, setStudentFiles] = useState<StudentFile[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [selectedFilepath, setSelectedFilepath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [fileContentCache, setFileContentCache] = useState<Record<string, string>>({});
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [contentError, setContentError] = useState<string | null>(null);

  const selectedStudent = useMemo(
    () => details?.students.find((student) => student.canvas_id === selectedCanvasId) ?? null,
    [details, selectedCanvasId]
  );

  const selectedFile = useMemo(
    () => studentFiles.find((file) => file.filepath === selectedFilepath) ?? null,
    [studentFiles, selectedFilepath]
  );

  const [manualGradesDraft, setManualGradesDraft] = useState<Record<string, { score: number | null; comments: string }>>({});
  const [overallCommentDraft, setOverallCommentDraft] = useState("");
  const [isSavingGrades, setIsSavingGrades] = useState(false);
  const isManualDraftDirty = useMemo(() => {
    if (!selectedStudent) return false;
    const savedGrades = Object.fromEntries(
      Object.entries(selectedStudent.manual_results).map(([key, item]) => [
        key,
        { score: item.score, comments: item.comments || "" },
      ])
    );
    return (
      JSON.stringify(manualGradesDraft) !== JSON.stringify(savedGrades) ||
      overallCommentDraft !== (selectedStudent.overall_comment || "")
    );
  }, [manualGradesDraft, overallCommentDraft, selectedStudent]);

  const loadFileContent = async (canvasId: string, filepath: string) => {
    const cacheKey = `${canvasId}:${filepath}`;
    const cached = fileContentCache[cacheKey];
    if (cached !== undefined) {
      setFileContent(cached);
      setIsLoadingContent(false);
      return;
    }

    setIsLoadingContent(true);
    try {
      const data = await apiClient.get<{ content: string }>(
        staffRunStudentFileContentPath(courseId, assignmentId, runId, canvasId, filepath)
      );
      setFileContent(data.content);
      setFileContentCache((prev) => ({ ...prev, [cacheKey]: data.content }));
    } catch (err) {
      setContentError(err instanceof Error ? err.message : "Failed to load file content.");
    } finally {
      setIsLoadingContent(false);
    }
  };

  const handleSelectFile = (canvasId: string, file: StudentFile) => {
    setSelectedFilepath(file.filepath);
    setFileContent(null);
    setContentError(null);
    if (!file.previewable) {
      setIsLoadingContent(false);
      return;
    }
    void loadFileContent(canvasId, file.filepath);
  };

  const handleInspectStudent = async (
    student: StudentRunDetail,
    discardUnsaved = false
  ) => {
    if (
      !discardUnsaved &&
      isManualDraftDirty &&
      !window.confirm("Discard unsaved manual grading changes?")
    ) {
      return;
    }
    setSelectedCanvasId(student.canvas_id);
    setIsSheetOpen(true);
    setStudentFiles([]);
    setSelectedFilepath(null);
    setFileContent(null);
    setFileContentCache({});
    setContentError(null);
    setIsLoadingFiles(true);

    const draft: Record<string, { score: number | null; comments: string }> = {};
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
        staffRunStudentFilesPath(courseId, assignmentId, runId, student.canvas_id)
      );
      setStudentFiles(data.files);
      const firstTextFile = data.files.find((file) => file.previewable);
      if (firstTextFile) {
        handleSelectFile(student.canvas_id, firstTextFile);
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
        staffRunManualGradesPath(courseId, assignmentId, runId, selectedCanvasId),
        {
          grades: manualGradesDraft,
          overall_comment: overallCommentDraft,
        }
      );
      const updatedStudents = details.students.map((student) =>
        student.canvas_id === selectedCanvasId ? updatedStudent : student
      );
      setDetails({
        ...details,
        ...updatedStudent.manual_progress,
        students: updatedStudents,
      });
      setSuccess("Manual grades saved successfully!");
      setTimeout(() => setSuccess(null), 3000);
      if (saveAndNext) {
        const currentIndex = updatedStudents.findIndex(
          (student) => student.canvas_id === selectedCanvasId
        );
        const remainingQueue = [
          ...updatedStudents.slice(currentIndex + 1),
          ...updatedStudents.slice(0, currentIndex),
        ];
        const nextUngraded = remainingQueue.find((student) =>
          Object.values(student.manual_results).some(
            (item) => item.score === null
          )
        );
        if (nextUngraded) {
          await handleInspectStudent(nextUngraded, true);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save manual grades.");
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
          `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}`
        );
        if (!active) return;
        setSummary(summaryData);

        const detailsData = await apiClient.get<RunDetailsResponse>(
          `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/details`
        );
        if (!active) return;
        setDetails({
          ...detailsData,
          students: [...detailsData.students].sort((a, b) =>
            a.student_name.localeCompare(b.student_name)
          ),
        });
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load run details.");
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

  // Keep workspace intact for its 24h retention window unless explicitly purged by staff

  const handleCsvExport = async () => {
    setError(null);
    try {
      await apiClient.download(
        staffRunCsvExportPath(courseId, assignmentId, runId),
        `run-${runId}-grades.csv`
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
        `run-${runId}-feedback.zip`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feedback export failed.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">Loading run details...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <BackLink href={`/staff/courses/${courseId}/assignments`} variant="compact">
              Back to course details
            </BackLink>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Run #{runId} Details</h1>
            <p className="text-muted-foreground">Grading results overview and student lists</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={handleCsvExport}
              disabled={!details?.exports_ready}
              title={details?.exports_ready ? undefined : "Complete all manual scores before exporting."}
            >
              <DownloadIcon className="mr-2 size-4" /> Export Grades CSV
            </Button>
            <Button
              variant="outline"
              onClick={handleFeedbackExport}
              disabled={!details?.exports_ready}
              title={details?.exports_ready ? undefined : "Complete all manual scores before exporting."}
            >
              <DownloadIcon className="mr-2 size-4" /> Export Feedback ZIP
            </Button>
          </div>
        </div>
        {details && !details.exports_ready && (
          <p className="-mt-4 mb-6 text-right text-xs text-amber-600 dark:text-amber-400 font-medium">
            Exports unlock after every manual rubric item has a score.
          </p>
        )}

        {/* Zero-Retention Warning Banner */}
        <div className="mb-6 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-600 dark:text-amber-400">
          <div className="flex gap-2 items-start font-semibold mb-1">
            <AwardIcon className="size-4 shrink-0 mt-0.5 animate-pulse text-amber-600" />
            <span>Zero-Retention Policy Active</span>
          </div>
          <p className="text-xs text-amber-700 leading-relaxed">
            Important: Leaving, refreshing, or closing this page will permanently purge all student submissions, grades CSVs, and feedback ZIPs from the server workspace. Make sure to download your exports first!
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-600">
            {success}
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
          {/* Summary stats */}
          <div className="md:col-span-1 space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-slate-500 uppercase">Run Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-2xl font-bold text-slate-900">{summary?.total_submission_count}</p>
                  <p className="text-xs text-slate-500">Total Submissions Processed</p>
                </div>
                <div className="border-t border-slate-100 pt-3">
                  <p className="text-2xl font-bold text-slate-900">
                    {details?.completed_students ?? 0} / {details?.total_students ?? 0}
                  </p>
                  <p className="text-xs text-slate-500">
                    {details?.requires_manual_grading
                      ? "Manual grading complete"
                      : "No manual grading required"}
                  </p>
                </div>
                <div className="flex justify-between border-t border-border pt-3 text-sm">
                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Passed</span>
                  <span className="font-bold text-foreground">{summary?.success_count}</span>
                </div>
                <div className="flex justify-between border-t border-border pt-3 text-sm">
                  <span className="text-rose-600 dark:text-rose-400 font-semibold">Failed</span>
                  <span className="font-bold text-foreground">{summary?.failure_count}</span>
                </div>
                <div className="flex justify-between border-t border-border pt-3 text-sm">
                  <span className="text-amber-600 dark:text-amber-400 font-semibold">Warnings</span>
                  <span className="font-bold text-foreground">{summary?.warning_count}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Student list */}
          <div className="md:col-span-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Graded Students</CardTitle>
                <CardDescription>Parity grading outcomes for individuals in this run.</CardDescription>
              </CardHeader>
              <CardContent>
                {!details || details.students.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-6">No student details returned.</p>
                ) : (
                  <div className="space-y-3">
                    {details.students.map((student) => {
                      const ungradedCount = Object.values(student.manual_results).filter(m => m.score === null).length;
                      const totalManualCount = Object.keys(student.manual_results).length;
                      return (
                        <div
                          key={student.canvas_id}
                          className="rounded-lg border border-border p-4 hover:shadow-xs transition-shadow bg-card text-card-foreground"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                            <div className="space-y-0.5">
                              <p className="font-semibold text-foreground">{student.student_name}</p>
                              <p className="text-xs text-muted-foreground">
                                Canvas ID: {student.canvas_id} | File: {student.matched_file}
                              </p>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="flex items-center text-foreground gap-1 text-sm font-semibold mr-1">
                                <AwardIcon className="size-4 text-muted-foreground" />
                                {student.score} / {student.max_score} pts
                              </div>
                              <span
                                className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                                  student.status === "success"
                                    ? "bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300"
                                    : student.status === "failure"
                                      ? "bg-rose-100 dark:bg-rose-950/80 text-rose-800 dark:text-rose-300"
                                      : "bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300"
                                }`}
                              >
                                {student.status}
                              </span>
                              {totalManualCount > 0 && (
                                <span
                                  className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                                    ungradedCount > 0
                                      ? "bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                                      : "bg-muted text-foreground border border-border"
                                  }`}
                                >
                                  {ungradedCount > 0 ? `Ungraded (${ungradedCount})` : "Graded"}
                                </span>
                              )}
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => handleInspectStudent(student)}
                                className="text-xs h-7 px-2"
                              >
                                <EyeIcon className="size-3.5 mr-1" /> Inspect
                              </Button>
                            </div>
                          </div>

                          {student.feedback_preview && (
                            <div className="mt-3 rounded border border-slate-50 bg-slate-50 p-2.5 text-xs text-slate-600">
                              <span className="font-bold block text-slate-500 mb-1">Feedback Summary:</span>
                              <p className="line-clamp-2">{student.feedback_preview}</p>
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

        {/* Detailed Student Review Slide-out Sheet */}
        <Sheet
          open={isSheetOpen}
          onOpenChange={(open) => {
            if (
              !open &&
              isManualDraftDirty &&
              !window.confirm("Discard unsaved manual grading changes?")
            ) {
              return;
            }
            setIsSheetOpen(open);
            if (!open) {
              setSelectedCanvasId(null);
            }
          }}
        >
          <SheetContent className="sm:max-w-5xl w-[85vw] p-0 flex flex-col h-full bg-slate-900 border-slate-800 text-slate-100">
            <SheetHeader className="p-6 border-b border-slate-800 shrink-0">
              <div className="flex justify-between items-start">
                <div>
                  <SheetTitle className="text-xl font-bold text-slate-100">
                    {selectedStudent?.student_name}
                  </SheetTitle>
                  <SheetDescription className="text-xs text-slate-400 mt-1">
                    Canvas ID: {selectedStudent?.canvas_id} | Score: {selectedStudent?.score} / {selectedStudent?.max_score} pts
                  </SheetDescription>
                </div>
              </div>
            </SheetHeader>

            <Tabs defaultValue="feedback" className="flex-1 flex flex-col min-h-0">
              <div className="px-6 border-b border-slate-800 shrink-0">
                <TabsList className="bg-slate-950 border border-slate-800 text-slate-400">
                  <TabsTrigger value="feedback" className="data-[state=active]:bg-slate-800 data-[state=active]:text-slate-100">
                    Feedback Preview
                  </TabsTrigger>
                  <TabsTrigger value="code" className="data-[state=active]:bg-slate-800 data-[state=active]:text-slate-100">
                    Code Explorer
                  </TabsTrigger>
                  {selectedStudent && Object.keys(selectedStudent.manual_results).length > 0 && (
                    <TabsTrigger value="manual" className="data-[state=active]:bg-slate-800 data-[state=active]:text-slate-100">
                      Manual Grading
                    </TabsTrigger>
                  )}
                </TabsList>
              </div>

              <TabsContent value="feedback" className="flex-1 overflow-y-auto p-6 min-h-0">
                <div className="bg-card text-card-foreground p-6 rounded-lg shadow-xs border border-border overflow-y-auto max-h-[70vh]">
                  {selectedStudent?.feedback_html ? (
                    // feedback_html is generated server-side; staff-only view
                    <div dangerouslySetInnerHTML={{ __html: selectedStudent.feedback_html }} />
                  ) : (
                    <p className="text-muted-foreground italic">No feedback HTML summary available.</p>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="code" className="flex-1 flex min-h-0 data-[state=active]:flex">
                <div className="flex flex-1 min-h-0 divide-x divide-slate-800">
                  {/* Left Sidebar - File Tree */}
                  <div className="w-64 shrink-0 flex flex-col bg-slate-950/40 overflow-y-auto p-4 space-y-2">
                    <h5 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Submission Files</h5>
                    {isLoadingFiles ? (
                      <p className="text-xs text-slate-500 animate-pulse">Loading file list...</p>
                    ) : studentFiles.length === 0 ? (
                      <p className="text-xs text-slate-500 italic">No files found.</p>
                    ) : (
                      <div className="space-y-1">
                        {studentFiles.map((file) => {
                          const isSelected = selectedFilepath === file.filepath;
                          return (
                            <button
                              key={file.filepath}
                              type="button"
                              onClick={() => selectedStudent && handleSelectFile(selectedStudent.canvas_id, file)}
                              className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-left text-xs font-mono transition-colors ${
                                isSelected
                                  ? "bg-indigo-600 text-white"
                                  : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                              }`}
                            >
                              <FileIcon className="size-3.5 shrink-0" />
                              <span className="truncate" title={file.filepath}>{file.filepath}</span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Right Content - Monaco Editor */}
                  <div className="flex-1 flex flex-col min-h-0 bg-slate-950">
                    {selectedFilepath ? (
                      <div className="flex-1 flex flex-col min-h-0">
                        <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 flex justify-between items-center text-xs shrink-0">
                          <span className="font-mono text-slate-300 truncate">{selectedFilepath}</span>
                          <span className="text-slate-500 font-mono">
                            {selectedFile?.size_bytes} bytes
                          </span>
                        </div>

                        <div className="flex-1 min-h-0 relative">
                          {isLoadingContent ? (
                            <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 z-10">
                              <p className="text-xs text-slate-400 animate-pulse">Loading file contents...</p>
                            </div>
                          ) : contentError ? (
                            <div className="p-6 text-center text-red-400 text-xs">
                              {contentError}
                            </div>
                          ) : !selectedFile?.previewable ? (
                            <div className="p-6 text-center text-slate-500 text-xs italic">
                              Preview not available for binary or large files.
                            </div>
                          ) : (
                            <div className="w-full h-full">
                              <MonacoEditor
                                key={selectedFilepath}
                                height="100%"
                                width="100%"
                                defaultLanguage={languageFromFilename(selectedFilepath)}
                                defaultValue={fileContent || ""}
                                options={{ readOnly: true, minimap: { enabled: false } }}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center justify-center text-slate-500 text-xs italic">
                        Select a file from the explorer to preview code.
                      </div>
                    )}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="manual" className="flex-1 overflow-y-auto p-6 min-h-0">
                <div className="max-w-3xl mx-auto space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-100">Manual Rubric Grading</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Score each criterion and add optional student-facing feedback.
                    </p>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-slate-200">Automated results</h4>
                      <span className="text-xs font-mono text-slate-400">
                        {selectedStudent?.automated_score} / {selectedStudent?.automated_max_score}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {selectedStudent?.automated_results.map((item) => (
                        <div key={item.key} className="flex justify-between gap-3 text-xs">
                          <span className="text-slate-300">{item.label}</span>
                          <span className={item.passed ? "text-green-400" : "text-red-400"}>
                            {item.points_awarded} / {item.points}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-4">
                    {Object.entries(selectedStudent?.manual_results ?? {}).map(([key, item]) => {
                      const draft = manualGradesDraft[key] ?? { score: item.score, comments: item.comments || "" };
                      return (
                        <div key={key} className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="font-semibold text-slate-200 text-sm">{item.label}</span>
                            <div className="flex items-center gap-2">
                              <Input
                                type="number"
                                min={0}
                                max={item.points}
                                step={1}
                                value={draft.score ?? ""}
                                placeholder="—"
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                                  const raw = e.target.value;
                                  const score = raw === ""
                                    ? null
                                    : Number(raw);
                                  setManualGradesDraft((prev) => ({
                                    ...prev,
                                    [key]: { ...prev[key], score, comments: prev[key]?.comments ?? "" },
                                  }));
                                }}
                                className="w-20 bg-slate-900 border-slate-800 text-slate-100 font-mono text-center text-xs h-8"
                              />
                              <span className="text-xs text-slate-400">/ {item.points} pts</span>
                            </div>
                          </div>

                          <textarea
                            value={draft.comments}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                              setManualGradesDraft(prev => ({
                                ...prev,
                                [key]: { ...prev[key], comments: e.target.value }
                              }));
                            }}
                            placeholder="Feedback comments for this item..."
                            rows={2}
                            className="w-full rounded border border-slate-800 bg-slate-900 p-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none placeholder-slate-600"
                          />
                        </div>
                      );
                    })}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-200" htmlFor="overall-comment">
                      Overall student feedback
                    </label>
                    <textarea
                      id="overall-comment"
                      value={overallCommentDraft}
                      onChange={(event) => setOverallCommentDraft(event.target.value)}
                      placeholder="Optional feedback included in the final HTML report..."
                      rows={3}
                      className="w-full rounded border border-slate-800 bg-slate-900 p-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none placeholder-slate-600"
                    />
                  </div>

                  <div className="pt-2 flex justify-end gap-2">
                    <Button
                      type="button"
                      disabled={isSavingGrades}
                      variant="outline"
                      onClick={() => void handleSaveManualGrades(false)}
                      className="text-xs px-4 py-2"
                    >
                      {isSavingGrades ? "Saving..." : "Save"}
                    </Button>
                    <Button
                      type="button"
                      disabled={isSavingGrades}
                      onClick={() => void handleSaveManualGrades(true)}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-4 py-2"
                    >
                      {isSavingGrades ? "Saving..." : "Save & Next Ungraded"}
                    </Button>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  );
}
