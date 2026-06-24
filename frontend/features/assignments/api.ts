import { apiClient, ApiError } from "@/lib/api-client";
import {
  Assignment,
  AssignmentsResponse,
  RunStatusResponse,
  SandboxRunCreateResponse,
  SandboxRunResultResponse,
  SandboxCancelResponse,
  ConceptMetadata,
} from "@/features/assignments/types";


const SANDBOX_SESSION_HEADER = "X-Sandbox-Session";
const intervalsMsDefault = 2000;

function sandboxSessionKey(courseId: string, assignmentId: string) {
  return `sandbox-session:${courseId}:${assignmentId}`;
}

export function getStoredSandboxSession(
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

function sleep(ms: number) {
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
  bundle: Blob
): Promise<{ run: SandboxRunCreateResponse; sessionId: string }> {
  const formData = new FormData();
  formData.append("bundle", bundle, "submission.zip");

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
  const intervalMs = options?.intervalMs ?? intervalsMsDefault;
  const maxAttempts = options?.maxAttempts ?? 60;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const status = await getRunStatus(statusUrl);
    options?.onStatusUpdate?.(status);
    if (options?.onStateChange) {
      options.onStateChange(status.state);
    }
    if (status.state === "complete" || status.state === "failure") {
      return status;
    }
    await sleep(intervalMs);
  }

  throw new Error("Sandbox run timed out before completion.");
}

export async function getRunResult(
  resultUrl: string,
  sessionId: string,
  options?: { intervalMs?: number; maxAttempts?: number }
) {
  const intervalMs = options?.intervalMs ?? intervalsMsDefault;
  const maxAttempts = options?.maxAttempts ?? 20;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    try {
      return await apiClient.get<SandboxRunResultResponse>(resultUrl, {
        headers: { [SANDBOX_SESSION_HEADER]: sessionId },
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        await sleep(intervalMs);
        continue;
      }
      throw error;
    }
  }

  throw new Error("Sandbox result was not ready in time.");
}

export async function runSandboxCheck(
  courseId: string,
  assignmentId: string,
  bundle: Blob
) {
  const { run, sessionId } = await createSandboxRun(courseId, assignmentId, bundle);
  await pollRunUntilComplete(run.status_url);
  const result = await getRunResult(run.result_url, sessionId);
  return { run, result, sessionId };
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

export function getConceptsMetadata() {
  return apiClient.get<Record<string, ConceptMetadata>>("/sandbox/concepts/metadata");
}

