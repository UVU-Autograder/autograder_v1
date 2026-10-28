"use client";

import { use, useState, useEffect } from "react";
import {
  UploadIcon,
  TrashIcon,
  DownloadIcon,
  XIcon,
  ShieldAlertIcon,
  SaveIcon,
} from "lucide-react";
import { AdminPageHeader } from "@/components/admin-page-header";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { PageEmpty, PageLoading } from "@/components/page-status";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api-client";
import { staffArtifactPath } from "@/features/staff/api";
import MonacoEditor from "@/components/monaco-editor";

type ArtifactType = "pytest_file" | "model_solution" | "support_file";

type ArtifactMetadata = {
  artifact_key: string;
  artifact_type: ArtifactType;
  display_filename: string | null;
  size_bytes: number | null;
};

type ArtifactListResponse = {
  course_id: string;
  assignment_id: string;
  artifacts: ArtifactMetadata[];
};

type PageProps = {
  params: Promise<{ courseId: string; assignmentId: string }>;
};

function typeLabel(type: ArtifactType): string {
  switch (type) {
    case "pytest_file":
      return "Tests";
    case "model_solution":
      return "Model solution";
    case "support_file":
      return "Support file";
  }
}

function defaultKeyForType(type: ArtifactType): string {
  if (type === "support_file") return "";
  return type;
}

export default function ArtifactsPage({ params }: PageProps) {
  const { courseId, assignmentId } = use(params);
  const [artifacts, setArtifacts] = useState<ArtifactMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);
  const [isLoadingCode, setIsLoadingCode] = useState(false);
  const [editArtifactKey, setEditArtifactKey] = useState("");
  const [editArtifactType, setEditArtifactType] = useState("");
  const [editArtifactFilename, setEditArtifactFilename] = useState("");
  const [editCodeText, setEditCodeText] = useState("");
  const [isSavingCode, setIsSavingCode] = useState(false);
  const [codeEditorError, setCodeEditorError] = useState<string | null>(null);

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [artifactKey, setArtifactKey] = useState("pytest_file");
  const [artifactType, setArtifactType] = useState<ArtifactType>("pytest_file");

  useEffect(() => {
    let active = true;
    apiClient
      .get<ArtifactListResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
      )
      .then((data) => {
        if (active) {
          setArtifacts(data.artifacts);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load files.");
          setIsLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [courseId, assignmentId]);

  const reloadArtifacts = async () => {
    try {
      const data = await apiClient.get<ArtifactListResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
      );
      setArtifacts(data.artifacts);
    } catch {
      // ignore reload errors
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setError("Please select a file to upload.");
      return;
    }
    const key = artifactKey.trim() || defaultKeyForType(artifactType);
    if (!key) {
      setError("Please specify a file key for support files.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("artifact_key", key);
    formData.append("artifact_type", artifactType);

    try {
      await apiClient.postForm(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
        formData,
      );
      setSuccess(`Uploaded ${uploadFile.name}.`);
      setUploadFile(null);
      if (artifactType === "support_file") setArtifactKey("");
      await reloadArtifacts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (key: string) => {
    if (!confirm(`Delete '${key}'?`)) return;

    setError(null);
    setSuccess(null);
    try {
      await apiClient.delete(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${key}`,
      );
      setSuccess(`Deleted '${key}'.`);
      await reloadArtifacts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deletion failed.");
    }
  };

  const handleDownload = async (key: string, filename: string | null) => {
    setError(null);
    try {
      await apiClient.download(
        staffArtifactPath(courseId, assignmentId, key),
        filename || key,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed.");
    }
  };

  const openCodeEditor = async (key: string, type: string, filename: string) => {
    setError(null);
    setCodeEditorError(null);
    setEditArtifactKey(key);
    setEditArtifactType(type);
    setEditArtifactFilename(filename);
    setEditCodeText("");
    setIsCodeModalOpen(true);
    setIsLoadingCode(true);
    setIsSavingCode(false);

    try {
      const text = await apiClient.getText(
        staffArtifactPath(courseId, assignmentId, key),
      );
      setEditCodeText(text);
      setIsLoadingCode(false);
    } catch (err) {
      setCodeEditorError(
        err instanceof Error ? err.message : "Failed to load file.",
      );
      setIsLoadingCode(false);
    }
  };

  const saveCodeChanges = async () => {
    if (!editArtifactKey) return;
    setIsSavingCode(true);
    setCodeEditorError(null);

    const file = new File([editCodeText], editArtifactFilename, {
      type: "text/plain",
    });
    const formData = new FormData();
    formData.append("file", file);
    formData.append("artifact_key", editArtifactKey);
    formData.append("artifact_type", editArtifactType);

    try {
      await apiClient.postForm(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
        formData,
      );
      setIsCodeModalOpen(false);
      setSuccess(`Saved ${editArtifactFilename}.`);
      await reloadArtifacts();
    } catch (err) {
      setCodeEditorError(
        err instanceof Error ? err.message : "Failed to save changes.",
      );
    } finally {
      setIsSavingCode(false);
    }
  };

  if (isLoading) {
    return <PageLoading className="h-screen">Loading files...</PageLoading>;
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pt-8 pb-12">
      <Breadcrumbs
        items={[
          { label: "Courses", href: "/staff/courses" },
          { label: "Assignments", href: `/staff/courses/${courseId}/assignments` },
          {
            label: assignmentId,
            href: `/staff/courses/${courseId}/assignments/${assignmentId}`,
          },
          { label: "Files" },
        ]}
      />

      <AdminPageHeader
        title="Files"
        description="Test suites, model solutions, and support files for this assignment."
      />

      {error && (
        <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded-md border border-success/30 bg-success/10 p-3 text-sm text-success">
          {success}
        </div>
      )}

      <section className="mb-8 space-y-3">
        <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
          Upload
        </h2>
        <form
          onSubmit={handleUpload}
          className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end"
        >
          <div className="space-y-1 sm:w-44">
            <label className="text-xs font-semibold text-muted-foreground uppercase">
              Type
            </label>
            <select
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
              value={artifactType}
              onChange={(e) => {
                const val = e.target.value as ArtifactType;
                setArtifactType(val);
                setArtifactKey(defaultKeyForType(val));
              }}
            >
              <option value="pytest_file">Tests</option>
              <option value="model_solution">Model solution</option>
              <option value="support_file">Support file</option>
            </select>
          </div>

          {artifactType === "support_file" && (
            <div className="space-y-1 sm:w-40">
              <label className="text-xs font-semibold text-muted-foreground uppercase">
                Key
              </label>
              <Input
                placeholder="e.g. helpers"
                required
                value={artifactKey}
                onChange={(e) => setArtifactKey(e.target.value)}
              />
            </div>
          )}

          <div className="min-w-0 flex-1 space-y-1">
            <label className="text-xs font-semibold text-muted-foreground uppercase">
              File
            </label>
            <input
              type="file"
              className="w-full text-xs text-muted-foreground file:mr-2 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-foreground hover:file:bg-muted/80"
              required
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            />
          </div>

          <Button type="submit" disabled={isUploading}>
            <UploadIcon className="mr-1.5 size-4" />
            {isUploading ? "Uploading..." : "Upload"}
          </Button>
        </form>
      </section>

      <section className="space-y-2">
        <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
          Uploaded files
        </h2>
        {artifacts.length === 0 ? (
          <PageEmpty className="py-8">No files uploaded yet.</PageEmpty>
        ) : (
          <ul className="divide-y divide-border border-y border-border">
            {artifacts.map((art) => (
              <li
                key={art.artifact_key}
                className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0 px-1">
                  <p className="truncate text-sm font-medium text-foreground">
                    {art.display_filename || art.artifact_key}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {typeLabel(art.artifact_type)}
                    {art.artifact_type === "support_file"
                      ? ` · ${art.artifact_key}`
                      : ""}
                  </p>
                </div>
                <div className="flex shrink-0 gap-1 px-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      openCodeEditor(
                        art.artifact_key,
                        art.artifact_type,
                        art.display_filename || art.artifact_key,
                      )
                    }
                  >
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      handleDownload(art.artifact_key, art.display_filename)
                    }
                  >
                    <DownloadIcon className="size-4" />
                    <span className="sr-only">Download</span>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:bg-destructive/10"
                    onClick={() => handleDelete(art.artifact_key)}
                  >
                    <TrashIcon className="size-4" />
                    <span className="sr-only">Delete</span>
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {isCodeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="flex h-[85vh] w-full max-w-5xl flex-col rounded-lg border border-border bg-card text-card-foreground shadow-xl">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div>
                <h3 className="text-sm font-semibold text-foreground">
                  Edit {editArtifactFilename}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsCodeModalOpen(false)}
                className="cursor-pointer text-muted-foreground hover:text-foreground"
              >
                <XIcon className="size-5" />
              </button>
            </div>

            {codeEditorError && (
              <div className="flex items-center gap-2 border-b border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
                <ShieldAlertIcon className="size-4 shrink-0" />
                <span>{codeEditorError}</span>
              </div>
            )}

            <div className="relative flex grow items-center justify-center overflow-hidden bg-muted">
              {isLoadingCode ? (
                <p className="text-xs text-muted-foreground">Loading file…</p>
              ) : (
                <MonacoEditor
                  height="100%"
                  width="100%"
                  defaultLanguage={
                    editArtifactFilename.endsWith(".py")
                      ? "python"
                      : editArtifactFilename.endsWith(".json")
                        ? "json"
                        : "plaintext"
                  }
                  defaultValue={editCodeText}
                  onChange={(val) => setEditCodeText(val || "")}
                />
              )}
            </div>

            <div className="flex justify-end gap-2 border-t border-border px-4 py-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCodeModalOpen(false)}
                disabled={isSavingCode}
              >
                Cancel
              </Button>
              <Button size="sm" onClick={saveCodeChanges} disabled={isSavingCode}>
                <SaveIcon className="mr-1.5 size-4" />
                {isSavingCode ? "Saving..." : "Save"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
