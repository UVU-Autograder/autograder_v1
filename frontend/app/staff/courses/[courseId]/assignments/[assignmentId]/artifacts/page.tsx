"use client";

import { use, useState, useEffect } from "react";
import { UploadIcon, TrashIcon, DownloadIcon, FileIcon, EditIcon, XIcon, ShieldAlertIcon, SaveIcon, FileTextIcon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import { staffArtifactPath } from "@/features/staff/api";
import MonacoEditor from "@/components/monaco-editor";

type ArtifactMetadata = {
  artifact_key: string;
  artifact_type: "pytest_file" | "model_solution" | "support_file";
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

export default function ArtifactsPage({ params }: PageProps) {
  const { courseId, assignmentId } = use(params);
  const [artifacts, setArtifacts] = useState<ArtifactMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Code Editor states
  const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);
  const [isLoadingCode, setIsLoadingCode] = useState(false);
  const [editArtifactKey, setEditArtifactKey] = useState("");
  const [editArtifactType, setEditArtifactType] = useState("");
  const [editArtifactFilename, setEditArtifactFilename] = useState("");
  const [editCodeText, setEditCodeText] = useState("");
  const [isSavingCode, setIsSavingCode] = useState(false);
  const [codeEditorError, setCodeEditorError] = useState<string | null>(null);

  // Form states for new upload
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [artifactKey, setArtifactKey] = useState("");
  const [artifactType, setArtifactType] = useState<"pytest_file" | "model_solution" | "support_file">("pytest_file");

  useEffect(() => {
    let active = true;
    apiClient
      .get<ArtifactListResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`
      )
      .then((data) => {
        if (active) {
          setArtifacts(data.artifacts);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load artifacts.");
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
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`
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
    if (!artifactKey.trim()) {
      setError("Please specify an artifact key.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("artifact_key", artifactKey.trim());
    formData.append("artifact_type", artifactType);

    try {
      await apiClient.postForm(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
        formData
      );
      setSuccess(`Artifact '${artifactKey}' uploaded successfully.`);
      setUploadFile(null);
      setArtifactKey("");
      await reloadArtifacts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (key: string) => {
    if (!confirm(`Are you sure you want to delete the artifact '${key}'?`)) return;

    setError(null);
    setSuccess(null);
    try {
      await apiClient.delete(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${key}`
      );
      setSuccess(`Artifact '${key}' deleted.`);
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
        filename || key
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed.");
    }
  };

  const fetchArtifactText = async (key: string): Promise<string> => {
    return apiClient.getText(staffArtifactPath(courseId, assignmentId, key));
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
      const text = await fetchArtifactText(key);
      setEditCodeText(text);
      setIsLoadingCode(false);
    } catch (err) {
      setCodeEditorError(err instanceof Error ? err.message : "Failed to load artifact code.");
      setIsLoadingCode(false);
    }
  };

  const saveCodeChanges = async () => {
    if (!editArtifactKey) return;
    setIsSavingCode(true);
    setCodeEditorError(null);

    const file = new File([editCodeText], editArtifactFilename, { type: "text/plain" });
    const formData = new FormData();
    formData.append("file", file);
    formData.append("artifact_key", editArtifactKey);
    formData.append("artifact_type", editArtifactType);

    try {
      await apiClient.postForm(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
        formData
      );
      setIsCodeModalOpen(false);
      setSuccess(`Code saved successfully for '${editArtifactFilename}'.`);
      await reloadArtifacts();
    } catch (err) {
      setCodeEditorError(err instanceof Error ? err.message : "Failed to save code changes.");
    } finally {
      setIsSavingCode(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground font-medium animate-pulse">Loading artifacts...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6 md:p-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 space-y-1">
          <BackLink href={`/staff/courses/${courseId}/assignments/${assignmentId}`} variant="compact">
            Back to assignment
          </BackLink>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Grading Assets</h1>
          <p className="text-muted-foreground">Upload and manage test suites or reference solutions.</p>
        </div>

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

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {/* Upload panel */}
          <div className="md:col-span-1">
            <Card>
              <form onSubmit={handleUpload}>
                <CardHeader>
                  <CardTitle className="text-lg">Upload Asset</CardTitle>
                  <CardDescription>Add a new pytest, model solution, or support file.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Asset Type</label>
                    <select
                      className="w-full rounded-md border border-input bg-background text-foreground p-2 text-sm focus:border-primary"
                      value={artifactType}
                      onChange={(e) => {
                        const val = e.target.value as "pytest_file" | "model_solution" | "support_file";
                        setArtifactType(val);
                        if (val === "pytest_file") setArtifactKey("pytest_file");
                        else if (val === "model_solution") setArtifactKey("model_solution");
                        else setArtifactKey("");
                      }}
                    >
                      <option value="pytest_file">Pytest File</option>
                      <option value="model_solution">Model Solution</option>
                      <option value="support_file">Support File</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Unique Key</label>
                    <Input
                      placeholder="e.g. pytest_file"
                      required
                      value={artifactKey}
                      onChange={(e) => setArtifactKey(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">File</label>
                    <input
                      type="file"
                      className="w-full text-xs text-muted-foreground file:mr-2 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-foreground hover:file:bg-muted/80"
                      required
                      onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    />
                  </div>
                </CardContent>
                <CardFooter>
                  <Button type="submit" className="w-full" disabled={isUploading}>
                    <UploadIcon className="mr-2 size-4" />
                    {isUploading ? "Uploading..." : "Upload File"}
                  </Button>
                </CardFooter>
              </form>
            </Card>
          </div>

          {/* List panel */}
          <div className="md:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Active Grading Artifacts</CardTitle>
                <CardDescription>Currently active files stored on the server.</CardDescription>
              </CardHeader>
              <CardContent>
                {artifacts.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-6">No assets uploaded yet.</p>
                ) : (
                  <div className="space-y-3">
                    {artifacts.map((art) => (
                      <div
                        key={art.artifact_key}
                        className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-muted/50 text-card-foreground"
                      >
                        <div className="flex items-center space-x-3">
                          <FileIcon className="size-8 text-muted-foreground" />
                          <div className="min-w-0">
                            <p className="truncate text-sm font-semibold text-foreground">
                              {art.display_filename || art.artifact_key}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Key: {art.artifact_key} | Type: {art.artifact_type}
                            </p>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() =>
                              openCodeEditor(art.artifact_key, art.artifact_type, art.display_filename || art.artifact_key)
                            }
                          >
                            <EditIcon className="size-4 text-primary" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() =>
                              handleDownload(art.artifact_key, art.display_filename)
                            }
                          >
                            <DownloadIcon className="size-4 text-muted-foreground" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(art.artifact_key)}
                          >
                            <TrashIcon className="size-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Code Editor Modal Overlay */}
      {isCodeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-card rounded-lg border border-border shadow-xl w-full max-w-5xl h-[85vh] flex flex-col text-card-foreground">
            <div className="p-4 border-b border-border flex justify-between items-center bg-muted/50 rounded-t-lg">
              <div className="flex items-center gap-2">
                <FileTextIcon className="size-5 text-primary animate-pulse" />
                <div>
                  <h3 className="font-bold text-foreground text-sm">Editing Grading Asset: {editArtifactFilename}</h3>
                  <p className="text-xs text-muted-foreground">Directly modify the asset content on the server.</p>
                </div>
              </div>
              <button type="button" onClick={() => setIsCodeModalOpen(false)} className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                <XIcon className="size-5" />
              </button>
            </div>

            {codeEditorError && (
              <div className="bg-destructive/10 text-destructive p-3 text-xs border-b border-destructive/30 flex items-center gap-2">
                <ShieldAlertIcon className="size-4 shrink-0" />
                <span>{codeEditorError}</span>
              </div>
            )}

            <div className="grow bg-muted overflow-hidden relative flex items-center justify-center">
              {isLoadingCode ? (
                <p className="text-xs text-muted-foreground animate-pulse font-mono">Fetching file content from server...</p>
              ) : (
                <MonacoEditor
                  height="100%"
                  width="100%"
                  defaultLanguage={editArtifactFilename.endsWith(".py") ? "python" : editArtifactFilename.endsWith(".json") ? "json" : "plaintext"}
                  defaultValue={editCodeText}
                  onChange={(val) => setEditCodeText(val || "")}
                />
              )}
            </div>

            <div className="p-4 border-t border-border flex justify-end gap-2 bg-muted/40 rounded-b-lg">
              <Button variant="outline" size="sm" onClick={() => setIsCodeModalOpen(false)} disabled={isSavingCode}>
                Cancel
              </Button>
              <Button size="sm" onClick={saveCodeChanges} disabled={isSavingCode}>
                <SaveIcon className="size-4 mr-1.5" />
                {isSavingCode ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
