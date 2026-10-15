import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api-client";
import {
  aiFailureAction,
  backoffDelayMs,
  isGraderFault,
  isLegacyAiFailureText,
  isRetryableAdmissionError,
  isTransientPollError,
  WaitControl,
} from "../sandbox-retry";
import { createSandboxRunWithRetry, pollRunUntilComplete } from "../api";
import { RetryCancelledError, RunLostError, RunStillPendingError } from "../sandbox-retry";

describe("backoffDelayMs", () => {
  it("grows exponentially, caps at 30 s, and jitters by at most 20%", () => {
    expect(backoffDelayMs(0, undefined, () => 0.5)).toBe(2_000);
    expect(backoffDelayMs(2, undefined, () => 0.5)).toBe(8_000);
    expect(backoffDelayMs(10, undefined, () => 0.5)).toBe(30_000);
    expect(backoffDelayMs(1, undefined, () => 0)).toBe(3_200);
    expect(backoffDelayMs(1, undefined, () => 1)).toBe(4_800);
  });

  it("prefers the server's retry hint", () => {
    expect(backoffDelayMs(0, 15, () => 0.5)).toBe(15_000);
    expect(backoffDelayMs(5, 0.1, () => 0.5)).toBe(1_000);
  });
});

describe("error classification", () => {
  it("auto-retries only admission errors that did not use up a run", () => {
    expect(isRetryableAdmissionError(new ApiError(503, "full", { code: "queue_full" }))).toBe(true);
    expect(isRetryableAdmissionError(new ApiError(503, "busy", { code: "busy" }))).toBe(true);
    expect(isRetryableAdmissionError(new ApiError(503, "Sandbox queue is full."))).toBe(true); // older backend
    expect(isRetryableAdmissionError(new ApiError(503, "x", { code: "grader_unavailable" }))).toBe(false);
    expect(isRetryableAdmissionError(new ApiError(429, "limit", { code: "quota_exhausted" }))).toBe(false);
    expect(isRetryableAdmissionError(new Error("boom"))).toBe(false);
  });

  it("treats network blips, 5xx and not-ready as transient while polling", () => {
    expect(isTransientPollError(new ApiError(0, "net", { code: "network_error" }))).toBe(true);
    expect(isTransientPollError(new ApiError(503, "busy"))).toBe(true);
    expect(isTransientPollError(new ApiError(409, "not ready"))).toBe(true);
    expect(isTransientPollError(new ApiError(404, "gone"))).toBe(false);
    expect(isTransientPollError(new ApiError(400, "bad"))).toBe(false);
  });

  it("retries busy/slow AI, falls back only on connection failure, and stops otherwise", () => {
    expect(aiFailureAction(new ApiError(503, "busy", { code: "ai_busy" }))).toBe("retry");
    expect(aiFailureAction(new ApiError(504, "slow", { code: "ai_timeout" }))).toBe("retry");
    expect(aiFailureAction(new ApiError(0, "net", { code: "network_error" }))).toBe("fallback");
    expect(aiFailureAction(new ApiError(409, "fault", { code: "grader_fault" }))).toBe("stop");
    expect(aiFailureAction(new ApiError(503, "offline", { code: "ai_unavailable" }))).toBe("stop");
    expect(aiFailureAction(new ApiError(502, "old backend"))).toBe("retry");
  });

  it("recognises older backends' outage text and grader faults", () => {
    expect(isLegacyAiFailureText("⚠️ Local AI assistant request timed out. Please try again.")).toBe(true);
    expect(isLegacyAiFailureText("Your Money class works. **Next step:** review __eq__.")).toBe(false);
    expect(isGraderFault("cleanup_failure")).toBe(true);
    expect(isGraderFault("concept_blocked")).toBe(false);
    expect(isGraderFault(null, true)).toBe(true);
  });
});

describe("WaitControl", () => {
  it("can be skipped and cancelled", async () => {
    const control = new WaitControl();
    const pending = control.wait(60_000);
    control.skip();
    await pending;
    control.cancel();
    expect(control.cancelled).toBe(true);
  });
});

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

const queuedStatus = {
  run_id: "run_1", state: "queue", queue_position: 3, eta_band: "1_to_3_min", message: null,
  submissions_ahead: 2, eta_seconds: 30,
};

describe("against a real-shaped API (fetch stubbed)", () => {
  beforeEach(() => {
    sessionStorage.setItem("mock_api", "false");
    vi.useFakeTimers();
  });
  afterEach(() => {
    sessionStorage.clear();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("polls through a 503 blip to completion", async () => {
    const responses = [
      jsonResponse(503, { detail: "Scheduling is unavailable. Retry later." }),
      jsonResponse(200, queuedStatus),
      jsonResponse(200, { ...queuedStatus, state: "complete", queue_position: null, submissions_ahead: null }),
    ];
    vi.stubGlobal("fetch", vi.fn(async () => responses.shift()!));
    const updates: string[] = [];
    const done = pollRunUntilComplete("/runs/run_1/status", { onStatusUpdate: (s) => updates.push(s.state) });
    await vi.advanceTimersByTimeAsync(60_000);
    await expect(done).resolves.toMatchObject({ state: "complete" });
    expect(updates).toEqual(["queue", "complete"]);
  });

  it("stops with RunStillPendingError after the time cap, and RunLostError on 404", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(200, queuedStatus)));
    const slow = pollRunUntilComplete("/runs/run_1/status", { maxDurationMs: 5_000 });
    const assertion = expect(slow).rejects.toBeInstanceOf(RunStillPendingError);
    await vi.advanceTimersByTimeAsync(20_000);
    await assertion;

    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(404, { detail: "Run not found." })));
    await expect(pollRunUntilComplete("/runs/gone/status")).rejects.toBeInstanceOf(RunLostError);
  });

  it("retries a full queue without counting it, then uploads", async () => {
    const created = {
      run_id: "run_9", sandbox_session: "sess", status_url: "/runs/run_9/status",
      result_url: "/sandbox/runs/run_9/result",
      upload_quota: { limit: 20, window_seconds: 3600, remaining: 19, reset_at: "2026-10-15T00:00:00Z" },
      initial_status: queuedStatus, file_preview: {},
    };
    const responses = [
      jsonResponse(503, { detail: { code: "queue_full", message: "full", retry_after_seconds: 2 } }),
      jsonResponse(202, created),
    ];
    vi.stubGlobal("fetch", vi.fn(async () => responses.shift()!));
    const waits: number[] = [];
    const run = createSandboxRunWithRetry("cs1410", "lab5", new Blob(["x"]), undefined, new WaitControl(), (ms) => waits.push(ms));
    await vi.advanceTimersByTimeAsync(10_000);
    await expect(run).resolves.toMatchObject({ run: { run_id: "run_9" } });
    expect(waits).toHaveLength(1);
    expect(waits[0]).toBeGreaterThanOrEqual(1_600);
  });

  it("stops retrying when cancelled", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(503, { detail: { code: "queue_full", message: "full" } })));
    const control = new WaitControl();
    const run = createSandboxRunWithRetry("cs1410", "lab5", new Blob(["x"]), undefined, control, () => control.cancel());
    const assertion = expect(run).rejects.toBeInstanceOf(RetryCancelledError);
    await vi.advanceTimersByTimeAsync(1_000);
    await assertion;
  });
});
