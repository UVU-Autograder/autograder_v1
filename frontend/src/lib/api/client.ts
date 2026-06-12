import { API_BASE_URL } from "@/lib/config";
import type {
  ArtifactMetadata,
  SandboxAssignmentDetail,
  SandboxAssignmentSummary,
  SandboxCourse,
  StaffAssignmentSetup,
  StaffAssignmentSummary,
  StaffCourseSummary,
} from "@/types/app";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail ?? message;
    } catch {
      // Keep status text when the backend does not return JSON.
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  listSandboxCourses: () =>
    request<{ courses: SandboxCourse[] }>("/sandbox/courses"),
  listSandboxAssignments: (courseId: string, sandboxSession?: string) =>
    request<{ course_id: string; assignments: SandboxAssignmentSummary[] }>(
      `/sandbox/courses/${courseId}/assignments`,
      sandboxSession
        ? { headers: { "X-Sandbox-Session": sandboxSession } }
        : undefined,
    ),
  getSandboxAssignment: (
    courseId: string,
    assignmentId: string,
    sandboxSession?: string,
  ) =>
    request<SandboxAssignmentDetail>(
      `/sandbox/courses/${courseId}/assignments/${assignmentId}`,
      sandboxSession
        ? { headers: { "X-Sandbox-Session": sandboxSession } }
        : undefined,
    ),
  listStaffCourses: () =>
    request<{ courses: StaffCourseSummary[] }>("/staff/courses"),
  listStaffAssignments: (courseId: string) =>
    request<{ course_id: string; assignments: StaffAssignmentSummary[] }>(
      `/staff/courses/${courseId}/assignments`,
    ),
  getStaffAssignmentSetup: (courseId: string, assignmentId: string) =>
    request<StaffAssignmentSetup>(
      `/staff/courses/${courseId}/assignments/${assignmentId}/setup`,
    ),
  listAssignmentArtifacts: (courseId: string, assignmentId: string) =>
    request<{
      course_id: string;
      assignment_id: string;
      artifacts: ArtifactMetadata[];
    }>(`/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`),
};
