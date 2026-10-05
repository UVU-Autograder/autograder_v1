"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  createSandboxRun,
  pollRunUntilComplete,
  getRunResult,
  cancelSandboxRun,
  getSandboxAiFeedback,
  streamSandboxAiFeedback,
} from "@/features/assignments/api";
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

type RunPhase = "idle" | "submitting" | "running" | "complete" | "error";

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
    setIsAiLoading(true);
    setAiFeedback("");
    try {
      await streamSandboxAiFeedback(targetRunId, targetSessionId, (chunk) => {
        setAiFeedback((prev) => (prev ? prev + chunk : chunk));
      });
    } catch (err) {
      try {
        const res = await getSandboxAiFeedback(targetRunId, targetSessionId);
        setAiFeedback(res.ai_feedback);
      } catch {
        setAiFeedback(
          err instanceof Error
            ? `Could not generate AI feedback: ${err.message}`
            : "Could not generate AI feedback at this time.",
        );
      }
    } finally {
      setIsAiLoading(false);
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

  const handleRunCode = async () => {
    setPhase("submitting");
    setErrorMessage(null);
    setResult(null);
    setRunStatus(null);
    setRunState("queue");
    setShowFeedback(false);
    setAiFeedback(null);

    try {
      const bundleBlob = await createSubmissionBundle(files);
      const { run, sessionId } = await createSandboxRun(
        courseId,
        assignmentId,
        bundleBlob,
        stdinInput || undefined,
      );

      setQuota(run.upload_quota);

      const runId = run.run_id;
      setActiveRunId(runId);
      setActiveSessionId(sessionId);
      setLastRunId(runId);
      setLastSessionId(sessionId);
      setRunStatus(run.initial_status);
      setRunState(run.initial_status.state);
      setPhase("running");

      const finalStatus = await pollRunUntilComplete(run.status_url, {
        onStatusUpdate: (currentStatus) => {
          setRunStatus(currentStatus);
          setRunState(currentStatus.state);
        },
      });

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
          setErrorMessage(
            "Upload quota exceeded. Please wait for the window to reset.",
          );
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
      <details className="mb-3 rounded-md border border-border bg-card text-card-foreground text-xs">
        <summary className="cursor-pointer select-none px-3 py-2 text-muted-foreground font-medium hover:text-foreground">
          Provide stdin{" "}
          <span className="font-mono text-xs text-muted-foreground/70">
            (optional)
          </span>
        </summary>
        <div className="border-t border-border px-3 pb-3 pt-2">
          <textarea
            id="sandbox-stdin-input"
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
      {!bundleStatus.hasRequiredEntrypoint && bundleStatus.expectedEntrypoint && (
        <div className="mb-2 flex items-center gap-2 p-2.5 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400 text-xs">
          <AlertTriangle className="size-4 shrink-0" />
          <span>
            Required entrypoint <strong>{bundleStatus.expectedEntrypoint}</strong> is missing from workspace files.
          </span>
        </div>
      )}
      <Button
        onClick={handleRunCode}
        disabled={isLoading || isQuotaExceeded}
        variant="default"
        className="w-full text-sm font-semibold py-2.5 cursor-pointer"
      >
        {isLoading ? "Running Tests..." : "Run Code"}
      </Button>

      {isLoading && (
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
          {runStatus?.queue_position != null && (
            <p>Queue position: #{runStatus.queue_position}</p>
          )}
          {runStatus?.eta_band && (
            <p>Estimated wait: {formatEtaBand(runStatus.eta_band)}</p>
          )}
        </div>
      )}

      {errorMessage && (
        <p className="mt-3 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive font-medium">
          {errorMessage}
        </p>
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
                ? "Your submission is queued. Position and ETA update as capacity clears."
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
        disabled={isAiLoading}
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
                  <span>Regenerate</span>
                </button>
              )}
            </div>
            {isAiLoading ? (
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
