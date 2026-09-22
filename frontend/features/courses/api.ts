import { apiClient } from "@/lib/api-client";
import { SandboxCoursesResponse, StaffCoursesResponse, CourseAdminDetail } from "@/features/courses/types";

export function getSandboxCourses() {
    return apiClient.get<SandboxCoursesResponse>("/sandbox/courses");
}

export function getStaffCourses() {
    return apiClient.get<StaffCoursesResponse>("/staff/courses");
}

export function getAdminCourses() {
    return apiClient.get<CourseAdminDetail[]>("/staff/admin/courses");
}

export function createAdminCourse(payload: {
    code: string;
    title: string;
    term: string;
    default_concepts?: string[];
    instructor_email?: string | null;
    instructor_name?: string | null;
    ia_email?: string | null;
    ia_name?: string | null;
}) {
    return apiClient.post<CourseAdminDetail>("/staff/admin/courses", payload);
}

export function updateAdminCourse(
    courseId: number,
    payload: {
        code?: string;
        title?: string;
        term?: string;
        default_concepts?: string[];
        is_active?: boolean;
        instructor_id?: number | null;
        ia_id?: number | null;
        instructor_email?: string | null;
        instructor_name?: string | null;
        ia_email?: string | null;
        ia_name?: string | null;
    }
) {
    return apiClient.put<CourseAdminDetail>(`/staff/admin/courses/${courseId}`, payload);
}

export function deleteAdminCourse(courseId: number) {
    return apiClient.delete<void>(`/staff/admin/courses/${courseId}`);
}

export function getAdminUsers() {
    return apiClient.get<{ id: number; email: string; display_name: string | null; is_active: boolean }[]>("/staff/admin/users");
}

export type StaffAccessRecord = {
  id: number;
  user_id: number;
  user_email: string;
  user_name: string | null;
  role_id: number;
  role_name: string;
  course_id: number | null;
  course_code: string | null;
  section_id: number | null;
  section_crn: string | null;
  is_active: boolean;
};

export type StaffAccessPayload = {
  email: string;
  display_name?: string | null;
  role_name: string;
  course_id?: number | null;
  section_id?: number | null;
};

export function getAdminAccessList() {
    return apiClient.get<StaffAccessRecord[]>("/staff/admin/access");
}

export function grantAdminAccess(payload: StaffAccessPayload) {
    return apiClient.post<StaffAccessRecord>("/staff/admin/access", payload);
}

export function revokeAdminAccess(accessId: number) {
    return apiClient.delete<void>(`/staff/admin/access/${accessId}`);
}

export type SectionAdminDetail = {
  id: number;
  course_id: number;
  crn: string;
  is_active: boolean;
};

export function getCourseSections(courseId: number) {
  return apiClient.get<SectionAdminDetail[]>(
    `/staff/admin/courses/${courseId}/sections`,
  );
}

export function createAdminSection(courseId: number, payload: { crn: string }) {
  return apiClient.post<SectionAdminDetail>(
    `/staff/admin/courses/${courseId}/sections`,
    payload,
  );
}

export function updateAdminSection(
  sectionId: number,
  payload: { crn?: string; is_active?: boolean },
) {
  return apiClient.put<SectionAdminDetail>(
    `/staff/admin/sections/${sectionId}`,
    payload,
  );
}

export function deleteAdminSection(sectionId: number) {
  return apiClient.delete<void>(`/staff/admin/sections/${sectionId}`);
}

export type MonitoringStats = {
  active_runs_count: number;
  queued_runs_count: number;
  sandbox_runs_last_hour: number;
  total_token_usage: number;
  cleanup_service_healthy: boolean;
  cleanup_last_checked_at: string | null;
  cleanup_failed_runs: number;
  cleanup_overdue_runs: number;
  cleanup_orphan_errors: number;
};

export function getAdminMonitoring() {
    return apiClient.get<MonitoringStats>("/staff/admin/monitoring");
}