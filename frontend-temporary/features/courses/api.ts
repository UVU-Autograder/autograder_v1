import { apiClient } from "@/lib/api-client";
import { CoursesResponse } from "@/features/courses/types";

export function getCourses() {
    return apiClient.get<CoursesResponse>("/sandbox/courses");
}