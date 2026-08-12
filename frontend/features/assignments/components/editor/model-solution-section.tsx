"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
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
} from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";
import { apiClient } from "@/lib/api-client";
import { staffArtifactPath } from "@/features/staff/api";

type ValidationStatus = {
  status: "idle" | "queue" | "run" | "success" | "failure";
  errors: string[];
  score: number;
  max_score: number;
};

export function ModelSolutionSection() {
  const {
    courseId,
    assignmentId,
    artifacts,
    refreshArtifacts,
    openCodeEditor,
    setErrorMessage,
    setSuccessMessage,
  } = useAssignmentEditor();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

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
      } catch {
        clearInterval(timer);
      }
    };

    const timer = setInterval(checkStatus, 1500);
    return () => clearInterval(timer);
  }, [validation.status, courseId, assignmentId]);

  const triggerValidation = async () => {
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
      setErrorMessage("Please select a file or ZIP archive to upload.");
      return;
    }

    setUploading(true);
    setErrorMessage(null);
    try {
      const filename = selectedFile.name;
      const baseKey = filename
        .replace(/\.[^/.]+$/, "")
        .replace(/[^a-zA-Z0-9_]/g, "_");
      const artifactKey = filename.endsWith(".zip")
        ? `solution_archive_${baseKey}`
        : `solution_${baseKey}`;

      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("artifact_key", artifactKey);
      formData.append("artifact_type", "model_solution");

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
      <Card>
        <CardHeader>
          <CardTitle>Model Solution Files</CardTitle>
          <CardDescription>
            Attach single Python scripts or a multi-file `.zip` archive
            containing your reference solution.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <form
            onSubmit={handleUpload}
            className="flex flex-col sm:flex-row gap-3 items-end"
          >
            <div className="space-y-1 grow">
              <label className="text-xs font-semibold text-slate-700">
                Upload Solution File or ZIP Archive
              </label>
              <Input
                type="file"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="text-xs cursor-pointer bg-white"
              />
            </div>
            <Button type="submit" disabled={uploading}>
              <UploadIcon className="w-4 h-4 mr-1.5" />
              {uploading ? "Uploading..." : "Upload File"}
            </Button>
          </form>

          {/* Solution Files List */}
          <div className="space-y-3 pt-2">
            {solutionArtifacts.map((art) => {
              const displayFilename = art.display_filename || art.artifact_key;
              const isTextFile =
                displayFilename.endsWith(".py") ||
                displayFilename.endsWith(".json") ||
                displayFilename.endsWith(".txt") ||
                displayFilename.endsWith(".md");

              return (
                <div
                  key={art.artifact_key}
                  className="flex items-center justify-between p-3.5 bg-stone-50 rounded-lg border border-stone-200"
                >
                  <div className="flex items-center gap-3">
                    <FileCodeIcon className="w-5 h-5 text-indigo-600 shrink-0" />
                    <div>
                      <div className="font-mono text-sm font-bold text-slate-900">
                        {displayFilename}
                      </div>
                      {art.size_bytes !== null &&
                        art.size_bytes !== undefined && (
                          <div className="text-xs text-stone-500 font-mono">
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
                            "model_solution",
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
                      onClick={() =>
                        handleDeleteSolution(art.artifact_key, displayFilename)
                      }
                    >
                      <Trash2Icon className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              );
            })}

            {solutionArtifacts.length === 0 && (
              <p className="text-xs text-stone-400 italic p-6 text-center border border-dashed rounded-lg">
                No model solution files attached yet. Upload a Python solution
                script or ZIP archive above.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Preflight Validation Embedded at Bottom */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Model Solution Validation</CardTitle>
            <CardDescription>
              Validate your model solution files against the test suite.
            </CardDescription>
          </div>
          <Button
            onClick={triggerValidation}
            disabled={
              validation.status === "queue" || validation.status === "run"
            }
            size="sm"
          >
            <PlayIcon className="w-4 h-4 mr-1.5" />
            {validation.status === "queue" || validation.status === "run"
              ? "Validating..."
              : "Run Preflight Validation"}
          </Button>
        </CardHeader>
        <CardContent>
          {validation.status !== "idle" && (
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-slate-900 text-sm">
                  Validation Run Status
                </h4>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-bold uppercase ${
                    validation.status === "success"
                      ? "bg-emerald-100 text-emerald-800"
                      : validation.status === "failure"
                        ? "bg-red-100 text-red-800"
                        : "bg-amber-100 text-amber-800 animate-pulse"
                  }`}
                >
                  {validation.status}
                </span>
              </div>

              {(validation.status === "queue" ||
                validation.status === "run") && (
                <p className="text-xs text-slate-500 animate-pulse font-mono">
                  Executing model solution against tests.py in sandbox
                  container...
                </p>
              )}

              {validation.status === "success" && (
                <div className="flex items-center text-emerald-700 gap-2 text-xs font-semibold p-3 bg-emerald-50 rounded-lg">
                  <CheckCircle2Icon className="w-5 h-5 text-emerald-600 shrink-0" />
                  <span>
                    Parity Confirmed. Model Solution scored {validation.score} /{" "}
                    {validation.max_score} pts.
                  </span>
                </div>
              )}

              {validation.status === "failure" && (
                <div className="space-y-2 p-3 bg-red-50 rounded-lg border border-red-200">
                  <div className="flex items-center text-red-700 gap-2 text-xs font-semibold">
                    <ShieldAlertIcon className="w-5 h-5 text-red-600 shrink-0" />
                    <span>Preflight validation errors found:</span>
                  </div>
                  <ul className="list-disc pl-5 text-xs text-red-800 font-mono space-y-1">
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
