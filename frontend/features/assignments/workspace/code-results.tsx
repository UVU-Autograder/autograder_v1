"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { runSandboxCheck } from "@/features/assignments/api";
import { ApiError } from "@/lib/api-client";
import type { SandboxRunResultResponse, AssignmentsDetails } from "@/features/assignments/types";
import { useAssignmentFile } from "./assignment-file-context";
import { createSubmissionBundle } from "./file-utils";

type CodeResultsProps = {
  courseId: string;
  assignmentId: string;
  maxScore: number;
  initialQuota?: AssignmentsDetails["upload_quota"];
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

import { useEffect } from "react";

export default function CodeResults({
  courseId,
  assignmentId,
  maxScore,
  initialQuota,
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
    setShowCheckCode(true);

    try {
      const bundle = await createSubmissionBundle(files);
      setPhase("running");
      const { result: runResult, run } = await runSandboxCheck(courseId, assignmentId, bundle);
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
    }
  };

  const score = result?.projected_score ?? 0;
  const totalScore = result?.max_score ?? maxScore;
  const percent = totalScore > 0 ? Math.round((score / totalScore) * 100) : 0;
  const isLoading = phase === "submitting" || phase === "running";
  const isQuotaExhausted = quota !== undefined && quota.remaining === 0;

  return (
    <div className="px-1">
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
                      <p className="font-semibold">Test Case #{index + 1}</p>
                      <p className="text-sm">{test.label}</p>
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
              ? "Waiting for sandbox results..."
              : "Run Check Code to see your projected score and test summaries."}
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
              "Run Check Code to generate session-only projected feedback."}
          </p>
          {result?.retention_notice && (
            <p className="mt-3 text-xs text-slate-500">{result.retention_notice}</p>
          )}
        </div>
      </div>
    </div>
  );
}
