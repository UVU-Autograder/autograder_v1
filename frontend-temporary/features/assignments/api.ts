import { apiClient } from "@/lib/api-client";
import { Assignment, AssignmentsResponse } from "@/features/assignments/types";

export function getAssignments(courseId: string) {
  return apiClient.get<AssignmentsResponse>(`/sandbox/courses/${courseId}/assignments`);
}

export function getAssignment(courseId: string, assignmentId: string) {
  return apiClient.get<Assignment>(`/sandbox/courses/${courseId}/assignments/${assignmentId}`);
}