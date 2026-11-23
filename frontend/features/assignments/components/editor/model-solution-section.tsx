"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  FileCodeIcon,
  UploadIcon,
  DownloadIcon,
  Trash2Icon,
  PlayIcon,
  CheckCircle2Icon,
  ShieldAlertIcon,
  FileTextIcon,
  FilePlusIcon,
  XCircleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";
import { apiClient } from "@/lib/api-client";
import { staffArtifactPath } from "@/features/staff/api";
import { makeUniqueKey, slugifyKey } from "@/lib/slugify";
import { isTextFilename, validateFilename } from "@/features/assignments/workspace/file-utils";
import VisualDiffViewer from "@/components/visual-diff-viewer";
import { Badge } from "@/components/ui/badge";

type TestCaseDetail = {
  nodeid?: string;
  outcome?: string;
  duration?: number;
  message?: string | null;
  actual?: string | null;
  expected?: string | null;
  your_value?: string | null;
  expected_value?: string | null;
  expected_input?: string | null;
};

type ValidationTestResult = {
  key: string;
  label: string;
  points: number;
  points_awarded: number;
  passed: boolean;
  extra_credit?: boolean;
  item_type?: string;
  marker?: string;
  actual?: string | null;
  expected?: string | null;
  your_value?: string | null;
  expected_value?: string | null;
  test_results?: TestCaseDetail[];
};

type ValidationStatus = {
  status: "idle" | "queue" | "run" | "success" | "failure";
  errors: string[];
  score: number;
  max_score: number;
  test_results?: ValidationTestResult[];
};

import { Label } from "@/components/ui/label";

interface ZipFileEntry {
  path: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  entry: any;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function cleanZipEntries(zipFiles: Record<string, any>): { name: string; entry: any }[] {
  const validEntries: ZipFileEntry[] = [];

  for (const [rawPath, entry] of Object.entries(zipFiles)) {
    if (entry.dir) continue;
    const normalized = rawPath.replace(/\\/g, "/").replace(/^\/+/, "");
    const parts = normalized.split("/");
    if (parts.some((p) => p.startsWith(".") || p === "__MACOSX" || p === "Thumbs.db")) {
      continue;
    }
    const filename = parts[parts.length - 1];
    if (!filename || filename.startsWith(".")) continue;
    validEntries.push({ path: normalized, entry });
  }

  // If all files share a common single root folder (e.g. "my_solution/file.py"), strip that root folder
  if (validEntries.length > 0) {
    const firstParts = validEntries[0].path.split("/");
    if (firstParts.length > 1) {
      const candidatePrefix = firstParts[0] + "/";
      const allSharePrefix = validEntries.every((e) => e.path.startsWith(candidatePrefix));
      if (allSharePrefix) {
        return validEntries.map((e) => ({
          name: e.path.slice(candidatePrefix.length).split("/").pop() || e.path,
          entry: e.entry,
        }));
      }
    }
  }

  return validEntries.map((e) => ({
    name: e.path.split("/").pop() || e.path,
    entry: e.entry,
  }));
}

export function ModelSolutionSection() {
  const {
    courseId,
    assignmentId,
    artifacts,
    refreshArtifacts,
    openCodeEditor,
    setErrorMessage,
    setSuccessMessage,
    entrypoint,
    dirty,
    saving,
    scoringItems,
  } = useAssignmentEditor();

  const [expandedDiffs, setExpandedDiffs] = useState<Record<string, boolean>>({});
  const toggleDiff = (key: string) => {
    setExpandedDiffs((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [newFilename, setNewFilename] = useState("");
  const [filenameError, setFilenameError] = useState<string | null>(null);

  const handleCreate = (event: React.FormEvent) => {
    event.preventDefault();
    const filename = newFilename.trim();
    const result = validateFilename(
      filename,
      artifacts.map((artifact) => artifact.display_filename || artifact.artifact_key),
    );
    if (!result.valid) {
      setFilenameError(result.error || "Invalid filename.");
      return;
    }
    if (!isTextFilename(filename)) {
      setFilenameError("Use a source or text file extension, such as .py, .cpp, .h, or .txt. Other file types can be uploaded.");
      return;
    }
    const key = makeUniqueKey(
      `solution_${slugifyKey(filename)}`,
      artifacts.map((artifact) => artifact.artifact_key),
    );
    setFilenameError(null);
    // A new file stays in the editor until Save; canceling creates no artifact.
    void openCodeEditor(key, "model_solution", filename, "");
  };

  // Preflight validation state
  const [validation, setValidation] = useState<ValidationStatus>({
    status: "idle",
    errors: [],
    score: 0,
    max_score: 0,
  });

  // Filter model solution artifacts
  const solutionArtifacts = artifacts.filter(
    (a) => a.artifact_type === "model_solution" || a.artifact_type === "support_file",
  );

  // Poll validation status if queued or running
  useEffect(() => {
    if (validation.status !== "queue" && validation.status !== "run") return;

    const checkStatus = async () => {
      try {
        const data = await apiClient.get<ValidationStatus>(
          `/staff/courses/${courseId}/assignments/${assignmentId}/validation-status`,
        );
        setValidation(data);
        if (data.status !== "queue" && data.status !== "run") {
          clearInterval(timer);
        }
      } catch (error) {
        clearInterval(timer);
        setValidation({
          status: "failure",
          errors: [`Could not check model solution status. ${error instanceof Error ? error.message : "Try testing again."}`],
          score: 0,
          max_score: 0,
        });
      }
    };

    const timer = setInterval(checkStatus, 1500);
    return () => clearInterval(timer);
  }, [validation.status, courseId, assignmentId]);

  const triggerValidation = async () => {
    if (dirty || saving) return;
    setValidation({
      status: "queue",
      errors: [],
      score: 0,
      max_score: 0,
    });

    try {
      await apiClient.post(
        `/staff/courses/${courseId}/assignments/${assignmentId}/validate-model-solution`,
        {},
      );
    } catch (err: unknown) {
      setValidation({
        status: "failure",
        errors: [
          err instanceof Error ? err.message : "Validation launch failed.",
        ],
        score: 0,
        max_score: 0,
      });
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFiles.length === 0) {
      setErrorMessage("Please select a solution file or ZIP archive to upload.");
      return;
    }

    setUploading(true);
    setErrorMessage(null);
    try {
      // 1. Expand any ZIP files among the selected files
      const rawExtractedFiles: File[] = [];

      for (const file of selectedFiles) {
        if (file.name.toLowerCase().endsWith(".zip")) {
          const jszipModule = await import("jszip");
          const JSZip = (jszipModule.default ?? jszipModule) as unknown as typeof import("jszip");
          const zip = await JSZip.loadAsync(file);

          const entries = cleanZipEntries(zip.files);
          for (const { name, entry } of entries) {
            const blob = await entry.async("blob");
            rawExtractedFiles.push(
              new File([blob], name, {
                type: blob.type || "application/octet-stream",
              })
            );
          }
        } else {
          rawExtractedFiles.push(file);
        }
      }

      if (rawExtractedFiles.length === 0) {
        throw new Error("No valid solution files found in the selected upload.");
      }

      // Deduplicate by filename (later file in list wins)
      const fileMap = new Map<string, File>();
      for (const file of rawExtractedFiles) {
        fileMap.set(file.name, file);
      }
      const filesToUpload = Array.from(fileMap.values());

      const suiteFilenames = new Set(
        artifacts
          .filter((artifact) => artifact.artifact_type === "pytest_file" || artifact.artifact_type === "test_file")
          .map((artifact) => artifact.display_filename?.toLowerCase()),
      );
      for (const file of filesToUpload) {
        if (suiteFilenames.has(file.name.toLowerCase())) {
          throw new Error(`Cannot overwrite test suite '${file.name}'. Edit tests on Tests & Rubric.`);
        }
      }

      // 2. Validate and upload each file
      let uploadedCount = 0;
      const currentArtifacts = [...artifacts];

      for (const file of filesToUpload) {
        const filename = file.name;
        const existing = currentArtifacts.find((artifact) => artifact.display_filename === filename);
        const artifactKey = existing?.artifact_key || makeUniqueKey(
          `solution_${slugifyKey(filename)}`,
          currentArtifacts.map((artifact) => artifact.artifact_key),
        );
        const artifactType = existing?.artifact_type || "model_solution";

        const formData = new FormData();
        formData.append("file", file);
        formData.append("artifact_key", artifactKey);
        formData.append("artifact_type", artifactType);

        await apiClient.postForm(
          `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
          formData,
        );

        if (!existing) {
          currentArtifacts.push({
            artifact_key: artifactKey,
            artifact_type: artifactType,
            display_filename: filename,
            size_bytes: file.size,
          });
        }
        uploadedCount++;
      }

      setSuccessMessage(
        uploadedCount === 1
          ? `Uploaded model solution file '${filesToUpload[0].name}' successfully.`
          : `Uploaded ${uploadedCount} model solution file(s) successfully.`
      );
      setSelectedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await refreshArtifacts();
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "Failed to upload model solution file(s).",
      );
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteSolution = async (key: string, filename: string) => {
    if (
      !confirm(
        `Are you sure you want to delete model solution file '${filename}'?`,
      )
    )
      return;
    try {
      await apiClient.delete(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${key}`,
      );
      setSuccessMessage(`Deleted '${filename}'.`);
      await refreshArtifacts();
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to delete solution file.",
      );
    }
  };

  const handleDownload = (key: string, filename: string) => {
    apiClient
      .download(staffArtifactPath(courseId, assignmentId, key), filename || key)
      .catch(() => setErrorMessage("Download failed."));
  };

  return (
    <div className="space-y-6">
      {/* Upload Model Solution Card */}
      <Card size="sm" className="gap-1.5 py-3">
        <CardHeader className="px-4 py-0">
          <CardTitle>Model Solution Files</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-4 py-0">
          <form onSubmit={handleCreate} className="space-y-2">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="grow space-y-1">
                <Label htmlFor="new-solution-filename" className="pl-0 text-xs">
                  New File Name
                </Label>
                <Input
                  id="new-solution-filename"
                  value={newFilename}
                  placeholder={entrypoint || "main.py"}
                  onChange={(event) => {
                    setNewFilename(event.target.value);
                    setFilenameError(null);
                  }}
                  aria-invalid={Boolean(filenameError)}
                  aria-describedby={filenameError ? "solution-filename-error" : undefined}
                />
              </div>
              <Button type="submit">
                <FilePlusIcon className="mr-1.5 h-4 w-4" /> Create File
              </Button>
            </div>
            {filenameError && (
              <p id="solution-filename-error" role="alert" className="text-xs text-destructive">
                {filenameError}
              </p>
            )}
          </form>
          <form
            onSubmit={handleUpload}
            className="flex flex-col sm:flex-row gap-3 items-end"
          >
            <div className="space-y-1 grow">
              <Label htmlFor="solution-upload" className="pl-0 text-xs">
                Upload Solution Files or ZIP Archive
              </Label>
              <Input
                id="solution-upload"
                type="file"
                multiple
                ref={fileInputRef}
                aria-label="Upload Solution File"
                onChange={(e) => setSelectedFiles(Array.from(e.target.files || []))}
                className="text-xs cursor-pointer"
              />
            </div>
            <Button type="submit" disabled={uploading}>
              <UploadIcon className="w-4 h-4 mr-1.5" />
              {uploading
                ? "Uploading..."
                : selectedFiles.length > 1
                ? `Upload ${selectedFiles.length} Files`
                : "Upload File"}
            </Button>
          </form>

          {/* Solution Files List */}
          <div className="space-y-3 pt-2">
            {solutionArtifacts.map((art) => {
              const displayFilename = art.display_filename || art.artifact_key;
              const isTextFile = isTextFilename(displayFilename);

              return (
                <div
                  key={art.artifact_key}
                  className="flex items-center justify-between p-3.5 bg-card rounded-lg border border-border text-card-foreground"
                >
                  <div className="flex items-center gap-3">
                    <FileCodeIcon className="w-5 h-5 text-primary shrink-0" />
                    <div>
                      <div className="font-mono text-sm font-bold text-foreground">
                        {displayFilename}
                      </div>
                      {art.size_bytes !== null &&
                        art.size_bytes !== undefined && (
                          <div className="text-xs text-muted-foreground font-mono">
                            {Math.round(art.size_bytes / 1024)} KB
                          </div>
                        )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {isTextFile && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          openCodeEditor(
                            art.artifact_key,
                            art.artifact_type,
                            displayFilename,
                          )
                        }
                      >
                        <FileTextIcon className="w-4 h-4 mr-1" /> Edit Code
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        handleDownload(art.artifact_key, displayFilename)
                      }
                    >
                      <DownloadIcon className="w-4 h-4 mr-1" /> Download
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label="Delete solution file"
                      onClick={() =>
                        handleDeleteSolution(art.artifact_key, displayFilename)
                      }
                    >
                      <Trash2Icon className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              );
            })}

            {solutionArtifacts.length === 0 && (
              <p className="rounded-lg border border-dashed border-border px-3 py-3 text-center text-xs text-muted-foreground">
                No model solution files yet.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Model Solution Validation Embedded at Bottom */}
      <Card size="sm" className="gap-1.5 py-3">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 px-4 py-0">
          <CardTitle>Verify Model Solution</CardTitle>
          <Button
            onClick={triggerValidation}
            disabled={
              dirty || saving || validation.status === "queue" || validation.status === "run"
            }
            size="sm"
          >
            <PlayIcon className="w-4 h-4 mr-1.5" />
            {validation.status === "queue" || validation.status === "run"
              ? "Validating..."
              : "Test Model Solution"}
          </Button>
        </CardHeader>
        <CardContent className="px-4 py-0">
          {(dirty || saving) && (
            <p className="text-xs text-muted-foreground">
              Save assignment changes before testing the model solution.
            </p>
          )}
          {validation.status !== "idle" && (
            <div className="space-y-3 rounded-lg border border-border bg-card p-3 text-card-foreground">
              <div className="flex items-center justify-end">
                <span
                  className={`rounded-full px-3 py-1 text-xs font-bold uppercase ${
                    validation.status === "success"
                      ? "bg-success/15 text-success"
                      : validation.status === "failure"
                        ? "bg-destructive/15 text-destructive"
                        : "bg-warning/15 text-warning-foreground animate-pulse"
                  }`}
                >
                  {validation.status}
                </span>
              </div>

              {validation.status === "success" && (
                <div className="flex items-center text-success gap-2 text-xs font-semibold p-3 bg-success/10 rounded-lg border border-success/20">
                  <CheckCircle2Icon className="w-5 h-5 text-success shrink-0" />
                  <span>
                    Parity Confirmed. Model Solution scored {validation.score} /{" "}
                    {validation.max_score} pts.
                  </span>
                </div>
              )}

              {validation.status === "failure" && (
                <div className="space-y-2 p-3 bg-destructive/10 rounded-lg border border-destructive/30 text-destructive">
                  <div className="flex items-center gap-2 text-xs font-semibold">
                    <ShieldAlertIcon className="w-5 h-5 text-destructive shrink-0" />
                    <span>Model solution errors found:</span>
                  </div>
                  <ul className="list-disc pl-5 text-xs font-mono space-y-1">
                    {validation.errors.map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              {validation.test_results && validation.test_results.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-border">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Comparison Results Preview
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {validation.test_results.filter((t) => t.passed).length} of{" "}
                      {validation.test_results.length} passed
                    </span>
                  </div>

                  <div className="space-y-2">
                    {validation.test_results.map((testRes) => {
                      const itemConfig = scoringItems.find((s) => s.key === testRes.key);
                      const mode = itemConfig?.comparison_mode || "normalized";
                      const tol = itemConfig?.tolerance;
                      const isExpanded = Boolean(expandedDiffs[testRes.key]);

                      const actualOutput =
                        testRes.actual ??
                        testRes.your_value ??
                        testRes.test_results?.[0]?.actual ??
                        testRes.test_results?.[0]?.your_value ??
                        null;
                      const expectedOutput =
                        testRes.expected ??
                        testRes.expected_value ??
                        testRes.test_results?.[0]?.expected ??
                        testRes.test_results?.[0]?.expected_value ??
                        (itemConfig?.outputs ? itemConfig.outputs.join("\n") : null);

                      const hasDiffData = actualOutput !== null || expectedOutput !== null;

                      let modeBadgeLabel = "Normalized";
                      if (mode === "exact") modeBadgeLabel = "Exact";
                      else if (mode === "numeric_tolerance") {
                        modeBadgeLabel = tol !== null && tol !== undefined ? `Numeric (±${tol})` : "Numeric (±1e-4)";
                      } else if (mode === "regex") {
                        modeBadgeLabel = "Regex";
                      }

                      return (
                        <div
                          key={testRes.key}
                          className="rounded-lg border border-border bg-card/60 p-2.5 text-xs text-card-foreground space-y-2"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2 min-w-0">
                              {testRes.passed ? (
                                <CheckCircle2Icon className="w-4 h-4 text-success shrink-0" />
                              ) : (
                                <XCircleIcon className="w-4 h-4 text-destructive shrink-0" />
                              )}
                              <span className="font-semibold text-foreground truncate">
                                {testRes.label || testRes.key}
                              </span>
                              <Badge
                                variant={
                                  mode === "exact"
                                    ? "secondary"
                                    : mode === "numeric_tolerance"
                                      ? "info"
                                      : mode === "regex"
                                        ? "warning"
                                        : "outline"
                                }
                                className="text-[10px] px-1.5 py-0"
                              >
                                {modeBadgeLabel}
                              </Badge>
                            </div>

                            <div className="flex items-center gap-2 shrink-0">
                              <span className="font-mono text-xs">
                                {testRes.points_awarded} / {testRes.points} pts
                              </span>
                              {hasDiffData && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 px-1.5 text-xs text-muted-foreground hover:text-foreground"
                                  onClick={() => toggleDiff(testRes.key)}
                                  aria-label={isExpanded ? `Hide diff for ${testRes.key}` : `View diff for ${testRes.key}`}
                                >
                                  {isExpanded ? (
                                    <>
                                      <ChevronDownIcon className="w-3.5 h-3.5 mr-1" /> Hide Diff
                                    </>
                                  ) : (
                                    <>
                                      <ChevronRightIcon className="w-3.5 h-3.5 mr-1" /> View Diff
                                    </>
                                  )}
                                </Button>
                              )}
                            </div>
                          </div>

                          {isExpanded && hasDiffData && (
                            <div className="mt-2 pt-2 border-t border-border">
                              <VisualDiffViewer expected={expectedOutput} actual={actualOutput} />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
