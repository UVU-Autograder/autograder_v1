"use client";

import { use, useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeftIcon, UploadIcon, TrashIcon, DownloadIcon, FileIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import { staffArtifactPath } from "@/features/staff/api";

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

  // Form states for new upload
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [artifactKey, setArtifactKey] = useState("");
  const [artifactType, setArtifactType] = useState<"pytest_file" | "model_solution" | "support_file">("pytest_file");

  const fetchArtifacts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<ArtifactListResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`
      );
      setArtifacts(data.artifacts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load artifacts.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    Promise.resolve().then(() => {
      fetchArtifacts();
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId, assignmentId]);

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
      fetchArtifacts();
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
      fetchArtifacts();
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

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">Loading artifacts...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 space-y-1">
          <Button variant="ghost" size="sm" className="-ml-3" asChild>
            <Link href={`/staff/courses/${courseId}/assignments/${assignmentId}/setup`}>
              <ArrowLeftIcon className="mr-1 size-4" /> Back to setup wizard
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Grading Assets</h1>
          <p className="text-slate-500">Upload and manage test suites or reference solutions.</p>
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
                    <label className="text-xs font-semibold text-slate-500">Asset Type</label>
                    <select
                      className="w-full rounded-md border border-slate-200 p-2 text-sm focus:border-indigo-500"
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
                    <label className="text-xs font-semibold text-slate-500">Unique Key</label>
                    <Input
                      placeholder="e.g. pytest_file"
                      required
                      value={artifactKey}
                      onChange={(e) => setArtifactKey(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-slate-500">File</label>
                    <input
                      type="file"
                      className="w-full text-xs text-slate-500 file:mr-2 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-slate-700 hover:file:bg-slate-200"
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
                  <p className="text-sm text-slate-400 text-center py-6">No assets uploaded yet.</p>
                ) : (
                  <div className="space-y-3">
                    {artifacts.map((art) => (
                      <div
                        key={art.artifact_key}
                        className="flex items-center justify-between rounded-lg border border-slate-100 p-3 hover:bg-slate-50"
                      >
                        <div className="flex items-center space-x-3">
                          <FileIcon className="size-8 text-slate-400" />
                          <div className="min-w-0">
                            <p className="truncate text-sm font-semibold text-slate-700">
                              {art.display_filename || art.artifact_key}
                            </p>
                            <p className="text-xs text-slate-400">
                              Key: {art.artifact_key} | Type: {art.artifact_type}
                            </p>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() =>
                              handleDownload(art.artifact_key, art.display_filename)
                            }
                          >
                            <DownloadIcon className="size-4 text-slate-600" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(art.artifact_key)}
                          >
                            <TrashIcon className="size-4 text-red-500" />
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
    </div>
  );
}
