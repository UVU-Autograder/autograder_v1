import { apiClient } from "@/lib/api-client";
import type { CourseActivityResponse, SystemActivityResponse } from "./types";

export function getAdminActivity(windowHours: number = 168): Promise<SystemActivityResponse> {
  return apiClient.get<SystemActivityResponse>(`/staff/admin/activity?window_hours=${windowHours}`);
}

export function getCourseActivity(courseId: string, windowHours: number = 168): Promise<CourseActivityResponse> {
  return apiClient.get<CourseActivityResponse>(`/staff/courses/${courseId}/activity?window_hours=${windowHours}`);
}
