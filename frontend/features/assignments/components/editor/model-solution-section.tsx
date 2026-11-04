"use client";

import React, { useState, useEffect } from "react";
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
} from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";
import { apiClient } from "@/lib/api-client";
import { staffArtifactPath } from "@/features/staff/api";
import { makeUniqueKey, slugifyKey } from "@/lib/slugify";
import { isTextFilename, validateFilename } from "@/features/assignments/workspace/file-utils";

type ValidationStatus = {
  status: "idle" | "queue" | "run" | "success" | "failure";
  errors: string[];
  score: number;
  max_score: number;
};

import { Label } from "@/components/ui/label";

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
  } = useAssignmentEditor();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
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
    (a) =>
      a.artifact_type === "model_solution" ||
      (a.artifact_key !== "assignment_tests" &&
        a.artifact_type !== "pytest_file"),
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
    if (!selectedFile) {
      setErrorMessage("Please select a solution file to upload.");
      return;
    }
    if (selectedFile.name.toLowerCase().endsWith(".zip")) {
      setErrorMessage("ZIP model solution uploads are not supported. Upload individual solution files instead.");
      return;
    }

    setUploading(true);
    setErrorMessage(null);
    try {
      const filename = selectedFile.name;
      const existing = artifacts.find((artifact) => artifact.display_filename === filename);
      if (existing?.artifact_type === "pytest_file") {
        throw new Error("Edit the test suite on Tests & Rubric.");
      }
      const artifactKey = existing?.artifact_key || makeUniqueKey(
        `solution_${slugifyKey(filename)}`,
        artifacts.map((artifact) => artifact.artifact_key),
      );

      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("artifact_key", artifactKey);
      formData.append("artifact_type", existing?.artifact_type || "model_solution");

      await apiClient.postForm(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
        formData,
      );
      setSuccessMessage(
        `Uploaded model solution file '${filename}' successfully.`,
      );
      setSelectedFile(null);
      await refreshArtifacts();
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "Failed to upload model solution file.",
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
            <p className="text-xs text-muted-foreground">
              Create a file to write your solution here, or upload existing files below. Save in the editor to keep your changes.
            </p>
          </form>
          <form
            onSubmit={handleUpload}
            className="flex flex-col sm:flex-row gap-3 items-end"
          >
            <div className="space-y-1 grow">
              <Label htmlFor="solution-upload" className="pl-0 text-xs">
                Upload Solution File
              </Label>
              <Input
                id="solution-upload"
                type="file"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="text-xs cursor-pointer"
              />
            </div>
            <Button type="submit" disabled={uploading}>
              <UploadIcon className="w-4 h-4 mr-1.5" />
              {uploading ? "Uploading..." : "Upload File"}
            </Button>
          </form>
          <p className="text-xs text-muted-foreground">
            Upload files individually. ZIP archives are not supported.
          </p>

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
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
