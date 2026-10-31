export interface ActivityTimeseriesPoint {
  timestamp: string;
  run_count: number;
  active_sessions: number;
  success_count: number;
  failure_count: number;
}

export interface AttemptBucket {
  bucket_label: string;
  session_count: number;
  percentage: number;
}

export interface BottleneckItem {
  key: string;
  category: string;
  count: number;
  description?: string | null;
}

export interface AssignmentActivitySummary {
  assignment_id: number;
  assignment_code: string;
  title: string;
  total_runs: number;
  active_students: number;
  pass_rate: number;
  top_bottleneck?: string | null;
}

export interface SystemActivityResponse {
  window_hours: number;
  total_sandbox_runs: number;
  active_student_sessions: number;
  overall_pass_rate: number;
  total_ai_tokens: number;
  total_ai_requests: number;
  velocity: ActivityTimeseriesPoint[];
  attempt_distribution: AttemptBucket[];
  top_bottlenecks: BottleneckItem[];
  assignments: AssignmentActivitySummary[];
}

export interface CourseActivityResponse {
  course_id: number;
  course_code: string;
  course_title: string;
  window_hours: number;
  total_sandbox_runs: number;
  active_student_sessions: number;
  overall_pass_rate: number;
  total_ai_tokens: number;
  total_ai_requests: number;
  velocity: ActivityTimeseriesPoint[];
  attempt_distribution: AttemptBucket[];
  top_bottlenecks: BottleneckItem[];
  assignments: AssignmentActivitySummary[];
}
