"use client";

import { useState } from "react";
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
} from "@/features/assignments/types";
import { useAssignmentFile } from "./assignment-file-context";
import { createSubmissionBundle } from "./file-utils";
import { useEffect } from "react";

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
      return "text-green-600";
    case "failed":
      return "text-red-600";
    case "warning":
      return "text-amber-700";
    default:
      return "text-slate-600";
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

      const calculateRemaining = () => {
        const resetTime = new Date(quota.reset_at).getTime();
        const now = new Date().getTime();
        return Math.max(0, Math.floor((resetTime - now) / 1000));
      };

      const initialDiff = calculateRemaining();
      setCountdown(initialDiff);

      if (initialDiff <= 0) return;

      timer = setInterval(() => {
        const diff = calculateRemaining();
        setCountdown(diff);
        if (diff <= 0) {
          clearInterval(timer);
          setQuota((prev) => prev ? { ...prev, remaining: prev.limit } : prev);
        }
      }, 1000);
    });

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [quota]);

  const handleCheckCode = async () => {
    setPhase("submitting");
    setErrorMessage(null);
    setRunState("queue");
    setRunStatus(null);
    setShowCheckCode(true);

    try {
      const bundle = await createSubmissionBundle(files);
      const { run, sessionId } = await createSandboxRun(courseId, assignmentId, bundle);
      setActiveRunId(run.run_id);
      setActiveSessionId(sessionId);
      setRunStatus(run.initial_status);
      setRunState(run.initial_status.state);
      setPhase("running");

      await pollRunUntilComplete(run.status_url, {
        onStateChange: (state) => setRunState(state),
        onStatusUpdate: (status) => setRunStatus(status),
      });
      const runResult = await getRunResult(run.result_url, sessionId);
      
      setResult(runResult);
      if (run.upload_quota) {
        setQuota(run.upload_quota);
      }
      setPhase("complete");
    } catch (error) {
      setPhase("error");
      if (error instanceof ApiError && error.status === 429) {
        setErrorMessage("Upload limit reached. Please wait for the quota to reset.");
        if (quota) {
          setQuota({ ...quota, remaining: 0 });
        }
      } else {
        setErrorMessage(
          error instanceof Error ? error.message : "Failed to run sandbox check."
        );
      }
    } finally {
      setActiveRunId(null);
      setActiveSessionId(null);
      setRunStatus(null);
    }
  };

  const handleCancel = async () => {
    if (!activeRunId || !activeSessionId) return;
    try {
      await cancelSandboxRun(activeRunId, activeSessionId);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setErrorMessage("Cannot cancel: the run has already started executing.");
        return;
      }
      console.error("Failed to cancel run:", error);
      setErrorMessage(error instanceof Error ? error.message : "Failed to cancel run.");
    }
  };

  const score = result?.projected_score ?? 0;
  const totalScore = result?.max_score ?? maxScore;
  const percent = totalScore > 0 ? Math.round((score / totalScore) * 100) : 0;
  const isLoading = phase === "submitting" || phase === "running";
  const isQuotaExhausted = quota !== undefined && quota.remaining === 0;
  const testCases = (assignment.rubric || []).filter((item) => item.item_type === 'pytest');

  return (
    <div className="px-1">
      <div className="mb-4 bg-slate-50 border border-slate-200 rounded-lg p-3">
        <h4 className="text-xs font-bold text-slate-800 mb-2 uppercase tracking-wide">Test Case Specifications</h4>
        <div className="space-y-2">
          {testCases.length === 0 ? (
            <p className="text-xs text-slate-500">No test cases specified.</p>
          ) : (
            testCases.map((tc, index) => (
              <div key={tc.key} className="text-xs flex justify-between items-start gap-2 border-b border-slate-100 last:border-b-0 pb-1.5 last:pb-0">
                <span className="font-medium text-slate-700">
                  {tc.label || `Test Case #${index + 1}`}
                </span>
                <span className="text-slate-500 whitespace-nowrap">
                  {tc.points} pts {tc.extra_credit ? "(EC)" : ""}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      <Button
        onClick={handleCheckCode}
        disabled={isLoading || isQuotaExhausted}
        className="w-full mt-2 bg-gradient-to-r from-gray-800 to-gray-500 hover:from-black hover:to-indigo-600 text-white text-lg font-semibold px-6 py-3 rounded-lg disabled:opacity-50"
      >
        {phase === "submitting"
          ? "Submitting..."
          : phase === "running"
            ? "Running Tests..."
            : isQuotaExhausted
              ? "Upload Limit Reached"
              : "Run Tests"}
      </Button>

      {isLoading && runStatus && (
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
          <p className="mb-2 font-semibold uppercase tracking-wide">Run Status</p>
          <div className="space-y-1 text-amber-700">
            <p>
              <span className="font-semibold">State:</span> {runStateLabel(runStatus.state)}
            </p>
            {runStatus.queue_position !== null && (
              <p>
                <span className="font-semibold">Queue position:</span> {runStatus.queue_position}
              </p>
            )}
            {formatEtaBand(runStatus.eta_band) && (
              <p>
                <span className="font-semibold">Estimated wait: </span>
                {formatEtaBand(runStatus.eta_band)}
              </p>
            )}
            {runStatus.message && (
              <p className="mt-2 border-t border-amber-200 pt-2 italic">{runStatus.message}</p>
            )}
          </div>
        </div>
      )}

      {isLoading && activeRunId && activeSessionId && (
        <Button
          onClick={handleCancel}
          variant="destructive"
          disabled={runState !== "queue"}
          className="w-full mt-2"
        >
          {runState === "queue" ? "Cancel Run" : "Executing (Cannot Cancel)"}
        </Button>
      )}

      {quota && (
        <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-700">Sandbox Uploads:</span>
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
              <div className="w-full bg-slate-200 rounded-full h-2 mt-3">
                <div
                  className="h-2 bg-gradient-to-r from-purple-400 to-pink-500 rounded-lg"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>

            <p className="font-bold text-lg mb-2 mt-4">Test Cases:</p>
            <div>
              {result.test_summaries.length === 0 ? (
                <p className="text-sm text-slate-600">No test summaries returned.</p>
              ) : (
                result.test_summaries.map((test, index) => (
                  <div
                    key={`${test.label}-${index}`}
                    className={`p-3 mb-2 rounded-lg border ${testStatusContainerClass(test.status)}`}
                  >
                    <div className="flex justify-between items-center mb-2 gap-2">
                      <p className="font-semibold">
                        {test.label ? `Test Case: ${test.label}` : `Test Case #${index + 1}`}
                      </p>
                      <span className={`text-sm font-bold ${testStatusTextClass(test.status)}`}>
                        {testStatusLabel(test.status)}
                      </span>
                    </div>

                    <div className="text-sm space-y-1 text-slate-700">
                      <p>
                        <span className="font-medium">Points:</span> {test.points_awarded} /{" "}
                        {test.points_possible}
                      </p>
                      <p>
                        <span className="font-medium">Details:</span> {test.message}
                      </p>
                    </div>
                  </div>
                ))
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
