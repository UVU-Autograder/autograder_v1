export type StudentFile = {
  filepath: string;
  size_bytes: number;
  previewable: boolean;
  preview_kind?: "text" | "image" | "none";
};

export type FilePreview =
  | { kind: "text"; content: string }
  | { kind: "image"; contentType: string; contentBase64: string };

export type RunSummary = {
  id: number;
  status: string;
  total_submission_count: number;
  success_count: number;
  warning_count: number;
  failure_count: number;
  timeout_count: number;
  created_at: string;
};

export type StudentRunDetail = {
  student_name: string;
  canvas_id: string;
  bundle_files: string[];
  bundle_file_count: number;
  score: number;
  max_score: number;
  status: "success" | "failure" | "warning";
  feedback_preview: string;
  feedback_html: string;
  manual_results: Record<
    string,
    { label: string; points: number; score: number | null; comments: string }
  >;
  overall_comment: string;
  automated_results: {
    key: string;
    label: string;
    outcome: string;
    passed: boolean;
    points_awarded: number;
    points: number;
  }[];
  automated_score: number;
  automated_max_score: number;
};

export type ManualProgress = {
  requires_manual_grading: boolean;
  completed_students: number;
  total_students: number;
  exports_ready: boolean;
};

export type RunDetailsResponse = {
  run_id: number;
  status: string;
  students: StudentRunDetail[];
} & ManualProgress;

export type ManualGradeSaveResponse = StudentRunDetail & {
  manual_progress: ManualProgress;
};

export type ScoreBucket = {
  key: string;
  shortLabel: string;
  rangeLabel: string;
  count: number;
};

export type StatusFilter = "all" | "ungraded" | "graded" | "failed";
