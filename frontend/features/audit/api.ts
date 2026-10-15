import { apiClient } from "@/lib/api-client";
import {
  AuditLogListResponse,
  AuditLogQueryParams,
  AuditStatsResponse,
  AuditVerificationResponse,
} from "./types";

export function getAdminLogs(params: AuditLogQueryParams = {}) {
  const query = new URLSearchParams();
  if (params.page) query.set("page", params.page.toString());
  if (params.page_size) query.set("page_size", params.page_size.toString());
  if (params.event) query.set("event", params.event);
  if (params.workflow_type) query.set("workflow_type", params.workflow_type);
  if (params.actor_user_id !== undefined && params.actor_user_id !== null) {
    query.set("actor_user_id", params.actor_user_id.toString());
  }
  if (params.course_id) query.set("course_id", params.course_id);
  if (params.run_id !== undefined && params.run_id !== null) {
    query.set("run_id", params.run_id.toString());
  }
  if (params.search) query.set("search", params.search);
  if (params.start_time) query.set("start_time", params.start_time);
  if (params.end_time) query.set("end_time", params.end_time);

  const qs = query.toString();
  return apiClient.get<AuditLogListResponse>(`/staff/admin/logs${qs ? `?${qs}` : ""}`);
}

export function getAdminLogStats() {
  return apiClient.get<AuditStatsResponse>("/staff/admin/logs/stats");
}

export function verifyAdminLogs(limit: number = 500) {
  return apiClient.post<AuditVerificationResponse>(`/staff/admin/logs/verify?limit=${limit}`, {});
}
