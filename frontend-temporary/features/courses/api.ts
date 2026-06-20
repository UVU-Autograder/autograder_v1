import { apiClient } from "@/lib/api-client";
import { SandboxCoursesResponse, StaffCoursesResponse } from "@/features/courses/types";

export function getSandboxCourses() {
    return apiClient.get<SandboxCoursesResponse>("/sandbox/courses");
}

export function getStaffCourses() {
    return apiClient.get<StaffCoursesResponse>("/staff/courses");
}