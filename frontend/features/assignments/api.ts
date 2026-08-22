import { apiClient, ApiError, resolveUrl } from "@/lib/api-client";
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

/** Staff assignment lists reuse the sandbox endpoint for a student-parity view. */
export function getAssignments(courseId: string) {
  return apiClient.get<AssignmentsResponse>(`/sandbox/courses/${courseId}/assignments`);
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
  if (stdin && stdin.trim()) {
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

export async function getRunStatus(statusUrl: string) {
  return apiClient.get<RunStatusResponse>(statusUrl);
}

export async function pollRunUntilComplete(
  statusUrl: string,
  options?: {
    intervalMs?: number;
    maxAttempts?: number;
    onStateChange?: (state: string) => void;
    onStatusUpdate?: (status: RunStatusResponse) => void;
  }
) {
  const maxAttempts = options?.maxAttempts ?? 80;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const status = await getRunStatus(statusUrl);
    options?.onStatusUpdate?.(status);
    if (options?.onStateChange) {
      options.onStateChange(status.state);
    }
    if (status.state === "complete" || status.state === "failure") {
      return status;
    }
    const delay = options?.intervalMs ?? getAdaptivePollDelayMs(attempt);
    await sleep(delay);
  }

  throw new Error("Sandbox run timed out before completion.");
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
      if (error instanceof ApiError && error.status === 409) {
        const delay = options?.intervalMs ?? (attempt < 3 ? 150 : 350);
        await sleep(delay);
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
    }
  );
}

export async function streamSandboxAiFeedback(
  runId: string,
  sessionId: string,
  onChunk: (chunk: string) => void,
): Promise<string> {
  const url = resolveUrl(`/sandbox/runs/${runId}/ai-feedback/stream`);
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      [SANDBOX_SESSION_HEADER]: sessionId,
    },
    body: JSON.stringify({}),
  });

  if (!response.ok) {
    throw new Error(`Failed to stream AI feedback (${response.status})`);
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

export function getConceptsMetadata() {
  return apiClient.get<Record<string, ConceptMetadata>>("/sandbox/concepts/metadata");
}

export function createStaffAssignment(courseId: string, payload: AssignmentCreatePayload) {
  return apiClient.post<StaffAssignmentSetup>(`/staff/courses/${courseId}/assignments`, payload);
}

export function deleteStaffAssignment(courseId: string, assignmentId: string) {
  return apiClient.delete<void>(`/staff/courses/${courseId}/assignments/${assignmentId}`);
}
