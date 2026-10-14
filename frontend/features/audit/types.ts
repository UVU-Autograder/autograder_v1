export type AuditRecord = {
  id: number;
  timestamp: string;
  event: string;
  workflow_type?: string | null;
  actor_user_id?: number | null;
  course_id?: string | null;
  assignment_id?: string | null;
  run_id?: number | null;
  status_code?: number | null;
  payload: Record<string, unknown>;
};

export type AuditLogListResponse = {
  items: AuditRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type AuditStatsResponse = {
  total_events: number;
  events_24h: number;
  pii_redacted_count: number;
  access_denied_count: number;
  event_counts: Record<string, number>;
};

export type AuditViolationItem = {
  record_id: number;
  timestamp: string;
  event: string;
  field: string;
  matched_rule: string;
};

export type AuditVerificationResponse = {
  compliant: boolean;
  records_scanned: number;
  violations_count: number;
  violations: AuditViolationItem[];
  checked_at: string;
  disclaimer: string;
};

export type AuditLogQueryParams = {
  page?: number;
  page_size?: number;
  event?: string;
  workflow_type?: string;
  actor_user_id?: number;
  course_id?: string;
  run_id?: number;
  search?: string;
  start_time?: string;
  end_time?: string;
};
