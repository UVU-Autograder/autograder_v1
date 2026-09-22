"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Image from "next/image";
import { FileIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
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
import { apiClient } from "@/lib/api-client";
import { languageFromFilename } from "@/features/assignments/workspace/file-utils";
import {
  staffRunStudentFilesPath,
  staffRunStudentFileContentPath,
} from "@/features/staff/api";
import { hasUngradedManualItems } from "../lib/student-filter";
import type { StudentRunDetail, StudentFile, FilePreview } from "../types";

function buildManualGradesDraft(
  student: StudentRunDetail | null,
): Record<string, { score: number | null; comments: string }> {
  if (!student) return {};
  return Object.fromEntries(
    Object.entries(student.manual_results ?? {}).map(([key, item]) => [
      key,
      { score: item.score, comments: item.comments || "" },
    ]),
  );
}

function initialInspectTab(student: StudentRunDetail | null): string {
  if (!student) return "feedback";
  const manualCount = Object.keys(student.manual_results ?? {}).length;
  return manualCount > 0 && hasUngradedManualItems(student)
    ? "manual"
    : "feedback";
}

export interface StudentInspectDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  student: StudentRunDetail | null;
  courseId: string;
  assignmentId: string;
  runId: string;
  onSaveManualGrades: (
    canvasId: string,
    grades: Record<string, { score: number | null; comments: string }>,
    overallComment: string,
    saveAndNext: boolean,
  ) => Promise<void>;
  isSavingGrades: boolean;
}

export function StudentInspectDialog(props: StudentInspectDialogProps) {
  if (!props.isOpen || !props.student) return null;

  return (
    <StudentInspectDialogSession
      key={JSON.stringify([
        props.courseId,
        props.assignmentId,
        props.runId,
        props.student.canvas_id,
      ])}
      {...props}
      student={props.student}
    />
  );
}

function StudentInspectDialogSession({
  isOpen,
  onOpenChange,
  student,
  courseId,
  assignmentId,
  runId,
  onSaveManualGrades,
  isSavingGrades,
}: StudentInspectDialogProps & { student: StudentRunDetail }) {
  const canvasId = student.canvas_id;
  const [inspectTab, setInspectTab] = useState(() => initialInspectTab(student));
  const [studentFiles, setStudentFiles] = useState<StudentFile[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(true);
  const [selectedFilepath, setSelectedFilepath] = useState<string | null>(null);
  const [filePreview, setFilePreview] = useState<FilePreview | null>(null);
  const filePreviewCacheRef = React.useRef<Record<string, FilePreview>>({});
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [contentError, setContentError] = useState<string | null>(null);

  const [manualGradesDraft, setManualGradesDraft] = useState<
    Record<string, { score: number | null; comments: string }>
  >(() => buildManualGradesDraft(student));
  const [overallCommentDraft, setOverallCommentDraft] = useState(
    () => student?.overall_comment || "",
  );

  const isManualDraftDirty = useMemo(() => {
    if (!student) return false;
    const savedGrades = Object.fromEntries(
      Object.entries(student.manual_results ?? {}).map(([key, item]) => [
        key,
        { score: item.score, comments: item.comments || "" },
      ]),
    );
    return (
      JSON.stringify(manualGradesDraft) !== JSON.stringify(savedGrades) ||
      overallCommentDraft !== (student.overall_comment || "")
    );
  }, [manualGradesDraft, overallCommentDraft, student]);

  const loadFileContent = useCallback(
    async (canvasId: string, filepath: string) => {
      const cacheKey = `${canvasId}:${filepath}`;
      const cached = filePreviewCacheRef.current[cacheKey];
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
        filePreviewCacheRef.current[cacheKey] = preview;
      } catch (err) {
        setContentError(
          err instanceof Error ? err.message : "Failed to load file content.",
        );
      } finally {
        setIsLoadingContent(false);
      }
    },
    [courseId, assignmentId, runId],
  );

  const handleSelectFile = useCallback(
    (canvasId: string, file: StudentFile) => {
      setSelectedFilepath(file.filepath);
      setFilePreview(null);
      setContentError(null);
      if (!file.previewable) {
        setIsLoadingContent(false);
        return;
      }
      void loadFileContent(canvasId, file.filepath);
    },
    [loadFileContent],
  );

  useEffect(() => {
    let active = true;
    const loadStudentFiles = async () => {
      try {
        const data = await apiClient.get<{ files: StudentFile[] }>(
          staffRunStudentFilesPath(
            courseId,
            assignmentId,
            runId,
            canvasId,
          ),
        );
        if (!active) return;
        setStudentFiles(data.files);
        const firstTextFile = data.files.find(
          (file) => file.previewable && (file.preview_kind ?? "text") === "text",
        );
        const firstPreviewable =
          firstTextFile ?? data.files.find((file) => file.previewable);
        if (firstPreviewable) {
          handleSelectFile(canvasId, firstPreviewable);
        }
      } catch (err) {
        if (active) console.error("Failed to load student files", err);
      } finally {
        if (active) setIsLoadingFiles(false);
      }
    };
    void loadStudentFiles();

    return () => {
      active = false;
    };
  }, [canvasId, courseId, assignmentId, runId, handleSelectFile]);

  const selectedFile = useMemo(
    () =>
      studentFiles.find((file) => file.filepath === selectedFilepath) ?? null,
    [studentFiles, selectedFilepath],
  );

  const handleOpenChange = (open: boolean) => {
    if (
      !open &&
      isManualDraftDirty &&
      !window.confirm("Discard unsaved feedback or grading changes?")
    ) {
      return;
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="flex h-[min(90vh,56rem)] w-[min(96vw,72rem)] max-w-none flex-col gap-0 overflow-hidden p-0 sm:max-w-none">
        <DialogHeader className="shrink-0 border-b border-border p-6 pr-12">
          <DialogTitle className="text-xl font-bold text-foreground">
            {student?.student_name}
          </DialogTitle>
          <DialogDescription className="mt-1 text-xs text-muted-foreground">
            Canvas ID: {student?.canvas_id} | Score: {student?.score} /{" "}
            {student?.max_score} pts
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
              {student && Object.keys(student.manual_results ?? {}).length > 0 && (
                <TabsTrigger
                  value="manual"
                  className="relative data-[state=active]:bg-background data-[state=active]:text-foreground"
                >
                  Manual Grading
                  {hasUngradedManualItems(student) && (
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
              <div className="overflow-hidden rounded-lg border border-border bg-card p-2 text-card-foreground shadow-xs">
                {student?.feedback_html ? (
                  <iframe
                    srcDoc={student.feedback_html}
                    title={`Feedback Preview for ${student.student_name}`}
                    className="h-[480px] w-full rounded border-0 bg-background"
                    sandbox="allow-same-origin"
                  />
                ) : (
                  <p className="p-4 italic text-muted-foreground">
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
                    onClick={() => {
                      if (!student) return;
                      void onSaveManualGrades(
                        student.canvas_id,
                        manualGradesDraft,
                        overallCommentDraft,
                        false,
                      );
                    }}
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
                            student && handleSelectFile(student.canvas_id, file)
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
                  Score each criterion and add optional student-facing feedback.
                </p>
              </div>

              <div className="rounded-lg border border-border bg-card p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-foreground">
                    Automated results
                  </h4>
                  <span className="font-mono text-xs text-muted-foreground">
                    {student?.automated_score} / {student?.automated_max_score}
                  </span>
                </div>
                <div className="space-y-2">
                  {(student?.automated_results ?? []).map((item) => (
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
                {Object.entries(student?.manual_results ?? {}).map(
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
                                const score = raw === "" ? null : Number(raw);
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
                  onClick={() => {
                    if (!student) return;
                    void onSaveManualGrades(
                      student.canvas_id,
                      manualGradesDraft,
                      overallCommentDraft,
                      false,
                    );
                  }}
                  className="px-4 py-2 text-xs"
                >
                  {isSavingGrades ? "Saving..." : "Save"}
                </Button>
                <Button
                  type="button"
                  disabled={isSavingGrades}
                  onClick={() => {
                    if (!student) return;
                    void onSaveManualGrades(
                      student.canvas_id,
                      manualGradesDraft,
                      overallCommentDraft,
                      true,
                    );
                  }}
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
  );
}
