import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Assignment, RunStatusResponse, SandboxRunResultResponse } from "@/features/assignments/types";

// Vitest runs in mock-API mode by default, so mock the API module directly.
vi.mock("@/features/assignments/api", () => ({
  createSandboxRunWithRetry: vi.fn(),
  pollRunUntilComplete: vi.fn(),
  getAssignment: vi.fn(),
  getRunResult: vi.fn(),
  cancelSandboxRun: vi.fn(),
  requestAiFeedbackWithRetry: vi.fn(),
}));
vi.mock("@/components/markdown-renderer", () => ({
  default: ({ content }: { content: string }) => <div data-testid="markdown">{content}</div>,
}));
vi.mock("@/components/visual-diff-viewer", () => ({ default: () => null }));

import * as api from "@/features/assignments/api";
import { ApiError } from "@/lib/api-client";
import { GRADER_FAULT_MESSAGE, RunStillPendingError } from "@/features/assignments/sandbox-retry";
import CodeResults from "../code-results";
import { AssignmentFileProvider } from "../assignment-file-context";

const mocked = vi.mocked(api);

function quota(remaining: number, resetInMs = 60 * 60_000) {
  return { limit: 20, window_seconds: 3600, remaining, reset_at: new Date(Date.now() + resetInMs).toISOString() };
}

const assignment: Assignment = {
  id: "lab5",
  course_id: "cs1410",
  title: "Lab 5",
  sandbox_enabled: true,
  language: "python",
  max_score: 100,
  upload_quota: quota(20),
  description: "Operator overloading",
  accepted_bundle_types: ["zip"],
  max_upload_bytes: 1024 * 1024,
  constraints: [],
  rubric: [],
  rubric_groups: [],
  config: { bundle: { entrypoint: "money.py", file_requirements: [] }, scoring_items: [] },
} as unknown as Assignment;

function status(overrides: Partial<RunStatusResponse>): RunStatusResponse {
  return { run_id: "run_1", state: "queue", queue_position: 1, eta_band: null, message: null, ...overrides };
}

const completeResult = {
  run_id: "run_1",
  state: "complete",
  projected_score: 75,
  max_score: 100,
  warnings: [],
  test_summaries: [],
  rubric_groups: [],
  sanitized_feedback: "Review your results above.",
} as unknown as SandboxRunResultResponse;

function created(remaining = 19, resetInMs?: number) {
  return {
    run: {
      run_id: "run_1",
      sandbox_session: "sess",
      status_url: "/runs/run_1/status",
      result_url: "/sandbox/runs/run_1/result",
      upload_quota: quota(remaining, resetInMs),
      initial_status: status({}),
      file_preview: { preview_available: false, preview_kind: "metadata_only", sanitized_entries: [] },
    },
    sessionId: "sess",
  };
}

function renderPanel(initialQuota = quota(20)) {
  return render(
    <AssignmentFileProvider assignment={assignment}>
      <CodeResults courseId="cs1410" assignmentId="lab5" maxScore={100} initialQuota={initialQuota} assignment={assignment} />
    </AssignmentFileProvider>,
  );
}

function runButton(): HTMLButtonElement {
  return screen.getByRole("button", { name: /Run Code|Running Tests/ }) as HTMLButtonElement;
}

function aiButton(): HTMLButtonElement {
  return screen.getByRole("button", { name: /AI Feedback/ }) as HTMLButtonElement;
}

beforeEach(() => {
  vi.clearAllMocks();
  mocked.getAssignment.mockResolvedValue({ ...assignment, upload_quota: quota(1) });
  mocked.getRunResult.mockResolvedValue(completeResult);
});

afterEach(() => {
  vi.useRealTimers();
});

describe("CodeResults", () => {
  it("opening and closing the stdin box leaves Run Code usable", () => {
    renderPanel();
    fireEvent.click(screen.getByText(/Provide stdin/));
    fireEvent.change(screen.getByLabelText("Console input / stdin"), { target: { value: "Alice\n3\n" } });
    fireEvent.click(screen.getByText(/Provide stdin/));
    expect(runButton().disabled).toBe(false);
    expect(screen.getByTestId("quota-remaining").textContent).toContain("20 of 20 runs left this hour");
  });

  it("explains a used-up run limit and re-enables Run Code when it resets", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mocked.createSandboxRunWithRetry.mockResolvedValue(created(0, 2_000));
    mocked.pollRunUntilComplete.mockResolvedValue(status({ state: "complete", queue_position: null }));
    renderPanel(quota(1));

    fireEvent.click(runButton());
    await screen.findByTestId("quota-exhausted");
    expect(runButton().disabled).toBe(true);
    expect(screen.getByTestId("quota-exhausted").textContent).toMatch(/used all 20 runs.*unlocks in 0:0\d/);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(6_000);
    });
    await waitFor(() => expect(mocked.getAssignment).toHaveBeenCalledWith("cs1410", "lab5"));
    await waitFor(() => expect(runButton().disabled).toBe(false));
  });

  it("shows the queue-full countdown with Try now and Cancel", async () => {
    mocked.createSandboxRunWithRetry.mockImplementation(async (...args) => {
      const onWait = args[5];
      onWait?.(12_000, 1, new ApiError(503, "full", { code: "queue_full" }));
      return new Promise(() => {});
    });
    renderPanel();
    fireEvent.click(runButton());
    const wait = await screen.findByTestId("admission-wait");
    expect(wait.textContent).toMatch(/not been counted yet\. Retrying in 1\d s/);
    expect(screen.getByRole("button", { name: "Try now" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeTruthy();
  });

  it("shows how many submissions are ahead and the estimated wait", async () => {
    mocked.createSandboxRunWithRetry.mockResolvedValue(created());
    mocked.pollRunUntilComplete.mockImplementation(async (_url, options) => {
      options?.onStatusUpdate?.(status({ queue_position: 4, submissions_ahead: 3, eta_seconds: 42 }));
      return new Promise(() => {});
    });
    renderPanel();
    fireEvent.click(runButton());
    expect((await screen.findByTestId("queue-ahead")).textContent).toBe("About 3 submissions ahead of yours.");
    expect(screen.getByText("Estimated wait: about 42 s")).toBeTruthy();
  });

  it("offers Check again when a run takes unusually long, without resubmitting", async () => {
    mocked.createSandboxRunWithRetry.mockResolvedValue(created());
    mocked.pollRunUntilComplete
      .mockRejectedValueOnce(new RunStillPendingError(status({})))
      .mockResolvedValueOnce(status({ state: "complete", queue_position: null }));
    renderPanel();
    fireEvent.click(runButton());
    await screen.findByTestId("run-pending");
    fireEvent.click(screen.getByRole("button", { name: "Check again" }));
    await waitFor(() => expect(screen.getByText("75 / 100")).toBeTruthy());
    expect(mocked.createSandboxRunWithRetry).toHaveBeenCalledTimes(1);
    expect(mocked.pollRunUntilComplete).toHaveBeenCalledTimes(2);
  });

  it("blames the grader, not the student, for infrastructure failures and skips AI", async () => {
    mocked.createSandboxRunWithRetry.mockResolvedValue(created());
    mocked.pollRunUntilComplete.mockResolvedValue(
      status({ state: "failure", queue_position: null, failure_category: "cleanup_failure", grader_fault: true }),
    );
    mocked.getRunResult.mockRejectedValue(new Error("no stored result"));
    renderPanel();
    fireEvent.click(runButton());
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain(GRADER_FAULT_MESSAGE));
    expect(aiButton().disabled).toBe(true);
    expect(mocked.requestAiFeedbackWithRetry).not.toHaveBeenCalled();
  });

  it("keeps AI feedback unavailable until results are in, then shows the busy countdown", async () => {
    renderPanel();
    expect(aiButton().disabled).toBe(true);

    mocked.createSandboxRunWithRetry.mockResolvedValue(created());
    mocked.pollRunUntilComplete.mockResolvedValue(status({ state: "complete", queue_position: null }));
    mocked.requestAiFeedbackWithRetry.mockImplementation(async (...args) => {
      const onWait = args[4];
      onWait?.(8_000, 1, new ApiError(503, "busy", { code: "ai_busy", ahead: 2 }));
      return new Promise(() => {});
    });
    fireEvent.click(runButton());
    await waitFor(() => expect(aiButton().disabled).toBe(false));
    fireEvent.click(aiButton());
    const wait = await screen.findByTestId("ai-wait");
    expect(wait.textContent).toMatch(/helping other students \(about 2 ahead of you\)\. Retrying in [78] s/);
  });
});
