"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  createSandboxRunWithRetry,
  pollRunUntilComplete,
  getAssignment,
  getRunResult,
  cancelSandboxRun,
  requestAiFeedbackWithRetry,
} from "@/features/assignments/api";
import {
  GRADER_FAULT_MESSAGE,
  isGraderFault,
  RetryCancelledError,
  RunStillPendingError,
  WaitControl,
} from "@/features/assignments/sandbox-retry";
import { ApiError } from "@/lib/api-client";
import type {
  SandboxRunResultResponse,
  AssignmentsDetails,
  Assignment,
  RunStatusResponse,
  SandboxTestSummary,
} from "@/features/assignments/types";
import VisualDiffViewer from "@/components/visual-diff-viewer";
import MarkdownRenderer from "@/components/markdown-renderer";
import { Sparkles, Loader2, RefreshCw, Bot, AlertTriangle } from "lucide-react";
import { useAssignmentFile } from "./assignment-file-context";
import { checkBundleRequirements, createSubmissionBundle } from "./file-utils";

function cleanTestMessage(message: string | null | undefined): string {
  if (!message) return "";

  const lines = message.split("\n");
  const assertIndex = lines.findIndex(
    (line) => line.includes("AssertionError") || line.trim().startsWith("E   "),
  );
  if (assertIndex !== -1) {
    return lines.slice(assertIndex).join("\n");
  }

  return message;
}

function testStatusLabel(status: string): string {
  switch (status) {
    case "passed":
      return "Passed";
    case "failed":
      return "Failed";
    case "errored":
      return "Error";
    default:
      return status;
  }
}

function testStatusBadgeVariant(
  status: string,
): "success" | "destructive" | "warning" | "outline" {
  switch (status) {
    case "passed":
      return "success";
    case "failed":
    case "errored":
      return "destructive";
    case "warning":
      return "warning";
    default:
      return "outline";
  }
}

type CodeResultsProps = {
  courseId: string;
  assignmentId: string;
  maxScore: number;
  initialQuota?: AssignmentsDetails["upload_quota"];
  assignment?: Assignment;
};

type RunPhase = "idle" | "submitting" | "running" | "pending" | "complete" | "error";

type FollowedRun = { runId: string; sessionId: string; statusUrl: string; resultUrl: string };
type WaitInfo = { until: number; message: string };

function formatSeconds(totalSeconds: number): string {
  const seconds = Math.max(0, Math.round(totalSeconds));
  if (seconds < 60) return `${seconds} s`;
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return rest ? `${minutes} min ${rest} s` : `${minutes} min`;
}

function formatCountdown(ms: number): string {
  const seconds = Math.max(0, Math.ceil(ms / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

function aiWaitMessage(err: ApiError): string {
  switch (err.code) {
    case "ai_busy": {
      const ahead = typeof err.detail?.ahead === "number" && err.detail.ahead > 0 ? err.detail.ahead : null;
      return ahead
        ? `The AI tutor is helping other students (about ${ahead} ahead of you).`
        : "The AI tutor is helping other students.";
    }
    case "grading_not_complete":
      return "Waiting for your test results to finish.";
    case "ai_error":
      return "The AI tutor hit a snag.";
    default:
      return "The AI tutor is taking longer than usual.";
  }
}

function testStatusContainerClass(
  status: SandboxRunResultResponse["test_summaries"][number]["status"],
) {
  switch (status) {
    case "passed":
      return "border-success/30 bg-success/5 dark:bg-success/10";
    case "failed":
      return "border-destructive/30 bg-destructive/5 dark:bg-destructive/10";
    case "warning":
      return "border-warning/30 bg-warning/5 dark:bg-warning/10";
    default:
      return "border-border bg-card";
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
}: CodeResultsProps) {
  const { files, assignment } = useAssignmentFile();
  const bundleStatus = useMemo(
    () => checkBundleRequirements(files, assignment),
    [files, assignment]
  );
  const [showCheckCode] = useState(true);
  const [showFeedback, setShowFeedback] = useState(false);
  const [aiFeedback, setAiFeedback] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<SandboxRunResultResponse | null>(null);
  const [quota, setQuota] = useState<
    AssignmentsDetails["upload_quota"] | undefined
  >(initialQuota);
  const [prevInitialQuota, setPrevInitialQuota] = useState(initialQuota);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [lastRunId, setLastRunId] = useState<string | null>(null);
  const [lastSessionId, setLastSessionId] = useState<string | null>(null);
  const [runState, setRunState] = useState<string>("queue");
  const [runStatus, setRunStatus] = useState<RunStatusResponse | null>(null);
  const [onlyFailing, setOnlyFailing] = useState(false);
  const [isStaff] = useState(() => {
    if (typeof window === "undefined") return false;
    return !!(localStorage.getItem("token") || sessionStorage.getItem("token"));
  });
  const [stdinInput, setStdinInput] = useState("");
  const [waitInfo, setWaitInfo] = useState<WaitInfo | null>(null);
  const [aiWaitInfo, setAiWaitInfo] = useState<WaitInfo | null>(null);
  const [pendingRun, setPendingRun] = useState<FollowedRun | null>(null);
  const [aiBlockedReason, setAiBlockedReason] = useState<string | null>(null);
  const [aiFailed, setAiFailed] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  const runControlRef = useRef<WaitControl | null>(null);
  const aiControlRef = useRef<WaitControl | null>(null);

  if (initialQuota !== prevInitialQuota) {
    setQuota(initialQuota);
    setPrevInitialQuota(initialQuota);
  }

  const requestAiFeedback = async () => {
    const targetRunId = lastRunId;
    const targetSessionId = lastSessionId;
    if (isAiLoading) return;
    if (!targetRunId || !targetSessionId) {
      setAiFeedback(
        "Please run your tests first to generate AI feedback based on your results.",
      );
      return;
    }
    aiControlRef.current?.cancel();
    const control = new WaitControl();
    aiControlRef.current = control;
    setIsAiLoading(true);
    setAiFailed(false);
    setAiFeedback("");
    setAiWaitInfo(null);
    try {
      const text = await requestAiFeedbackWithRetry(
        targetRunId,
        targetSessionId,
        control,
        (chunk) => setAiFeedback((prev) => (prev ? prev + chunk : chunk)),
        (waitMs, _attempt, err) => {
          setAiFeedback("");
          setNow(Date.now());
          setAiWaitInfo({ until: Date.now() + waitMs, message: aiWaitMessage(err) });
        },
      );
      setAiFeedback(text);
    } catch (err) {
      if (err instanceof RetryCancelledError) {
        setAiFeedback(null);
        return;
      }
      if (err instanceof ApiError && err.code === "grader_fault") {
        setAiBlockedReason(GRADER_FAULT_MESSAGE);
      }
      setAiFailed(true);
      setAiFeedback(
        err instanceof Error && err.message
          ? err.message
          : "Could not generate AI feedback at this time.",
      );
    } finally {
      if (aiControlRef.current === control) {
        setAiWaitInfo(null);
        setIsAiLoading(false);
      }
    }
  };

  const handleToggleAiFeedback = async () => {
    if (showFeedback) {
      setShowFeedback(false);
      return;
    }
    setShowFeedback(true);
    if (aiFeedback || isAiLoading) return;
    await requestAiFeedback();
  };

  const handleForceRegenerateAiFeedback = async () => {
    await requestAiFeedback();
  };

  const refreshQuota = useCallback(() => {
    getAssignment(courseId, assignmentId)
      .then((latest) => setQuota(latest.upload_quota))
      .catch(() => {});
  }, [courseId, assignmentId]);

  const handleRunError = (err: unknown) => {
    if (err instanceof RetryCancelledError) {
      setPhase("idle");
      setErrorMessage("Run cancelled.");
      return;
    }
    setPhase("error");
    if (err instanceof ApiError) {
      if (err.status === 429) {
        setErrorMessage(err.message || "You have used all your runs for this hour.");
        refreshQuota();
      } else {
        setErrorMessage(err.message);
      }
    } else if (err instanceof Error) {
      setErrorMessage(err.message);
    } else {
      setErrorMessage("An unexpected error occurred.");
    }
  };

  /** Poll a run to the end and load its results (shared by Run Code and Check again). */
  const followRun = async (run: FollowedRun, control: WaitControl) => {
    setActiveRunId(run.runId);
    setActiveSessionId(run.sessionId);
    setPhase("running");
    let finalStatus: RunStatusResponse;
    try {
      finalStatus = await pollRunUntilComplete(run.statusUrl, {
        control,
        onStatusUpdate: (currentStatus) => {
          setRunStatus(currentStatus);
          setRunState(currentStatus.state);
        },
      });
    } catch (err) {
      if (err instanceof RunStillPendingError) {
        setPendingRun(run);
        setPhase("pending");
        return;
      }
      throw err;
    }

    if (finalStatus.state === "failure") {
      const fault = isGraderFault(finalStatus.failure_category, finalStatus.grader_fault);
      setPhase("error");
      setErrorMessage(
        fault ? GRADER_FAULT_MESSAGE : finalStatus.message || "Run failed during execution.",
      );
      if (fault) setAiBlockedReason(GRADER_FAULT_MESSAGE);
      try {
        const failedResult = await getRunResult(run.resultUrl, run.sessionId);
        setResult(failedResult);
        if (isGraderFault(failedResult.failure_category)) {
          setAiBlockedReason(GRADER_FAULT_MESSAGE);
          setErrorMessage(GRADER_FAULT_MESSAGE);
        }
      } catch {
        // Ignore if no stored result payload exists for the failed run
      }
      return;
    }

    const runResult = await getRunResult(run.resultUrl, run.sessionId);
    setResult(runResult);
    if (runResult.state === "failure") {
      const fault = isGraderFault(runResult.failure_category);
      setPhase("error");
      setErrorMessage(
        fault
          ? GRADER_FAULT_MESSAGE
          : runResult.warnings?.[0]?.message ||
              runResult.sanitized_feedback ||
              "Run failed during execution.",
      );
      if (fault) setAiBlockedReason(GRADER_FAULT_MESSAGE);
      return;
    }
    setPhase("complete");
  };

  const handleRunCode = async () => {
    runControlRef.current?.cancel();
    aiControlRef.current?.cancel();
    const control = new WaitControl();
    runControlRef.current = control;
    setPhase("submitting");
    setErrorMessage(null);
    setResult(null);
    setRunStatus(null);
    setRunState("queue");
    setShowFeedback(false);
    setAiFeedback(null);
    setAiFailed(false);
    setAiBlockedReason(null);
    setPendingRun(null);
    setWaitInfo(null);

    try {
      const bundleBlob = await createSubmissionBundle(files);
      const { run, sessionId } = await createSandboxRunWithRetry(
        courseId,
        assignmentId,
        bundleBlob,
        stdinInput || undefined,
        control,
        (waitMs, _attempt, err) => {
          setNow(Date.now());
          setWaitInfo({
            until: Date.now() + waitMs,
            message:
              err.code === "busy"
                ? "The grader is busy for a moment."
                : "The grading queue is full right now. Your run has not been counted yet.",
          });
        },
      );
      setWaitInfo(null);
      setQuota(run.upload_quota);
      setLastRunId(run.run_id);
      setLastSessionId(sessionId);
      setRunStatus(run.initial_status);
      setRunState(run.initial_status.state);
      await followRun(
        { runId: run.run_id, sessionId, statusUrl: run.status_url, resultUrl: run.result_url },
        control,
      );
    } catch (err) {
      setWaitInfo(null);
      handleRunError(err);
    } finally {
      if (runControlRef.current === control) {
        setActiveRunId(null);
        setActiveSessionId(null);
      }
    }
  };

  const handleCheckAgain = async () => {
    if (!pendingRun) return;
    runControlRef.current?.cancel();
    const control = new WaitControl();
    runControlRef.current = control;
    const run = pendingRun;
    setPendingRun(null);
    setErrorMessage(null);
    try {
      await followRun(run, control);
    } catch (err) {
      handleRunError(err);
    } finally {
      if (runControlRef.current === control) {
        setActiveRunId(null);
        setActiveSessionId(null);
      }
    }
  };

  const handleCancelRun = async () => {
    if (!activeRunId || !activeSessionId || runState !== "queue") return;
    try {
      await cancelSandboxRun(activeRunId, activeSessionId);
      runControlRef.current?.cancel();
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
  const quotaResetMs = quota ? Date.parse(quota.reset_at) : NaN;
  const aiAvailable =
    Boolean(lastRunId) &&
    !isLoading &&
    phase !== "pending" &&
    !aiBlockedReason &&
    (phase === "complete" || (phase === "error" && result !== null));

  // Tick once a second while a countdown is on screen.
  useEffect(() => {
    if (!waitInfo && !aiWaitInfo && !isQuotaExceeded) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [waitInfo, aiWaitInfo, isQuotaExceeded]);

  // When the hourly run limit is used up, re-enable Run Code as soon as it resets.
  useEffect(() => {
    if (!quota || quota.remaining > 0) return;
    const resetAt = Date.parse(quota.reset_at);
    const delay = Math.max((Number.isFinite(resetAt) ? resetAt - Date.now() : 60_000) + 1_000, 5_000);
    const timer = setTimeout(refreshQuota, delay);
    return () => clearTimeout(timer);
  }, [quota, refreshQuota]);

  // Stop any waits or polling when the workspace closes.
  useEffect(
    () => () => {
      runControlRef.current?.cancel();
      aiControlRef.current?.cancel();
    },
    [],
  );
  const score = result?.projected_score ?? 0;
  const totalScore = result?.max_score ?? maxScore;
  const percent = totalScore > 0 ? (score / totalScore) * 100 : 0;

  const renderTestItem = (test: SandboxTestSummary, index: number) => (
    <div
      key={`${test.label}-${index}`}
      className={`p-3 mb-2 rounded-lg border ${testStatusContainerClass(test.status)}`}
    >
      <div className="flex justify-between items-center mb-2 gap-2">
        <p className="font-semibold text-foreground text-sm">
          {test.label ? test.label : `Test Case #${index + 1}`}
        </p>
        <Badge variant={testStatusBadgeVariant(test.status)}>
          {testStatusLabel(test.status)}
        </Badge>
      </div>

      <div className="text-sm space-y-1 text-foreground">
        <p className="text-xs text-muted-foreground">
          <span className="font-medium">Points:</span> {test.points_awarded} /{" "}
          {test.points_possible}
        </p>

        {test.status !== "passed" && test.hint && (
          <div className="mt-2 rounded-md border border-border bg-muted/40 p-3 text-sm whitespace-pre-wrap">
            <Badge variant="secondary">Instructor Hint</Badge>
            <p className="mt-1">{test.hint}</p>
          </div>
        )}
        {test.output_truncated && (
          <p role="alert" className="mt-2 rounded-md border border-amber-400 p-2 text-xs">
            Output exceeded 64 KiB. This test failed. Check for excessive printing or a loop.
          </p>
        )}
        {test.status !== "passed" &&
          (test.your_value != null ||
            test.actual != null ||
            test.expected_value != null ||
            test.expected != null) && (
            <div className="mt-2.5 space-y-2">
              <div className="p-3 rounded-md border border-border bg-muted/40 space-y-1.5 text-xs font-sans">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-destructive w-28 shrink-0">
                    Your value:
                  </span>
                  <code className="bg-destructive/15 text-destructive px-2 py-0.5 rounded font-mono break-all font-medium">
                    {test.your_value ?? test.actual ?? "false"}
                  </code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-success w-28 shrink-0">
                    Expected value:
                  </span>
                  <code className="bg-success/15 text-success px-2 py-0.5 rounded font-mono break-all font-medium">
                    {test.expected_value ?? test.expected ?? "true"}
                  </code>
                </div>
              </div>
              {(test.expected || test.actual) && (
                <VisualDiffViewer
                  expected={test.expected ?? test.expected_value}
                  actual={test.actual ?? test.your_value}
                />
              )}
            </div>
          )}

        {test.status !== "passed" &&
          test.message &&
          !test.your_value &&
          !test.actual &&
          cleanTestMessage(test.message).trim() !==
            (test.label || "").trim() && (
            <p className="mt-2 text-xs text-destructive bg-destructive/10 p-2 rounded border border-destructive/20 font-sans">
              {cleanTestMessage(test.message).split("\n")[0]}
            </p>
          )}

        {isStaff &&
          test.status !== "passed" &&
          (result?.raw_output ||
            (test.message &&
              cleanTestMessage(test.message).includes("\n"))) && (
            <details className="mt-2 text-xs text-muted-foreground">
              <summary className="cursor-pointer font-semibold text-primary hover:underline">
                View Raw Terminal Output
              </summary>
              <pre className="mt-1 bg-muted text-foreground p-3 rounded-md font-mono text-xs overflow-x-auto whitespace-pre-wrap max-h-60 border border-border">
                {result?.raw_output || cleanTestMessage(test.message)}
              </pre>
            </details>
          )}
      </div>
    </div>
  );

  return (
    <div className="w-full max-w-full min-w-0 flex-1 h-full flex flex-col p-4 overflow-y-auto overflow-x-hidden bg-background border-l border-border text-foreground">
      {(result?.diagnostics?.stdout_truncated || result?.diagnostics?.stderr_truncated) && (
        <p role="alert" className="mb-3 rounded-md border border-amber-400 p-3 text-sm">
          Console output was truncated at 64 KiB. Check for excessive printing or a loop.
        </p>
      )}
      <details className="mb-3 rounded-md border border-border bg-card text-card-foreground text-xs">
        <summary className="cursor-pointer select-none px-3 py-2 text-muted-foreground font-medium hover:text-foreground">
          Provide stdin{" "}
          <span className="font-mono text-xs text-muted-foreground">
            (optional)
          </span>
        </summary>
        <div className="border-t border-border px-3 pb-3 pt-2">
          <textarea
            id="sandbox-stdin-input"
            name="stdin"
            aria-label="Console input / stdin"
            value={stdinInput}
            onChange={(e) => setStdinInput(e.target.value)}
            placeholder={
              "Each line will be fed as keyboard input (Enter)\ne.g.\nAlice\n3"
            }
            rows={3}
            className="w-full max-w-full resize-y rounded border border-input bg-background text-foreground p-2 font-mono text-xs leading-relaxed focus:border-primary focus:outline-none"
          />
        </div>
      </details>
      {Object.values(files).every((f) => f.category !== "workspace") ? (
        bundleStatus.expectedEntrypoint && (
          <div className="mb-2 flex items-center gap-2 p-2.5 rounded-lg border border-primary/20 bg-primary/5 text-primary text-xs font-medium">
            <Sparkles className="size-4 shrink-0 text-primary" />
            <span>
              To begin, create or upload <strong>{bundleStatus.expectedEntrypoint}</strong> in the sidebar.
            </span>
          </div>
        )
      ) : (
        <>
          {!bundleStatus.hasRequiredEntrypoint && bundleStatus.expectedEntrypoint && (
            <div className="mb-2 flex items-center gap-2 p-2.5 rounded-lg border border-warning/30 bg-warning/10 text-amber-900 dark:text-amber-200 font-medium text-xs">
              <AlertTriangle className="size-4 shrink-0" />
              <span>
                Required entrypoint <strong>{bundleStatus.expectedEntrypoint}</strong> is missing from workspace files.
              </span>
            </div>
          )}
          {bundleStatus.missingRequiredFiles.length > 0 && (
            <div className="mb-2 flex items-center gap-2 p-2.5 rounded-lg border border-warning/30 bg-warning/10 text-amber-900 dark:text-amber-200 font-medium text-xs">
              <AlertTriangle className="size-4 shrink-0" />
              <span>
                Missing required file(s):{" "}
                <strong>{bundleStatus.missingRequiredFiles.join(", ")}</strong>
              </span>
            </div>
          )}
        </>
      )}
      <Button
        onClick={handleRunCode}
        disabled={isLoading || isQuotaExceeded}
        variant="default"
        className="w-full text-sm font-semibold py-2.5 cursor-pointer"
      >
        {isLoading ? "Running Tests..." : "Run Code"}
      </Button>
      {quota && !isQuotaExceeded && (
        <p className="mt-1.5 text-center text-[11px] text-muted-foreground" data-testid="quota-remaining">
          {quota.remaining} of {quota.limit} runs left this hour
        </p>
      )}
      {quota && isQuotaExceeded && (
        <p
          role="status"
          data-testid="quota-exhausted"
          className="mt-2 rounded-lg border border-warning/30 bg-warning/10 p-2.5 text-xs font-medium text-warning"
        >
          You have used all {quota.limit} runs for this hour.{" "}
          {Number.isFinite(quotaResetMs)
            ? `Run Code unlocks in ${formatCountdown(quotaResetMs - now)}.`
            : "Run Code unlocks when the hour resets."}
        </p>
      )}

      {waitInfo && (
        <div
          role="status"
          data-testid="admission-wait"
          className="mt-3 rounded-lg border border-primary/30 bg-primary/5 dark:bg-primary/10 p-3 text-xs text-foreground space-y-2"
        >
          <p>
            {waitInfo.message} Retrying in {formatSeconds((waitInfo.until - now) / 1000)}.
          </p>
          <div className="flex gap-3 font-semibold">
            <button type="button" className="text-primary hover:underline cursor-pointer" onClick={() => runControlRef.current?.skip()}>
              Try now
            </button>
            <button type="button" className="text-destructive hover:underline cursor-pointer" onClick={() => runControlRef.current?.cancel()}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {phase === "pending" && pendingRun && (
        <div
          role="status"
          data-testid="run-pending"
          className="mt-3 rounded-lg border border-primary/30 bg-primary/5 dark:bg-primary/10 p-3 text-xs text-foreground space-y-2"
        >
          <p>Your run is taking longer than usual and is still in line. Your results will be kept.</p>
          <button type="button" className="font-semibold text-primary hover:underline cursor-pointer" onClick={handleCheckAgain}>
            Check again
          </button>
        </div>
      )}

      {isLoading && !waitInfo && (
        <div className="mt-3 rounded-lg border border-primary/30 bg-primary/5 dark:bg-primary/10 p-3 text-xs text-foreground space-y-1.5">
          <div className="flex items-center justify-between font-semibold">
            <span>Status: {runStateLabel(runState)}</span>
            {runState === "queue" && activeRunId && (
              <button
                type="button"
                onClick={handleCancelRun}
                className="text-xs text-destructive hover:underline font-bold cursor-pointer"
              >
                Cancel Run
              </button>
            )}
          </div>
          {runState === "queue" && runStatus?.submissions_ahead != null ? (
            <p data-testid="queue-ahead">
              {runStatus.submissions_ahead === 0
                ? "You're next in line."
                : `About ${runStatus.submissions_ahead} submission${runStatus.submissions_ahead === 1 ? "" : "s"} ahead of yours.`}
            </p>
          ) : runState === "queue" && runStatus?.queue_position != null ? (
            <p>Queue position: #{runStatus.queue_position}</p>
          ) : null}
          {runState === "queue" && runStatus?.submissions_ahead == null && runStatus?.eta_seconds != null && (
            <p>Other students&apos; submissions are being graded; yours is in line.</p>
          )}
          {runState === "queue" && runStatus?.eta_seconds != null ? (
            <p>Estimated wait: about {formatSeconds(runStatus.eta_seconds)}</p>
          ) : runStatus?.eta_band ? (
            <p>Estimated wait: {formatEtaBand(runStatus.eta_band)}</p>
          ) : null}
        </div>
      )}

      {errorMessage && (
        <div
          role="alert"
          data-failure-category={result?.failure_category ?? undefined}
          className="mt-3 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive space-y-1"
        >
          {result?.failure_category && (
            <span className="block font-mono text-[10px] uppercase tracking-wider opacity-80">
              {result.failure_category}
            </span>
          )}
          <p className="font-medium">{errorMessage}</p>
        </div>
      )}

      <div className={`flex flex-1 flex-col ${showCheckCode ? "" : "hidden"}`}>
        {result ? (
          <>
            <div className="mt-4">
              <p className="font-bold text-lg mb-2">Score:</p>
              <p className="text-foreground font-semibold">
                {score} / {totalScore}
              </p>
              <div className="w-full bg-muted rounded-full h-2 mt-3 overflow-hidden">
                <div
                  className={`h-2 rounded-lg transition-all ${percent >= 100 ? "bg-success" : "bg-primary"}`}
                  style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
                />
              </div>
            </div>

            <div className="flex items-center justify-between flex-wrap gap-2 mb-3 mt-4">
              <p className="font-bold text-lg">Test Cases:</p>
              <label className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={onlyFailing}
                  onChange={(e) => setOnlyFailing(e.target.checked)}
                  className="rounded border-input text-primary focus:ring-primary h-4 w-4"
                />
                Only show failing tests
              </label>
            </div>

            <div>
              {result.rubric_groups && result.rubric_groups.length > 0
                ? result.rubric_groups.map((group) => {
                    const filteredItems = onlyFailing
                      ? group.items.filter((item) => item.status !== "passed")
                      : group.items;
                    if (onlyFailing && filteredItems.length === 0) return null;

                    return (
                      <div
                        key={group.group_key}
                        className="mb-4 border border-border rounded-lg overflow-hidden bg-card shadow-xs"
                      >
                        <div className="flex justify-between items-center bg-muted/50 px-3 py-2 border-b border-border">
                          <span className="font-bold text-foreground text-xs">
                            {group.label}
                          </span>
                          <span className="text-xs font-semibold px-2 py-0.5 bg-muted text-muted-foreground rounded-full">
                            {group.points_earned} / {group.points_possible} pts
                          </span>
                        </div>
                        <div className="p-2 space-y-1">
                          {filteredItems.map((test, index) =>
                            renderTestItem(test, index),
                          )}
                        </div>
                      </div>
                    );
                  })
                : (() => {
                    const displaySummaries = onlyFailing
                      ? result.test_summaries.filter(
                          (t) => t.status !== "passed",
                        )
                      : result.test_summaries;
                    if (displaySummaries.length === 0) {
                      return (
                        <p className="text-sm text-muted-foreground">
                          {onlyFailing
                            ? "No failing tests found 🎉"
                            : "No test summaries returned."}
                        </p>
                      );
                    }
                    return displaySummaries.map((test, index) =>
                      renderTestItem(test, index),
                    );
                  })()}
            </div>

            {result.warnings.length > 0 && (
              <>
                <p className="font-bold text-lg mt-4">Warnings:</p>
                <div className="mt-2 space-y-3">
                  {result.warnings.map((warning, index) => (
                    <div
                      key={`${warning.code}-${index}`}
                      className="border-l-4 border-warning bg-warning/10 rounded-md p-3 text-foreground"
                    >
                      <p className="text-warning font-semibold text-sm">
                        {warning.code}
                      </p>
                      <p className="text-sm text-foreground/90 mt-1">
                        {warning.message}
                      </p>
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        ) : (
          <p className="mt-4 text-sm text-muted-foreground">
            {isLoading
              ? runState === "queue"
                ? "Your submission is queued. Your place in line updates as other submissions finish."
                : runState === "run"
                  ? "Your submission is running. Results will appear here when grading finishes."
                  : "Waiting for sandbox results..."
              : "Run tests to see your projected score and test summaries."}
          </p>
        )}
      </div>

      <Button
        variant="outline"
        onClick={handleToggleAiFeedback}
        disabled={isAiLoading || (!showFeedback && !aiFeedback && !aiAvailable)}
        title={
          aiBlockedReason ??
          (!aiAvailable && !aiFeedback ? "Run your tests first; AI feedback uses your results." : undefined)
        }
        className="w-full mt-4 font-semibold text-sm cursor-pointer flex items-center justify-center gap-2 border-primary/30 hover:border-primary/50 transition-colors"
      >
        {isAiLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <span>Consulting Local AI...</span>
          </>
        ) : showFeedback ? (
          <>
            <Bot className="h-4 w-4 text-muted-foreground" />
            <span>Hide AI Feedback</span>
          </>
        ) : aiFeedback ? (
          <>
            <Sparkles className="h-4 w-4 text-primary" />
            <span>Show AI Feedback</span>
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4 text-primary" />
            <span>Request AI Feedback</span>
          </>
        )}
      </Button>
      {showFeedback && (
        <div className="mt-3 space-y-2">
          <div className="p-4 rounded-xl border border-primary/25 bg-primary/[0.04] dark:bg-primary/[0.08] text-foreground transition-all">
            <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-primary/15">
              <div className="flex items-center gap-2">
                <div className="p-1 rounded bg-primary/10 text-primary">
                  <Sparkles className="h-3.5 w-3.5" />
                </div>
                <p className="font-semibold text-xs text-primary tracking-wide uppercase">
                  Local AI Tutor
                </p>
              </div>
              {aiFeedback && !isAiLoading && (
                <button
                  onClick={handleForceRegenerateAiFeedback}
                  title="Regenerate feedback from local model"
                  className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground cursor-pointer transition-colors px-1.5 py-0.5 rounded hover:bg-muted/50"
                >
                  <RefreshCw className="h-3 w-3" />
                  <span>{aiFailed ? "Try again" : "Regenerate"}</span>
                </button>
              )}
            </div>
            {aiBlockedReason && !aiFeedback ? (
              <p className="text-xs text-muted-foreground leading-relaxed" data-testid="ai-blocked">
                {aiBlockedReason} AI feedback is skipped for this run.
              </p>
            ) : isAiLoading && aiWaitInfo ? (
              <div className="space-y-2 py-2 text-xs" role="status" data-testid="ai-wait">
                <p className="text-foreground">
                  {aiWaitInfo.message} Retrying in {formatSeconds((aiWaitInfo.until - now) / 1000)}.
                </p>
                <button
                  type="button"
                  className="font-semibold text-primary hover:underline cursor-pointer"
                  onClick={() => aiControlRef.current?.skip()}
                >
                  Try now
                </button>
              </div>
            ) : isAiLoading ? (
              <div className="space-y-3 py-2">
                <div className="flex items-center gap-2 text-xs text-primary font-medium">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>
                    Analyzing code and test outputs on local AI tutor...
                  </span>
                </div>
                <div className="space-y-2 pt-1 opacity-70 animate-pulse">
                  <div className="h-2.5 bg-primary/20 rounded w-4/5" />
                  <div className="h-2.5 bg-primary/15 rounded w-full" />
                  <div className="h-2.5 bg-primary/15 rounded w-2/3" />
                </div>
              </div>
            ) : aiFeedback ? (
              <MarkdownRenderer content={aiFeedback} />
            ) : (
              <p className="text-xs text-muted-foreground leading-relaxed">
                Click &quot;Request AI Feedback&quot; to receive Socratic
                guidance and hints from your local model.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
