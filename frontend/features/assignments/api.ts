import {
  AI_TIMEOUT_MS,
  apiClient,
  ApiError,
  type ApiErrorDetail,
  fetchWithTimeout,
  isMockApiEnabled,
  resolveUrl,
} from "@/lib/api-client";
import {
  aiFailureAction,
  backoffDelayMs,
  isLegacyAiFailureText,
  isRetryableAdmissionError,
  isTransientPollError,
  MAX_ADMISSION_WAIT_MS,
  MAX_AI_ATTEMPTS,
  MAX_CONSECUTIVE_POLL_ERRORS,
  MAX_POLL_DURATION_MS,
  RetryCancelledError,
  RunLostError,
  RunStillPendingError,
  WaitControl,
} from "@/features/assignments/sandbox-retry";
import {
  Assignment,
  AssignmentsResponse,
  RunStatusResponse,
  SandboxRunCreateResponse,
  SandboxRunResultResponse,
  SandboxCancelResponse,
  SandboxAiFeedbackResponse,
  ConceptMetadata,
  StaffAssignmentSetup,
  AssignmentCreatePayload,
} from "@/features/assignments/types";


const SANDBOX_SESSION_HEADER = "X-Sandbox-Session";

function sandboxSessionKey(courseId: string, assignmentId: string) {
  return `sandbox-session:${courseId}:${assignmentId}`;
}

function getStoredSandboxSession(
  courseId: string,
  assignmentId: string
): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(sandboxSessionKey(courseId, assignmentId));
}

function storeSandboxSession(
  courseId: string,
  assignmentId: string,
  sessionId: string
) {
  sessionStorage.setItem(sandboxSessionKey(courseId, assignmentId), sessionId);
}

/** Adaptive fast-polling schedule for rapid local grading feedback (150ms -> 250ms -> 400ms -> 750ms). */
export function getAdaptivePollDelayMs(attempt: number): number {
  if (attempt === 0) return 150;
  if (attempt === 1) return 250;
  if (attempt === 2) return 350;
  if (attempt <= 5) return 500;
  if (attempt <= 12) return 750;
  return 1000;
}

export function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const inFlightAssignments = new Map<string, Promise<AssignmentsResponse>>();

/** Staff assignment lists reuse the sandbox endpoint for a student-parity view. */
export function getAssignments(courseId: string) {
  const existing = inFlightAssignments.get(courseId);
  if (existing) {
    return existing;
  }
  const promise = apiClient
    .get<AssignmentsResponse>(`/sandbox/courses/${courseId}/assignments`)
    .finally(() => {
      inFlightAssignments.delete(courseId);
    });
  inFlightAssignments.set(courseId, promise);
  return promise;
}

export function getAssignment(courseId: string, assignmentId: string) {
  return apiClient.get<Assignment>(
    `/sandbox/courses/${courseId}/assignments/${assignmentId}`,
    {
      headers: buildSandboxHeaders(courseId, assignmentId),
    }
  );
}

function buildSandboxHeaders(courseId: string, assignmentId: string) {
  const sessionId = getStoredSandboxSession(courseId, assignmentId);
  return sessionId ? { [SANDBOX_SESSION_HEADER]: sessionId } : undefined;
}

export async function createSandboxRun(
  courseId: string,
  assignmentId: string,
  bundle: Blob,
  stdin?: string,
): Promise<{ run: SandboxRunCreateResponse; sessionId: string }> {
  const formData = new FormData();
  formData.append("bundle", bundle, "submission.zip");
  // Whitespace-only input is still input: a blank line answers an input() call.
  if (stdin) {
    formData.append("stdin", stdin);
  }

  const { data, response } = await apiClient.postForm<SandboxRunCreateResponse>(
    `/sandbox/courses/${courseId}/assignments/${assignmentId}/runs`,
    formData,
    { headers: buildSandboxHeaders(courseId, assignmentId) }
  );

  const sessionId =
    response.headers.get(SANDBOX_SESSION_HEADER) ?? data.sandbox_session;
  storeSandboxSession(courseId, assignmentId, sessionId);

  return { run: data, sessionId };
}

/**
 * Upload a run, retrying automatically while the grading queue is full. Those
 * rejections happen before the run is counted, so the retries cost nothing.
 */
export async function createSandboxRunWithRetry(
  courseId: string,
  assignmentId: string,
  bundle: Blob,
  stdin: string | undefined,
  control: WaitControl,
  onWait?: (waitMs: number, attempt: number, error: ApiError) => void,
): Promise<{ run: SandboxRunCreateResponse; sessionId: string }> {
  const startedAt = Date.now();
  for (let attempt = 0; ; attempt += 1) {
    if (control.cancelled) throw new RetryCancelledError();
    try {
      return await createSandboxRun(courseId, assignmentId, bundle, stdin);
    } catch (err) {
      if (!isRetryableAdmissionError(err) || Date.now() - startedAt > MAX_ADMISSION_WAIT_MS) {
        throw err;
      }
      const waitMs = backoffDelayMs(attempt, err.retryAfterSeconds);
      onWait?.(waitMs, attempt + 1, err);
      await control.wait(waitMs);
    }
  }
}

export async function getRunStatus(statusUrl: string) {
  return apiClient.get<RunStatusResponse>(statusUrl);
}

/**
 * Poll until the run finishes. Transient errors (network blips, 5xx, timeouts) are
 * ridden out with backoff; a long wait ends in RunStillPendingError (the run keeps
 * going and can be checked again) rather than a failure, and a run the backend no
 * longer knows ends in RunLostError.
 */
export async function pollRunUntilComplete(
  statusUrl: string,
  options?: {
    intervalMs?: number;
    maxDurationMs?: number;
    onStateChange?: (state: string) => void;
    onStatusUpdate?: (status: RunStatusResponse) => void;
    control?: WaitControl;
  }
) {
  const maxDurationMs = options?.maxDurationMs ?? MAX_POLL_DURATION_MS;
  const control = options?.control ?? new WaitControl();
  const startedAt = Date.now();
  let lastStatus: RunStatusResponse | null = null;
  let consecutiveErrors = 0;

  for (let attempt = 0; ; attempt += 1) {
    if (control.cancelled) throw new RetryCancelledError();
    try {
      const status = await getRunStatus(statusUrl);
      consecutiveErrors = 0;
      lastStatus = status;
      options?.onStatusUpdate?.(status);
      options?.onStateChange?.(status.state);
      if (status.state === "complete" || status.state === "failure") {
        return status;
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) throw new RunLostError();
      if (!isTransientPollError(err)) throw err;
      consecutiveErrors += 1;
      if (consecutiveErrors > MAX_CONSECUTIVE_POLL_ERRORS) throw err;
      await control.wait(backoffDelayMs(consecutiveErrors - 1, err instanceof ApiError ? err.retryAfterSeconds : undefined));
      continue;
    }
    if (Date.now() - startedAt > maxDurationMs) {
      throw new RunStillPendingError(lastStatus);
    }
    let delay = options?.intervalMs ?? getAdaptivePollDelayMs(attempt);
    // Far back in a busy queue: poll gently, the position changes slowly.
    if (lastStatus?.state === "queue" && (lastStatus.submissions_ahead ?? lastStatus.queue_position ?? 0) > 3) {
      delay = Math.max(delay, 2_000);
    }
    await control.wait(delay);
  }
}

export async function getRunResult(
  resultUrl: string,
  sessionId: string,
  options?: { intervalMs?: number; maxAttempts?: number }
) {
  const maxAttempts = options?.maxAttempts ?? 30;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    try {
      return await apiClient.get<SandboxRunResultResponse>(resultUrl, {
        headers: { [SANDBOX_SESSION_HEADER]: sessionId },
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) throw new RunLostError();
      if (isTransientPollError(error)) {
        const delay = options?.intervalMs ?? (attempt < 3 ? 150 : 350);
        await sleep(error instanceof ApiError && error.status >= 500 ? Math.max(delay, 1_000) : delay);
        continue;
      }
      throw error;
    }
  }

  throw new Error("Sandbox result was not ready in time.");
}

export async function cancelSandboxRun(runId: string, sessionId: string) {
  return apiClient.post<SandboxCancelResponse>(
    `/sandbox/runs/${runId}/cancel`,
    {},
    {
      headers: { [SANDBOX_SESSION_HEADER]: sessionId },
    }
  );
}

export async function getSandboxAiFeedback(runId: string, sessionId: string) {
  return apiClient.post<SandboxAiFeedbackResponse>(
    `/sandbox/runs/${runId}/ai-feedback`,
    {},
    {
      headers: { [SANDBOX_SESSION_HEADER]: sessionId },
      timeoutMs: AI_TIMEOUT_MS,
    }
  );
}

export async function streamSandboxAiFeedback(
  runId: string,
  sessionId: string,
  onChunk: (chunk: string) => void,
): Promise<string> {
  if (isMockApiEnabled()) {
    const feedback = await getSandboxAiFeedback(runId, sessionId);
    const text = feedback.ai_feedback || "All tests passed cleanly.";
    onChunk(text);
    return text;
  }

  const url = resolveUrl(`/sandbox/runs/${runId}/ai-feedback/stream`);
  const response = await fetchWithTimeout(
    url,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        [SANDBOX_SESSION_HEADER]: sessionId,
      },
      body: JSON.stringify({}),
    },
    AI_TIMEOUT_MS,
  );

  if (!response.ok) {
    let detail: ApiErrorDetail | undefined;
    let message = `Failed to stream AI feedback (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (body.detail && typeof body.detail === "object") {
        detail = body.detail as ApiErrorDetail;
        if (typeof detail.message === "string") message = detail.message;
      }
    } catch {
      // Keep the generic message.
    }
    throw new ApiError(response.status, message, detail);
  }

  if (!response.body) {
    throw new Error("ReadableStream not supported on this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullText = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    fullText += chunk;
    onChunk(chunk);
  }

  return fullText;
}

/**
 * AI feedback with automatic retries while the tutor is busy or slow. Falls back
 * to the non-streaming endpoint only when the stream could not connect at all;
 * busy/timeout answers are retried instead, so overload never doubles GPU work.
 */
export async function requestAiFeedbackWithRetry(
  runId: string,
  sessionId: string,
  control: WaitControl,
  onChunk: (chunk: string) => void,
  onWait?: (waitMs: number, attempt: number, error: ApiError) => void,
): Promise<string> {
  let useStream = true;
  for (let attempt = 0; attempt < MAX_AI_ATTEMPTS; attempt += 1) {
    if (control.cancelled) throw new RetryCancelledError();
    let failure: unknown;
    try {
      const text = useStream
        ? await streamSandboxAiFeedback(runId, sessionId, onChunk)
        : (await getSandboxAiFeedback(runId, sessionId)).ai_feedback;
      if (!isLegacyAiFailureText(text)) return text;
      // Older backend: an outage arrived as a 200 with warning text.
      failure = new ApiError(503, text.replace(/^\s*⚠️\s*/, ""), { code: "ai_timeout" });
    } catch (err) {
      failure = err;
    }
    const action = aiFailureAction(failure);
    if (action === "fallback" && useStream) {
      useStream = false;
      continue;
    }
    if (action !== "retry" || attempt === MAX_AI_ATTEMPTS - 1) throw failure;
    const apiError = failure as ApiError;
    const waitMs = backoffDelayMs(attempt + 1, apiError.retryAfterSeconds);
    onWait?.(waitMs, attempt + 1, apiError);
    await control.wait(waitMs);
  }
  throw new Error("AI feedback is unavailable right now.");
}

let conceptsMetadataCache: Promise<Record<string, ConceptMetadata>> | null = null;

export function getConceptsMetadata() {
  if (!conceptsMetadataCache) {
    conceptsMetadataCache = apiClient
      .get<Record<string, ConceptMetadata>>("/sandbox/concepts/metadata")
      .catch((err) => {
        conceptsMetadataCache = null;
        throw err;
      });
  }
  return conceptsMetadataCache;
}

export function createStaffAssignment(courseId: string, payload: AssignmentCreatePayload) {
  return apiClient.post<StaffAssignmentSetup>(`/staff/courses/${courseId}/assignments`, payload);
}

export function deleteStaffAssignment(courseId: string, assignmentId: string) {
  return apiClient.delete<void>(`/staff/courses/${courseId}/assignments/${assignmentId}`);
}
