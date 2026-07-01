"use client";

import { use, useState, useEffect, useRef } from "react";
import { DownloadIcon, AwardIcon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import {
  staffRunCsvExportPath,
  staffRunFeedbackExportPath,
} from "@/features/staff/api";

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
};

type RunDetailsResponse = {
  run_id: number;
  status: string;
  students: StudentRunDetail[];
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
        setDetails(detailsData);
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

  const cleanupTimeoutRef = useRef<any>(null);

  useEffect(() => {
    // Cancel any pending cleanup from a previous mount/strict-mode cycle
    if (cleanupTimeoutRef.current) {
      clearTimeout(cleanupTimeoutRef.current);
      cleanupTimeoutRef.current = null;
    }

    const triggerCleanup = () => {
      const url = `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}/cleanup`;
      const token = typeof window !== "undefined" ? (localStorage.getItem("token") || sessionStorage.getItem("token")) : null;
      const headers = new Headers();
      if (token) {
        headers.set("authorization", `Bearer ${token}`);
      }
      const base = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
      
      fetch(`${base}${url}`, {
        method: "POST",
        headers,
        keepalive: true,
      }).catch((err) => console.error("Auto cleanup failed", err));
    };

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };

    const handleUnload = () => {
      triggerCleanup();
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("pagehide", handleUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("pagehide", handleUnload);
      
      // Delay unmount cleanup to avoid React 18 strict mode double-render purging files on initial load
      cleanupTimeoutRef.current = setTimeout(() => {
        triggerCleanup();
      }, 1500);
    };
  }, [courseId, assignmentId, runId]);

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
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Run #{runId} Details</h1>
            <p className="text-slate-500">Grading results overview and student lists</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={handleCsvExport}>
              <DownloadIcon className="mr-2 size-4" /> Export Grades CSV
            </Button>
            <Button variant="outline" onClick={handleFeedbackExport}>
              <DownloadIcon className="mr-2 size-4" /> Export Feedback ZIP
            </Button>
          </div>
        </div>

        {/* Zero-Retention Warning Banner */}
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
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
                <div className="flex justify-between border-t border-slate-100 pt-3 text-sm">
                  <span className="text-green-600 font-semibold">Passed</span>
                  <span className="font-bold text-slate-700">{summary?.success_count}</span>
                </div>
                <div className="flex justify-between border-t border-slate-100 pt-3 text-sm">
                  <span className="text-red-500 font-semibold">Failed</span>
                  <span className="font-bold text-slate-700">{summary?.failure_count}</span>
                </div>
                <div className="flex justify-between border-t border-slate-100 pt-3 text-sm">
                  <span className="text-amber-600 font-semibold">Warnings</span>
                  <span className="font-bold text-slate-700">{summary?.warning_count}</span>
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
                  <p className="text-sm text-slate-400 text-center py-6">No student details returned.</p>
                ) : (
                  <div className="space-y-3">
                    {details.students.map((student, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-slate-100 p-4 hover:shadow-sm transition-shadow bg-white"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                          <div className="space-y-0.5">
                            <p className="font-semibold text-slate-800">{student.student_name}</p>
                            <p className="text-xs text-slate-400">
                              Canvas ID: {student.canvas_id} | File: {student.matched_file}
                            </p>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center text-slate-700 gap-1 text-sm font-semibold">
                              <AwardIcon className="size-4 text-slate-400" />
                              {student.score} / {student.max_score} pts
                            </div>
                            <span
                              className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                                student.status === "success"
                                  ? "bg-green-50 text-green-700"
                                  : student.status === "failure"
                                    ? "bg-red-50 text-red-700"
                                    : "bg-amber-50 text-amber-700"
                              }`}
                            >
                              {student.status}
                            </span>
                          </div>
                        </div>

                        {student.feedback_preview && (
                          <div className="mt-3 rounded border border-slate-50 bg-slate-50 p-2.5 text-xs text-slate-600">
                            <span className="font-bold block text-slate-500 mb-1">Feedback Summary:</span>
                            <p className="line-clamp-2">{student.feedback_preview}</p>
                          </div>
                        )}
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
