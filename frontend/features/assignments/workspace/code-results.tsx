"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  createSandboxRun,
  pollRunUntilComplete,
  getRunResult,
  cancelSandboxRun,
} from "@/features/assignments/api";
import { ApiError } from "@/lib/api-client";
import type {
  SandboxRunResultResponse,
  AssignmentsDetails,
  Assignment,
  RunStatusResponse,
  SandboxTestSummary,
} from "@/features/assignments/types";
import { useAssignmentFile } from "./assignment-file-context";
import { createSubmissionBundle } from "./file-utils";
import VisualDiffViewer from "@/components/visual-diff-viewer";

function cleanTestMessage(message: string | null | undefined): string {
  if (!message) return "";

  const lines = message.split("\n");
  const assertIndex = lines.findIndex(
    (line) => line.includes("AssertionError") || line.trim().startsWith("E   ")
  );
  if (assertIndex !== -1) {
    return lines.slice(assertIndex).join("\n");
  }

  return message;
}

type CodeResultsProps = {
  courseId: string;
  assignmentId: string;
  maxScore: number;
  initialQuota?: AssignmentsDetails["upload_quota"];
  assignment: Assignment;
};

type RunPhase = "idle" | "submitting" | "running" | "complete" | "error";

function testStatusLabel(status: SandboxRunResultResponse["test_summaries"][number]["status"]) {
  switch (status) {
    case "passed":
      return "Passed";
    case "failed":
      return "Failed";
    case "warning":
      return "Warning";
    default:
      return "Not run";
  }
}

function testStatusContainerClass(
  status: SandboxRunResultResponse["test_summaries"][number]["status"]
) {
  switch (status) {
    case "passed":
      return "border-green-300 bg-green-50";
    case "failed":
      return "border-red-300 bg-red-50";
    case "warning":
      return "border-amber-300 bg-amber-50";
    default:
      return "border-slate-300 bg-slate-50";
  }
}

function testStatusTextClass(
  status: SandboxRunResultResponse["test_summaries"][number]["status"]
) {
  switch (status) {
    case "passed":
      return "text-green-600 font-bold";
    case "failed":
      return "text-red-600 font-bold";
    case "warning":
      return "text-amber-700 font-bold";
    default:
      return "text-slate-600 font-bold";
  }
}

function formatEtaBand(etaBand: string | null): string | null {
  if (!etaBand) return null;
  const labels: Record<string, string> = {
    under_1_min: "Under 1 minute",
    "1_to_3_min": "1–3 minutes",
    "3_to_5_min": "3–5 minutes",
    over_5_min: "Over 5 minutes",
  };
  return labels[etaBand] ?? etaBand;
}

function runStateLabel(state: string): string {
  switch (state) {
    case "queue":
      return "Queued";
    case "run":
      return "Running";
    case "complete":
      return "Complete";
    case "failure":
      return "Failed";
    default:
      return state;
  }
}

export default function CodeResults({
  courseId,
  assignmentId,
  maxScore,
  initialQuota,
  assignment,
}: CodeResultsProps) {
  const { files } = useAssignmentFile();
  const [showCheckCode, setShowCheckCode] = useState(true);
  const [showFeedback, setShowFeedback] = useState(true);
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<SandboxRunResultResponse | null>(null);
  const [quota, setQuota] = useState<AssignmentsDetails["upload_quota"] | undefined>(initialQuota);
  const [prevInitialQuota, setPrevInitialQuota] = useState(initialQuota);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [runState, setRunState] = useState<string>("queue");
  const [runStatus, setRunStatus] = useState<RunStatusResponse | null>(null);
  const [onlyFailing, setOnlyFailing] = useState(false);
  const [isStaff, setIsStaff] = useState(false);

  useEffect(() => {
    const token = typeof window !== "undefined" ? (localStorage.getItem("token") || sessionStorage.getItem("token")) : null;
    setIsStaff(!!token);
  }, []);

  if (initialQuota !== prevInitialQuota) {
    setQuota(initialQuota);
    setPrevInitialQuota(initialQuota);
  }

  useEffect(() => {
    let timer: NodeJS.Timeout;

    Promise.resolve().then(() => {
      if (!quota || quota.remaining > 0) {
        setCountdown(null);
        return;
      }

      const resetTime = new Date(quota.reset_at).getTime();

      const updateCountdown = () => {
        const now = new Date().getTime();
        const diff = Math.max(0, Math.floor((resetTime - now) / 1000));
        setCountdown(diff);
      };

      updateCountdown();
      timer = setInterval(updateCountdown, 1000);
    });

    return () => clearInterval(timer);
  }, [quota]);

  const handleRunCode = async () => {
    setPhase("submitting");
    setErrorMessage(null);
    setResult(null);
    setRunStatus(null);
    setRunState("queue");

    try {
      const bundleBlob = await createSubmissionBundle(files);
      const { run, sessionId } = await createSandboxRun(courseId, assignmentId, bundleBlob);

      setQuota(run.upload_quota);

      const runId = run.run_id;
      setActiveRunId(runId);
      setActiveSessionId(sessionId);
      setRunStatus(run.initial_status);
      setRunState(run.initial_status.state);
      setPhase("running");

      const finalStatus = await pollRunUntilComplete(
        run.status_url,
        {
          onStatusUpdate: (currentStatus) => {
            setRunStatus(currentStatus);
            setRunState(currentStatus.state);
          },
        }
      );

      if (finalStatus.state === "failure") {
        setPhase("error");
        setErrorMessage(finalStatus.message || "Run failed during execution.");
        return;
      }

      const runResult = await getRunResult(run.result_url, sessionId);
      setResult(runResult);
      setPhase("complete");
    } catch (err) {
      setPhase("error");
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setErrorMessage("Upload quota exceeded. Please wait for the window to reset.");
        } else {
          setErrorMessage(err.message);
        }
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred.");
      }
    } finally {
      setActiveRunId(null);
      setActiveSessionId(null);
    }
  };

  const handleCancelRun = async () => {
    if (!activeRunId || !activeSessionId || runState !== "queue") return;
    try {
      await cancelSandboxRun(activeRunId, activeSessionId);
      setPhase("idle");
      setErrorMessage("Run cancelled.");
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      }
    }
  };

  const isLoading = phase === "submitting" || phase === "running";
  const isQuotaExceeded = quota ? quota.remaining === 0 : false;
  const score = result?.projected_score ?? 0;
  const totalScore = result?.max_score ?? maxScore;
  const percent = totalScore > 0 ? (score / totalScore) * 100 : 0;

  const renderTestItem = (test: SandboxTestSummary, index: number) => (
    <div
      key={`${test.label}-${index}`}
      className={`p-3 mb-2 rounded-lg border ${testStatusContainerClass(test.status)}`}
    >
      <div className="flex justify-between items-center mb-2 gap-2">
        <p className="font-semibold text-slate-900 text-sm">
          {test.label ? test.label : `Test Case #${index + 1}`}
        </p>
        <span className={`text-xs ${testStatusTextClass(test.status)}`}>
          {testStatusLabel(test.status)}
        </span>
      </div>

      <div className="text-sm space-y-1 text-slate-700">
        <p className="text-xs text-slate-600">
          <span className="font-medium">Points:</span> {test.points_awarded} /{" "}
          {test.points_possible}
        </p>

        {(test.your_value != null || test.actual != null || test.expected_value != null || test.expected != null) && (
          <div className="mt-2.5 p-3 rounded-md border border-red-200 bg-red-100/60 space-y-1.5 text-xs font-sans">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-red-900 w-28 shrink-0">Your value:</span>
              <code className="bg-red-200/70 text-red-950 px-2 py-0.5 rounded font-mono break-all">
                {test.your_value ?? test.actual ?? "false"}
              </code>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-emerald-900 w-28 shrink-0">Expected value:</span>
              <code className="bg-emerald-200/70 text-emerald-950 px-2 py-0.5 rounded font-mono break-all">
                {test.expected_value ?? test.expected ?? "true"}
              </code>
            </div>
          </div>
        )}

        {test.message && !test.your_value && !test.actual && (
          <p className="mt-2 text-xs text-red-700 bg-red-100/60 p-2 rounded font-sans">
            {cleanTestMessage(test.message).split("\n")[0]}
          </p>
        )}

        {isStaff && (result?.raw_output || test.message) && (
          <details className="mt-2 text-xs text-slate-500">
            <summary className="cursor-pointer font-semibold text-purple-700 hover:text-purple-900">
              🔍 [Instructor Only] View Raw Terminal Output
            </summary>
            <pre className="mt-1 bg-slate-900 text-slate-100 p-3 rounded-md font-mono text-xs overflow-x-auto whitespace-pre-wrap max-h-60">
              {result?.raw_output || cleanTestMessage(test.message)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );

  return (
    <div className="w-[450px] bg-slate-50 border-l border-slate-200 p-4 flex flex-col h-full overflow-y-auto">
      <Button
        onClick={handleRunCode}
        disabled={isLoading || isQuotaExceeded}
        className="w-full bg-gradient-to-r from-purple-400 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white text-lg font-semibold px-6 py-3 rounded-lg shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? "Running Tests..." : "Run Code"}
      </Button>

      {isLoading && (
        <div className="mt-3 rounded-lg border border-purple-200 bg-purple-50 p-3 text-xs text-purple-900 space-y-1.5">
          <div className="flex items-center justify-between font-semibold">
            <span>Status: {runStateLabel(runState)}</span>
            {runState === "queue" && activeRunId && (
              <button
                type="button"
                onClick={handleCancelRun}
                className="text-xs text-red-600 hover:underline font-bold"
              >
                Cancel Run
              </button>
            )}
          </div>
          {runStatus?.queue_position != null && (
            <p>Queue position: #{runStatus.queue_position}</p>
          )}
          {runStatus?.eta_band && (
            <p>Estimated wait: {formatEtaBand(runStatus.eta_band)}</p>
          )}
        </div>
      )}

      {quota && (
        <div className="mt-3 text-xs text-slate-500 bg-white p-2.5 rounded border border-slate-200">
          <div className="flex justify-between items-center">
            <span>Sandbox Quota:</span>
            <span className={`font-bold ${quota.remaining === 0 ? "text-red-600" : "text-slate-600"}`}>
              {quota.remaining} / {quota.limit} remaining
            </span>
          </div>
          {quota.remaining === 0 && countdown !== null && (
            <div className="mt-2 text-red-600 font-semibold border-t border-red-200 pt-2 text-center">
              Resets in {Math.floor(countdown / 60)}m {countdown % 60}s
            </div>
          )}
        </div>
      )}

      {errorMessage && (
        <p className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {errorMessage}
        </p>
      )}

      <div className={`flex flex-1 flex-col ${showCheckCode ? "" : "hidden"}`}>
        {result ? (
          <>
            <div className="mt-4">
              <p className="font-bold text-lg mb-2">Score:</p>
              <p>
                {score} / {totalScore}
              </p>
              <div className="w-full bg-slate-200 rounded-full h-2 mt-3 overflow-hidden">
                <div
                  className="h-2 bg-gradient-to-r from-purple-400 to-pink-500 rounded-lg"
                  style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
                />
              </div>
            </div>

            <div className="flex items-center justify-between mb-3 mt-4">
              <p className="font-bold text-lg">Test Cases:</p>
              <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={onlyFailing}
                  onChange={(e) => setOnlyFailing(e.target.checked)}
                  className="rounded border-slate-300 text-purple-600 focus:ring-purple-500 h-4 w-4"
                />
                Only show failing tests
              </label>
            </div>

            <div>
              {result.rubric_groups && result.rubric_groups.length > 0 ? (
                result.rubric_groups.map((group) => {
                  const filteredItems = onlyFailing
                    ? group.items.filter((item) => item.status !== "passed")
                    : group.items;
                  if (onlyFailing && filteredItems.length === 0) return null;

                  return (
                    <div
                      key={group.group_key}
                      className="mb-4 border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm"
                    >
                      <div className="flex justify-between items-center bg-slate-100 px-3 py-2 border-b border-slate-200">
                        <span className="font-bold text-slate-800 text-xs">{group.label}</span>
                        <span className="text-xs font-bold px-2 py-0.5 bg-slate-200 text-slate-700 rounded-full">
                          {group.points_earned} / {group.points_possible} pts
                        </span>
                      </div>
                      <div className="p-2 space-y-1">
                        {filteredItems.map((test, index) => renderTestItem(test, index))}
                      </div>
                    </div>
                  );
                })
              ) : (
                (() => {
                  const displaySummaries = onlyFailing
                    ? result.test_summaries.filter((t) => t.status !== "passed")
                    : result.test_summaries;
                  if (displaySummaries.length === 0) {
                    return (
                      <p className="text-sm text-slate-600">
                        {onlyFailing ? "No failing tests found 🎉" : "No test summaries returned."}
                      </p>
                    );
                  }
                  return displaySummaries.map((test, index) => renderTestItem(test, index));
                })()
              )}
            </div>

            {result.warnings.length > 0 && (
              <>
                <p className="font-bold text-lg mt-4">Warnings:</p>
                <div className="mt-2 space-y-3">
                  {result.warnings.map((warning, index) => (
                    <div
                      key={`${warning.code}-${index}`}
                      className="border-l-4 border-amber-500 bg-amber-50 rounded-md p-4"
                    >
                      <p className="text-amber-800 font-semibold">{warning.code}</p>
                      <p className="text-sm text-amber-700 mt-2">{warning.message}</p>
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        ) : (
          <p className="mt-4 text-sm text-slate-600">
            {isLoading
              ? runState === "queue"
                ? "Your submission is queued. Position and ETA update as capacity clears."
                : runState === "run"
                  ? "Your submission is running. Results will appear here when grading finishes."
                  : "Waiting for sandbox results..."
              : "Run tests to see your projected score and test summaries."}
          </p>
        )}
      </div>

      <br />

      <Button
        onClick={() => setShowFeedback((prev) => !prev)}
        className="w-full mt-2 bg-gradient-to-r from-purple-400 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white text-lg font-semibold px-6 py-3 rounded-lg"
      >
        View AI Feedback
      </Button>
      <div className={`flex flex-1 flex-col ${showFeedback ? "" : "hidden"}`}>
        <div className="text-wrap mt-4">
          <p className="font-bold text-lg">Feedback:</p>
          <p className="mt-2 text-sm text-slate-700">
            {result?.sanitized_feedback ??
              "Run tests to generate session-only projected feedback."}
          </p>
          {result?.retention_notice && (
            <p className="mt-3 text-xs text-slate-500">{result.retention_notice}</p>
          )}
        </div>
      </div>
    </div>
  );
}
