"use client";

import { use, useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeftIcon, PlayIcon, ClockIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";

type RunSummary = {
  id: number;
  workflow_type: string;
  status: string;
  total_submission_count: number;
  success_count: number;
  warning_count: number;
  failure_count: number;
  timeout_count: number;
  created_at: string;
};

type RunSummaryListResponse = {
  runs: RunSummary[];
};

type IngestionResponse = {
  run_id: string;
  status: string;
  workflow_type: string;
  total_submission_count: number;
  created_at: string;
};

type RunStatusResponse = {
  run_id: string;
  state: "queue" | "run" | "complete" | "failure";
  queue_position: number | null;
  eta_band: string | null;
  message: string | null;
};

type PageProps = {
  params: Promise<{ courseId: string; assignmentId: string }>;
};

export default function RunsPage({ params }: PageProps) {
  const { courseId, assignmentId } = use(params);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [activeStatus, setActiveStatus] = useState<RunStatusResponse | null>(null);
  const [zipFile, setZipFile] = useState<File | null>(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) {
        setIsLoading(true);
        setError(null);
      }
    });

    apiClient.get<RunSummaryListResponse>(
      `/staff/courses/${courseId}/assignments/${assignmentId}/runs`
    ).then((data) => {
      if (active) {
        setRuns(data.runs);
        setIsLoading(false);
      }
    }).catch((err) => {
      if (active) {
        setError(err instanceof Error ? err.message : "Failed to load runs.");
        setIsLoading(false);
      }
    });

    return () => {
      active = false;
    };
  }, [courseId, assignmentId]);

  // Poll status of an active running process
  useEffect(() => {
    if (!activeRunId) return;

    // eslint-disable-next-line prefer-const
    let timer: NodeJS.Timeout;
    const checkStatus = async () => {
      try {
        const data = await apiClient.get<RunStatusResponse>(`/runs/${activeRunId}/status`);
        setActiveStatus(data);
        if (data.state === "complete" || data.state === "failure") {
          setActiveRunId(null);
          setSuccess("Grading run processing complete!");
          
          // Trigger a silent background refetch
          apiClient.get<RunSummaryListResponse>(
            `/staff/courses/${courseId}/assignments/${assignmentId}/runs`
          ).then((r) => setRuns(r.runs)).catch(() => {});

          clearInterval(timer);
        }
      } catch {
        clearInterval(timer);
      }
    };

    timer = setInterval(checkStatus, 2000);
    return () => clearInterval(timer);
  }, [activeRunId, courseId, assignmentId]);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!zipFile) {
      setError("Please select a Canvas ZIP export file.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append("file", zipFile);

    try {
      const res = await apiClient.postForm<IngestionResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/submissions/ingest`,
        formData
      );
      setZipFile(null);
      setActiveRunId(res.data.run_id);
      setActiveStatus({
        run_id: res.data.run_id,
        state: "queue",
        queue_position: null,
        eta_band: null,
        message: "Ingestion accepted. Queued for execution...",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "ZIP Ingestion failed.");
    } finally {
      setIsUploading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">Loading runs history...</p>
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
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Official Canvas Runs</h1>
          <p className="text-slate-500">Launch student grading cycles via Canvas ZIP exports.</p>
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
          {/* Launch Panel */}
          <div className="md:col-span-1">
            <Card>
              <form onSubmit={handleIngest}>
                <CardHeader>
                  <CardTitle className="text-lg">Launch New Run</CardTitle>
                  <CardDescription>Upload a standard ZIP containing Canvas assignments.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-slate-500">Submissions ZIP</label>
                    <input
                      type="file"
                      accept=".zip"
                      className="w-full text-xs text-slate-500 file:mr-2 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-slate-700 hover:file:bg-slate-200"
                      required
                      onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                    />
                  </div>
                </CardContent>
                <CardFooter>
                  <Button type="submit" className="w-full" disabled={isUploading || !!activeRunId}>
                    <PlayIcon className="mr-2 size-4" />
                    {isUploading ? "Uploading ZIP..." : "Launch grading run"}
                  </Button>
                </CardFooter>
              </form>
            </Card>

            {activeStatus && (
              <Card className="mt-4 border-amber-200 bg-amber-50">
                <CardHeader>
                  <CardTitle className="text-sm text-amber-800">Processing Active Run</CardTitle>
                </CardHeader>
                <CardContent className="text-xs text-amber-700 space-y-2">
                  <p>
                    <span className="font-semibold">Run ID:</span> {activeStatus.run_id}
                  </p>
                  <p>
                    <span className="font-semibold">State:</span>{" "}
                    <span className="uppercase font-bold">{activeStatus.state}</span>
                  </p>
                  {activeStatus.queue_position !== null && (
                    <p>
                      <span className="font-semibold">Queue Position:</span>{" "}
                      {activeStatus.queue_position}
                    </p>
                  )}
                  {activeStatus.message && (
                    <p className="mt-1 border-t border-amber-200 pt-2 italic">
                      {activeStatus.message}
                    </p>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Runs history */}
          <div className="md:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Grading History</CardTitle>
                <CardDescription>Select a run to view grades distribution and feedback exports.</CardDescription>
              </CardHeader>
              <CardContent>
                {runs.length === 0 ? (
                  <p className="text-sm text-slate-400 text-center py-6">No official runs recorded yet.</p>
                ) : (
                  <div className="space-y-3">
                    {runs.map((run) => (
                      <div
                        key={run.id}
                        className="flex items-center justify-between rounded-lg border border-slate-100 p-4 hover:bg-slate-50"
                      >
                        <div className="space-y-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-slate-800">Run #{run.id}</span>
                            <span
                              className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                                run.status === "complete"
                                  ? "bg-green-100 text-green-700"
                                  : run.status === "failure"
                                    ? "bg-red-100 text-red-700"
                                    : "bg-amber-100 text-amber-700"
                              }`}
                            >
                              {run.status}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-slate-500">
                            <span>Submissions: {run.total_submission_count}</span>
                            <span className="text-green-600 font-medium">Passed: {run.success_count}</span>
                            <span className="text-red-500 font-medium">Failed: {run.failure_count}</span>
                            <span className="flex items-center gap-0.5">
                              <ClockIcon className="size-3" />
                              {new Date(run.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <Button size="sm" variant="ghost" asChild>
                          <Link
                            href={`/staff/courses/${courseId}/assignments/${assignmentId}/runs/${run.id}`}
                          >
                            Details →
                          </Link>
                        </Button>
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
